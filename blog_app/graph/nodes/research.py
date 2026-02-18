import os
import sys
from dotenv import load_dotenv

from blog_app.config.config_loader import read_yaml
from blog_app.config.paths_config import CONFIG_PATH

from blog_app.core.state import State
from blog_app.core.schemas import EvidenceItem
from blog_app.logger.custom_logger import CustomLogger
from blog_app.exception.custom_exception import CustomException

from datetime import date, timedelta
from typing import List, Optional

logger = CustomLogger().get_logger(__name__)
load_dotenv()


class ResearchNode:
    """
    Handles external research via Tavily.

    EvidenceItems are built directly from Tavily's structured response —
    no LLM extraction step needed. Tavily already returns title, url,
    snippet, and published_at. Using an LLM to re-parse this was the
    source of repeated failures (Gemini drops fields under function calling).
    """

    @staticmethod
    def _iso_to_date(s: Optional[str]) -> Optional[date]:
        if not s:
            return None
        try:
            return date.fromisoformat(s[:10])
        except Exception:
            return None

    @staticmethod
    def _tavily_search(query: str, max_results: int = 5) -> List[dict]:
        if not os.getenv("TAVILY_API_KEY"):
            logger.warning("TAVILY_API_KEY not set; skipping research")
            return []
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults

            tool = TavilySearchResults(max_results=max_results)
            results = tool.invoke({"query": query})

            out: List[dict] = []
            for r in results or []:
                url = r.get("url") or ""
                if not url:
                    continue   # skip results with no URL
                out.append({
                    "title":        r.get("title") or "",
                    "url":          url,
                    "snippet":      r.get("content") or r.get("snippet") or "",
                    "published_at": r.get("published_date") or r.get("published_at"),
                    "source":       r.get("source"),
                })
            return out
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            return []

    @staticmethod
    def research_node(state: State) -> dict:
        try:
            config = read_yaml(CONFIG_PATH)["research"]

            queries = (state.get("queries") or [])[:config["max_queries"]]
            logger.info(f"🔍 Starting web research with {len(queries)} queries...")

            raw: List[dict] = []
            for q in queries:
                raw.extend(
                    ResearchNode._tavily_search(
                        q, max_results=config["tavily"]["max_results"]
                    )
                )

            if not raw:
                logger.info("⚠️ No research results found")
                return {"evidence": []}

            logger.info(f"📋 Found {len(raw)} raw search results")

            # Build EvidenceItems directly — no LLM needed, Tavily data is already structured
            dedup: dict = {}
            for r in raw:
                url = r.get("url") or ""
                if url and url not in dedup:
                    dedup[url] = EvidenceItem(
                        title=r.get("title") or "",
                        url=url,
                        snippet=r.get("snippet") or "",
                        published_at=r.get("published_at"),
                        source=r.get("source"),
                    )

            evidence = list(dedup.values())

            # For open_book: filter to items within the recency window
            if state.get("mode") == "open_book":
                as_of   = date.fromisoformat(state["as_of"])
                cutoff  = as_of - timedelta(days=int(state["recency_days"]))
                before  = len(evidence)
                evidence = [
                    e for e in evidence
                    if (d := ResearchNode._iso_to_date(e.published_at)) and d >= cutoff
                ]
                logger.info(f"📅 Filtered to {len(evidence)} recent items (from {before})")

            logger.info(f"✅ Research complete: {len(evidence)} evidence items ready")
            return {
                "evidence": evidence,
                "run_id":   state.get("run_id"),
            }

        except Exception as e:
            logger.exception(f"Research node failed: {e}")
            raise CustomException("Research node execution failed", sys)

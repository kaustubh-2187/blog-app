import os
import sys
from dotenv import load_dotenv

from blog_app.config.config_loader import read_yaml
from blog_app.config.paths_config import CONFIG_PATH

from blog_app.core.state import State
from blog_app.prompts.prompts import BlogPrompts
from blog_app.core.schemas import EvidencePack
from blog_app.llm.client import llm

from blog_app.logger.custom_logger import CustomLogger
from blog_app.exception.custom_exception import CustomException

from datetime import date, timedelta
from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage

logger = CustomLogger().get_logger(__name__)
load_dotenv()

class ResearchNode:
    """
    Handles external research and evidence synthesis.
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
                out.append(
                    {
                        "title": r.get("title") or "",
                        "url": r.get("url") or "",
                        "snippet": r.get("content") or r.get("snippet") or "",
                        "published_at": r.get("published_date") or r.get("published_at"),
                        "source": r.get("source"),
                    }
                )
            return out
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            return []

    @staticmethod
    def research_node(state: State) -> dict:
        try:

            config = read_yaml(CONFIG_PATH)["research"]
            RESEARCH_SYSTEM = BlogPrompts.RESEARCH_SYSTEM

            queries = (state.get("queries") or [])[:config["max_queries"]]
            raw: List[dict] = []
            for q in queries:
                raw.extend(ResearchNode._tavily_search(q, max_results=config['tavily']['max_results']))

            if not raw:
                return {"evidence": []}

            extractor = llm.with_structured_output(EvidencePack)

            
            pack = extractor.invoke(
                [
                    SystemMessage(content=RESEARCH_SYSTEM),
                    HumanMessage(
                        content=(
                            f"As-of date: {state['as_of']}\n"
                            f"Recency days: {state['recency_days']}\n\n"
                            f"Raw results:\n{raw}"
                        )
                    ),
                ]
            )

            dedup = {}
            for e in pack.evidence:
                if e.url:
                    dedup[e.url] = e
            evidence = list(dedup.values())

            if state.get("mode") == "open_book":
                as_of = date.fromisoformat(state["as_of"])
                cutoff = as_of - timedelta(days=int(state["recency_days"]))
                evidence = [e for e in evidence if (d := ResearchNode._iso_to_date(e.published_at)) and d >= cutoff]

            return {
                "evidence": evidence,
                "run_id": state.get("run_id")
            }
        except Exception as e:
            logger.exception(f"Research node failed: {e}")
            raise CustomException("Research node execution failed", sys)


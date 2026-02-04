import os
import sys
from dotenv import load_dotenv

from blog_app.config.config_loader import read_yaml


from blog_app.core.state import State
from blog_app.prompts.prompts import BlogPrompts
from blog_app.core.schemas import Plan
from blog_app.llm.client import llm
from blog_app.logger.custom_logger import CustomLogger
from blog_app.exception.custom_exception import CustomException

from langchain_core.messages import SystemMessage, HumanMessage

logger = CustomLogger().get_logger(__name__)
load_dotenv()

class OrechestratorNode:
    """
    Responsible for producing the high-level blog plan.
    Converts topic + evidence into a structured Plan.
    """

    @staticmethod
    def orchestrator_node(state: State) -> dict:
        try:

            ORCH_SYSTEM = BlogPrompts.ORCH_SYSTEM

            planner = llm.with_structured_output(Plan)
            mode = state.get("mode", "closed_book")
            evidence = state.get("evidence", [])

            forced_kind = "news_roundup" if mode == "open_book" else None

            plan = planner.invoke(
                [
                    SystemMessage(content=ORCH_SYSTEM),
                    HumanMessage(
                        content=(
                            f"Topic: {state['topic']}\n"
                            f"Mode: {mode}\n"
                            f"As-of: {state['as_of']} (recency_days={state['recency_days']})\n"
                            f"{'Force blog_kind=news_roundup' if forced_kind else ''}\n\n"
                            f"Evidence:\n{[e.model_dump() for e in evidence][:16]}"
                        )
                    ),
                ]
            )
            if forced_kind:
                plan.blog_kind = "news_roundup"

            logger.info("Orchestrator node completed successfully")
            return {"plan": plan}
        except Exception as e:
            logger.error(f"Orchestrator node failed: {e}")
            raise CustomException("Orchestrator node execution failed", sys)
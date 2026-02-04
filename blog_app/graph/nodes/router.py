import sys
from dotenv import load_dotenv

from blog_app.config.config_loader import read_yaml
from blog_app.config.paths_config import CONFIG_PATH

from blog_app.core.state import State
from blog_app.prompts.prompts import BlogPrompts
from blog_app.core.schemas import RouterDecision
from blog_app.llm.client import llm

from langchain_core.messages import SystemMessage, HumanMessage

from blog_app.logger.custom_logger import CustomLogger
from blog_app.exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)
load_dotenv()

class RouterNode:
    """
    Decides routing strategy:
    - whether research is needed
    - which mode to run in
    - recency window
    """

    @staticmethod
    def router_node(state: State) -> dict:
        try:
            config = read_yaml(CONFIG_PATH)["router"]

            logger.info("Starting router node")
        
            ROUTER_SYSTEM = BlogPrompts.ROUTER_SYSTEM

            decider = llm.with_structured_output(RouterDecision)
            decision = decider.invoke(
                [
                    SystemMessage(content=ROUTER_SYSTEM),
                    HumanMessage(content=f"Topic: {state['topic']}\nAs-of date: {state['as_of']}"),
                ]
            )

            # if decision.mode == "open_book":
            #     recency_days = config['recency_days']['open_book']
            # elif decision.mode == "hybrid":
            #     recency_days = config['recency_days']['hybrid']
            # else:
            #     recency_days = config['recency_days']['closed_book']
            recency_days = config["recency_days"].get(decision.mode)

            logger.info(
                f"Routing decision: mode={decision.mode}, "
                f"needs_research={decision.needs_research}"
            )

            return {
                "needs_research": decision.needs_research,
                "mode": decision.mode,
                "queries": decision.queries,
                "recency_days": recency_days,
                "run_id": state.get("run_id")
            }
        except Exception as e:
            logger.exception(f"Router node failed: {e}")
            raise CustomException("Router node execution failed", sys)

class RouteResolver:
    """
    Pure routing logic for LangGraph conditional edges.
    """

    @staticmethod
    def route_next(state: State) -> str:
        return "research" if state["needs_research"] else "orchestrator"
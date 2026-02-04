import sys
from dotenv import load_dotenv

from blog_app.config.config_loader import read_yaml
from blog_app.config.paths_config import CONFIG_PATH

from blog_app.core.state import State
from blog_app.graph.fanout import fanout
from blog_app.graph.nodes.reducer import ReducerNode
from blog_app.graph.nodes.router import RouterNode, RouteResolver
from blog_app.graph.nodes.research import ResearchNode
from blog_app.graph.nodes.orchestrator import OrechestratorNode
from blog_app.graph.nodes.worker import WorkerNode

from blog_app.logger.custom_logger import CustomLogger
from blog_app.exception.custom_exception import CustomException

from langgraph.graph import StateGraph, START, END

logger = CustomLogger().get_logger(__name__)
load_dotenv()

class GraphBuilder:
    """
    Responsible ONLY for constructing and compiling the LangGraph graph.
    No execution, no logging, no exception handling.
    """ 
    def __init__(self):
        self.config = read_yaml(CONFIG_PATH)
        self.recursion_limit = self.config['graph']['recursion_limit']
        self.max_concurrency = self.config['graph']['max_concurrency']
    
    def _build_reducer_graph(self):

        try:
            # build reducer subgraph
            logger.info("Building the reducer subgraph")
            reducer_graph = StateGraph(State)
            reducer_graph.add_node("merge_content", ReducerNode.merge_content)
            reducer_graph.add_node("decide_images", ReducerNode.decide_images)
            reducer_graph.add_node("generate_and_place_images", ReducerNode.generate_and_place_images)
            reducer_graph.add_edge(START, "merge_content")
            reducer_graph.add_edge("merge_content", "decide_images")
            reducer_graph.add_edge("decide_images", "generate_and_place_images")
            reducer_graph.add_edge("generate_and_place_images", END)
            compiled_reducer_graph = reducer_graph.compile()

            logger.info('Reduver Graph Sucessfully built and compiled')
            return compiled_reducer_graph
        
        except Exception as e:
            logger.error(f"Error during building the reducer graph : {e}")
            raise CustomException("Failed during building the reducer graph", sys)

    def build(self):
        reducer_subgraph = self._build_reducer_graph()
        try:
            # -----------------------------
            #  Build main graph
            # -----------------------------
            logger.info("Building the main graph")
            g = StateGraph(State)
            g.add_node("router", RouterNode.router_node)
            g.add_node("research", ResearchNode.research_node)
            g.add_node("orchestrator", OrechestratorNode.orchestrator_node)
            g.add_node("worker", WorkerNode.worker_node)
            g.add_node("reducer", reducer_subgraph)

            g.add_edge(START, "router")
            g.add_conditional_edges("router", RouteResolver.route_next, {"research": "research", "orchestrator": "orchestrator"})
            g.add_edge("research", "orchestrator")

            g.add_conditional_edges("orchestrator", fanout, ["worker"])
            g.add_edge("worker", "reducer")
            g.add_edge("reducer", END)

            # app = g.compile()
            app = g.compile().with_config(
                recursion_limit=self.recursion_limit, 
                max_concurrency=self.max_concurrency
            )
            logger.info("Main Graph Sucessfully Built and Compiled")

            return app
        except Exception as e:
            logger.error(f"Error during building the main graph : {e}")
            raise CustomException("Failed during building the main graph", sys)
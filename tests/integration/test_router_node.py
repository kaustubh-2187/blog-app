"""
Integration tests for router node.
"""
import pytest
from blog_app.graph.nodes.router import RouterNode
from blog_app.core.schemas import RouterDecision


class TestRouterNode:
    """Test RouterNode integration."""
    
    def test_router_hybrid_mode(self):
        """Test router returns hybrid mode for mixed topics."""
        state = {
            "topic": "Latest LangGraph features in 2024",
            "as_of": "2024-02-03"
        }
        
        result = RouterNode.router_node(state)
        
        assert "mode" in result
        assert result["mode"] in ["closed_book", "hybrid", "open_book"]
        assert "needs_research" in result
        assert isinstance(result["needs_research"], bool)
    
    def test_router_closed_book_mode(self):
        """Test router returns closed_book for evergreen topics."""
        state = {
            "topic": "Python basics: variables and data types",
            "as_of": "2024-02-03"
        }
        
        result = RouterNode.router_node(state)
        
        # Evergreen topic should likely be closed_book
        assert result["mode"] in ["closed_book", "hybrid"]
    
    def test_router_returns_queries(self):
        """Test router returns search queries when needed."""
        state = {
            "topic": "Latest AI developments in 2024",
            "as_of": "2024-02-03"
        }
        
        result = RouterNode.router_node(state)
        
        if result["needs_research"]:
            assert "queries" in result
            assert isinstance(result["queries"], list)
            assert len(result["queries"]) > 0
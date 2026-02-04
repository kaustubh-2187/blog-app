"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import date
from unittest.mock import Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blog_app.core.state import State
from blog_app.core.schemas import Task, Plan, EvidenceItem, RouterDecision


# ============================================================
# Environment Setup
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "test-key")
    os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "test-key")
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "test-key")


# ============================================================
# Temporary Directory Fixtures
# ============================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_data_dir(temp_dir):
    """Create temporary data directory structure."""
    data_dir = temp_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def temp_images_dir(temp_dir):
    """Create temporary images directory."""
    images_dir = temp_dir / "images"
    images_dir.mkdir(exist_ok=True)
    return images_dir


# ============================================================
# Sample Data Fixtures
# ============================================================

@pytest.fixture
def sample_task():
    """Sample Task object."""
    return Task(
        id=1,
        title="Introduction to LangGraph",
        goal="Understand the basics of LangGraph",
        bullets=[
            "LangGraph is a framework for building agentic workflows",
            "It provides state management for AI agents",
            "LangGraph enables multi-agent coordination"
        ],
        target_words=250,
        tags=["LangGraph", "AI", "workflows"],
        requires_research=True,
        requires_citations=True,
        requires_code=False
    )


@pytest.fixture
def sample_plan(sample_task):
    """Sample Plan object."""
    return Plan(
        blog_title="How LangGraph Enables Agentic Workflows",
        audience="technical developers",
        tone="technical",
        blog_kind="explainer",
        constraints=["Keep it under 2000 words"],
        tasks=[sample_task]
    )


@pytest.fixture
def sample_evidence():
    """Sample Evidence items."""
    return [
        EvidenceItem(
            title="LangGraph Documentation",
            url="https://langchain.com/langgraph",
            published_at="2024-01-15",
            snippet="LangGraph is a framework for building stateful applications",
            source="LangChain"
        ),
        EvidenceItem(
            title="Building Agentic Workflows",
            url="https://example.com/workflows",
            published_at="2024-02-01",
            snippet="Agentic workflows enable autonomous task execution",
            source="Tech Blog"
        )
    ]


@pytest.fixture
def sample_state(sample_plan, sample_evidence):
    """Sample State object."""
    return {
        "topic": "How LangGraph enables agentic workflows",
        "run_id": "test1234",
        "mode": "hybrid",
        "needs_research": True,
        "queries": ["LangGraph tutorial", "agentic workflows"],
        "evidence": sample_evidence,
        "plan": sample_plan,
        "as_of": "2024-02-03",
        "recency_days": 45,
        "sections": [],
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],
        "final": ""
    }


@pytest.fixture
def sample_router_decision():
    """Sample RouterDecision."""
    return RouterDecision(
        needs_research=True,
        mode="hybrid",
        reason="Topic requires current examples",
        queries=["LangGraph tutorial", "agentic AI workflows"],
        max_results_per_query=5
    )


# ============================================================
# Mock LLM Fixtures
# ============================================================

@pytest.fixture
def mock_llm():
    """Mock LLM client."""
    mock = MagicMock()
    mock.invoke = MagicMock()
    mock.with_structured_output = MagicMock(return_value=mock)
    return mock


@pytest.fixture
def mock_groq_client(mock_llm):
    """Mock Groq client."""
    return mock_llm


# ============================================================
# Mock Service Fixtures
# ============================================================

@pytest.fixture
def mock_tavily_search():
    """Mock Tavily search results."""
    def _search(query: str, max_results: int = 5):
        return [
            {
                "title": f"Result for {query}",
                "url": f"https://example.com/{query.replace(' ', '-')}",
                "content": f"This is content about {query}",
                "published_date": "2024-02-01",
                "source": "Example"
            }
        ]
    return _search


@pytest.fixture
def mock_gemini_image():
    """Mock Gemini image generation."""
    def _generate_image(prompt: str):
        return b"fake_image_bytes_data"
    return _generate_image
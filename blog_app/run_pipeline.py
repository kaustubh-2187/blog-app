import uuid
from datetime import date
from typing import Dict, Any

from blog_app.graph.builder import GraphBuilder


def run_blog_pipeline(
    topic: str,
    as_of: str | None = None,
) -> Dict[str, Any]:
    """
    Runs the blog generation pipeline end-to-end.

    This function is intentionally framework-agnostic.
    It can be reused by FastAPI, CLI, tests, etc.
    """

    if not topic or not topic.strip():
        raise ValueError("Topic must be a non-empty string.")

    run_id = uuid.uuid4().hex[:8]
    # -----------------------------
    # Build graph (once per process)
    # -----------------------------
    graph_builder = GraphBuilder()
    app = graph_builder.build()

    inputs: Dict[str, Any] = {
        "topic": topic.strip(),
        "run_id" : run_id,
        # routing / research
        "mode": "",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "plan": None,

        # recency
        "as_of": as_of or date.today().isoformat(),
        "recency_days": 7,

        # workers
        "sections": [],

        # reducer / images
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],

        # final output
        "final": "",
    }

    # Run graph (non-streaming execution)
    output = app.invoke(inputs)

    return output


if __name__ == "__main__":
    result = run_blog_pipeline(
        topic="How LangGraph enables agentic workflows",
    )

    print("\n===== BLOG GENERATED =====\n")
    print(result.get("final", "No output generated"))

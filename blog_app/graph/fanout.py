from langgraph.types import Send
from blog_app.core.state import State
from dotenv import load_dotenv

load_dotenv()

def fanout(state: State):
    assert state["plan"] is not None
    total_tasks = len(state["plan"].tasks)
    return [
        Send(
            "worker",
            {
                "task": task.model_dump(),
                "topic": state["topic"],
                "mode": state["mode"],
                "as_of": state["as_of"],
                "recency_days": state["recency_days"],
                "plan": state["plan"].model_dump(),
                "evidence": [e.model_dump() for e in state.get("evidence", [])],
                "total_tasks": total_tasks,
            },
        )
        for task in state["plan"].tasks
    ]
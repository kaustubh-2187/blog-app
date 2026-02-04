import sys
from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage
from blog_app.prompts.prompts import BlogPrompts
from blog_app.core.schemas import EvidenceItem, Task, Plan
from blog_app.llm.client import llm

from blog_app.logger.custom_logger import CustomLogger
from blog_app.exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)
load_dotenv()

class WorkerNode:
    """
    Responsible for generating ONE blog section per task.
    Stateless and safe for parallel execution.
    """
    @staticmethod
    def worker_node(payload: dict) -> dict:
        try:
            logger.info("Worker node started")

            WORKER_SYSTEM = BlogPrompts.WORKER_SYSTEM

            task = Task(**payload["task"])
            plan = Plan(**payload["plan"])
            evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]

            bullets_text = "\n- " + "\n- ".join(task.bullets)
            evidence_text = "\n".join(
                f"- {e.title} | {e.url} | {e.published_at or 'date:unknown'}"
                for e in evidence[:20]
            )

            logger.info(
                f"Generating section: task_id={task.id}, title='{task.title}'"
            )

            section_md = llm.invoke(
                [
                    SystemMessage(content=WORKER_SYSTEM),
                    HumanMessage(
                        content=(
                            f"Blog title: {plan.blog_title}\n"
                            f"Audience: {plan.audience}\n"
                            f"Tone: {plan.tone}\n"
                            f"Blog kind: {plan.blog_kind}\n"
                            f"Constraints: {plan.constraints}\n"
                            f"Topic: {payload['topic']}\n"
                            f"Mode: {payload.get('mode')}\n"
                            f"As-of: {payload.get('as_of')} (recency_days={payload.get('recency_days')})\n\n"
                            f"Section title: {task.title}\n"
                            f"Goal: {task.goal}\n"
                            f"Target words: {task.target_words}\n"
                            f"Tags: {task.tags}\n"
                            f"requires_research: {task.requires_research}\n"
                            f"requires_citations: {task.requires_citations}\n"
                            f"requires_code: {task.requires_code}\n"
                            f"Bullets:{bullets_text}\n\n"
                            f"Evidence (ONLY cite these URLs):\n{evidence_text}\n"
                        )
                    ),
                ]
            ).content.strip()

            logger.info(f"Worker node completed task_id={task.id}")
            return {"sections": [(task.id, section_md)]}
        except Exception as e:
            logger.error(f"Worker node failed: {e}")
            raise CustomException("Worker node execution failed", sys)
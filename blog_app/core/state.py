from pydantic import BaseModel, Field
from typing import List, Annotated, Optional, Literal, TypedDict
from blog_app.core.schemas import EvidenceItem, Plan
import operator

class State(TypedDict):
    topic: str
    run_id: str  # Added to track the unique run identifier

    # routing / research
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]

    # recency
    as_of: str
    recency_days: int

    # workers
    sections: Annotated[List[tuple[int, str]], operator.add]  # (task_id, section_md)

    # reducer/image
    images_enabled: bool  # Whether to generate images
    merged_md: str
    md_with_placeholders: str
    image_specs: List[dict]

    final: str
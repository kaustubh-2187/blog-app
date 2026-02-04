from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date


class BlogGenerationRequest(BaseModel):
    """Request model for blog generation."""
    
    topic: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Blog topic or title",
        examples=["How LangGraph enables agentic workflows"]
    )
    
    as_of: Optional[str] = Field(
        default=None,
        description="Reference date (ISO format YYYY-MM-DD)",
        examples=["2024-02-03"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "How LangGraph enables agentic workflows",
                "as_of": "2024-02-03"
            }
        }


class BlogStatusRequest(BaseModel):
    """Request model for checking blog status."""
    
    run_id: str = Field(
        ...,
        min_length=8,
        max_length=8,
        description="Run ID (UUID)",
        examples=["a1b2c3d4"]
    )
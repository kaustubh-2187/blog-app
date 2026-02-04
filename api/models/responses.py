from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TaskInfo(BaseModel):
    """Task information."""
    id: int
    title: str
    target_words: int
    requires_research: bool
    requires_citations: bool
    requires_code: bool


class PlanInfo(BaseModel):
    """Plan information."""
    blog_title: str
    audience: str
    tone: str
    blog_kind: str
    tasks: List[TaskInfo]


class BlogGenerationResponse(BaseModel):
    """Response model for blog generation."""
    
    run_id: str = Field(..., description="Unique run identifier")
    status: str = Field(..., description="Generation status")
    message: str = Field(..., description="Status message")
    
    # Optional fields populated on success
    topic: Optional[str] = None
    mode: Optional[str] = None
    plan: Optional[PlanInfo] = None
    
    # File paths
    markdown_path: Optional[str] = None
    images_count: Optional[int] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "a1b2c3d4",
                "status": "completed",
                "message": "Blog generated successfully",
                "topic": "How LangGraph enables agentic workflows",
                "mode": "hybrid",
                "markdown_path": "data/how-langgraph-enables-agentic-workflows_a1b2c3d4/markdown/how-langgraph-enables-agentic-workflows.md",
                "images_count": 3,
                "created_at": "2024-02-03T12:00:00"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    run_id: Optional[str] = None


class FileListResponse(BaseModel):
    """File listing response."""
    run_id: str
    files: List[Dict[str, Any]]
    total_files: int
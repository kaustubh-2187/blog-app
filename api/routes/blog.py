import asyncio
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from api.models.requests import BlogGenerationRequest, BlogStatusRequest
from api.models.responses import (
    BlogGenerationResponse,
    ErrorResponse,
    PlanInfo,
    TaskInfo
)
from run_pipeline import run_blog_pipeline
from blog_app.config.paths_config import get_run_output_dir, get_markdown_dir

router = APIRouter()

# In-memory storage for job status (replace with Redis/DB in production)
job_status = {}


async def generate_blog_async(request: BlogGenerationRequest, run_id: str):
    """
    Background task to generate blog.
    """
    try:
        job_status[run_id] = {
            "status": "processing",
            "message": "Generating blog...",
            "created_at": datetime.now()
        }
        
        # Run pipeline
        result = await asyncio.to_thread(
            run_blog_pipeline,
            topic=request.topic,
            as_of=request.as_of or date.today().isoformat()
        )
        
        # Extract plan info
        plan = result.get("plan")
        plan_info = None
        if plan:
            plan_info = PlanInfo(
                blog_title=plan.blog_title,
                audience=plan.audience,
                tone=plan.tone,
                blog_kind=plan.blog_kind,
                tasks=[
                    TaskInfo(
                        id=t.id,
                        title=t.title,
                        target_words=t.target_words,
                        requires_research=t.requires_research,
                        requires_citations=t.requires_citations,
                        requires_code=t.requires_code
                    )
                    for t in plan.tasks
                ]
            )
        
        # Get file paths
        title_slug = plan.blog_title.lower().replace(" ", "-") if plan else "blog"
        run_dir = get_run_output_dir(title_slug, run_id)
        markdown_dir = get_markdown_dir(run_dir)
        
        # Count images
        images_dir = run_dir / "images"
        images_count = len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0
        
        # Find markdown file
        md_files = list(markdown_dir.glob("*.md"))
        markdown_path = str(md_files[0]) if md_files else None
        
        job_status[run_id] = {
            "status": "completed",
            "message": "Blog generated successfully",
            "topic": request.topic,
            "mode": result.get("mode"),
            "plan": plan_info,
            "markdown_path": markdown_path,
            "images_count": images_count,
            "created_at": job_status[run_id]["created_at"],
            "completed_at": datetime.now()
        }
        
    except Exception as e:
        job_status[run_id] = {
            "status": "failed",
            "message": f"Generation failed: {str(e)}",
            "error": str(e),
            "created_at": job_status[run_id]["created_at"],
            "completed_at": datetime.now()
        }


@router.post("/blog/generate", response_model=BlogGenerationResponse)
async def generate_blog(
    request: BlogGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a blog post.
    
    This endpoint starts the blog generation process asynchronously.
    Use the returned run_id to check status with /blog/status/{run_id}.
    """
    import uuid
    
    run_id = uuid.uuid4().hex[:8]
    
    # Start background task
    background_tasks.add_task(generate_blog_async, request, run_id)
    
    return BlogGenerationResponse(
        run_id=run_id,
        status="processing",
        message="Blog generation started",
        topic=request.topic
    )


@router.get("/blog/status/{run_id}", response_model=BlogGenerationResponse)
async def get_blog_status(run_id: str):
    """
    Get blog generation status.
    
    Returns the current status of a blog generation job.
    """
    if run_id not in job_status:
        raise HTTPException(
            status_code=404,
            detail=f"Run ID {run_id} not found"
        )
    
    status = job_status[run_id]
    
    return BlogGenerationResponse(
        run_id=run_id,
        **status
    )


@router.get("/blog/download/{run_id}/markdown")
async def download_markdown(run_id: str):
    """
    Download the generated markdown file.
    """
    if run_id not in job_status:
        raise HTTPException(status_code=404, detail="Run ID not found")
    
    status = job_status[run_id]
    
    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Blog is still {status['status']}"
        )
    
    markdown_path = status.get("markdown_path")
    if not markdown_path or not Path(markdown_path).exists():
        raise HTTPException(status_code=404, detail="Markdown file not found")
    
    return FileResponse(
        path=markdown_path,
        media_type="text/markdown",
        filename=Path(markdown_path).name
    )


@router.delete("/blog/{run_id}")
async def delete_blog(run_id: str):
    """
    Delete a generated blog and its files.
    """
    if run_id not in job_status:
        raise HTTPException(status_code=404, detail="Run ID not found")
    
    # Remove from job status
    del job_status[run_id]
    
    # TODO: Delete files from disk
    
    return {"message": f"Blog {run_id} deleted"}


@router.get("/blog/list")
async def list_blogs():
    """
    List all generated blogs.
    """
    return {
        "blogs": [
            {
                "run_id": run_id,
                "status": status["status"],
                "topic": status.get("topic"),
                "created_at": status["created_at"],
                "completed_at": status.get("completed_at")
            }
            for run_id, status in job_status.items()
        ],
        "total": len(job_status)
    }
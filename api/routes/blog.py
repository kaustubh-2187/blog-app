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
from blog_app.run_pipeline import run_blog_pipeline
from blog_app.config.paths_config import get_run_output_dir, get_markdown_dir
from blog_app.services.file_service import _safe_slug
from api.utils.progress_logger import ProgressLogger
import logging

router = APIRouter()

# In-memory storage for job status
job_status = {}

# Storing user-facing progress messages per run_id
job_logs = {}


def load_sample_blogs():
    """Load sample blogs from sample_data/ directory into job_status on startup."""
    from blog_app.services.file_service import _safe_slug
    
    sample_dir = Path("sample_data")
    if not sample_dir.exists():
        return
    
    for blog_dir in sample_dir.iterdir():
        if not blog_dir.is_dir():
            continue
        
        markdown_dir = blog_dir / "markdown"
        if not markdown_dir.exists():
            continue
        
        md_files = list(markdown_dir.glob("*.md"))
        if not md_files:
            continue
        
        # Extract run_id from folder name (last 8 chars after underscore)
        folder_name = blog_dir.name
        run_id = folder_name.split('_')[-1]
        
        # Extract topic from folder name (everything before last underscore)
        topic_slug = '_'.join(folder_name.split('_')[:-1])
        topic = topic_slug.replace('_', ' ').title()
        
        # Count images
        images_dir = blog_dir / "images"
        images_count = len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0
        
        # Add to job_status
        job_status[run_id] = {
            "status": "completed",
            "message": "Sample blog",
            "topic": topic,
            "mode": "sample",
            "plan": None,
            "markdown_path": str(md_files[0]),
            "images_count": images_count,
            "created_at": datetime.fromtimestamp(blog_dir.stat().st_ctime),
            "completed_at": datetime.fromtimestamp(blog_dir.stat().st_ctime)
        }
        logging.info(f"Loaded sample blog: {run_id} - {topic}")


# Load sample blogs on module import
load_sample_blogs()


async def generate_blog_async(request: BlogGenerationRequest, run_id: str):
    """
    Background task to generate blog.
    Emits clean, user-facing progress messages via ProgressLogger.
    """
    job_logs[run_id] = []
    progress = ProgressLogger(run_id, job_logs)

    try:
        job_status[run_id] = {
            "status": "processing",
            "message": "Starting blog generation…",
            "created_at": datetime.now()
        }

        progress.emit("start")
        progress.custom(f"Topic: \"{request.topic}\"")

        # Override LLM provider if user selected one
        if request.provider:
            from blog_app.llm import client as llm_client_module
            loader = llm_client_module.ModelLoader()
            llm_client_module.llm = loader.load_llm(provider_override=request.provider)
            progress.custom(f"Using model provider: {request.provider}")

        # ── Stage 1: routing is the first thing the pipeline does ─────────
        progress.emit("routing")
        job_status[run_id]["message"] = "Analysing topic…"

        def _run_with_progress():
            from blog_app.graph.builder import GraphBuilder
            from datetime import date as _date

            graph_builder = GraphBuilder()
            app = graph_builder.build()

            inputs = {
                "topic": request.topic.strip(),
                "run_id": run_id,
                "mode": "",
                "needs_research": False,
                "queries": [],
                "evidence": [],
                "plan": None,
                "as_of": request.as_of or _date.today().isoformat(),
                "recency_days": 7,
                "sections": [],
                "images_enabled": request.images_enabled,
                "merged_md": "",
                "md_with_placeholders": "",
                "image_specs": [],
                "final": "",
            }

            output = {}
            sections_written = 0
            total_tasks = 0

            try:
                for step in app.stream(inputs, stream_mode="updates"):
                    node = next(iter(step)) if step else None
                    payload = step.get(node, {}) if node else {}

                    if node == "router":
                        mode = payload.get("mode", "")
                        if payload.get("needs_research"):
                            progress.emit("route_research")
                            progress.emit("research_start")
                            job_status[run_id]["message"] = "Searching the web…"
                        else:
                            progress.emit("route_no_research")
                            job_status[run_id]["message"] = "Building outline…"

                    elif node == "research":
                        count = len(payload.get("evidence", []))
                        progress.custom(f"Found {count} relevant source(s) — reviewing…")
                        progress.emit("planning")
                        job_status[run_id]["message"] = "Building outline…"

                    elif node == "orchestrator":
                        plan = payload.get("plan")
                        if plan:
                            total_tasks = len(getattr(plan, "tasks", []) or [])
                            progress.emit("planning_done")
                            progress.custom(
                                f"Plan ready: \"{getattr(plan, 'blog_title', 'Your Blog')}\" "
                                f"— {total_tasks} section{'s' if total_tasks != 1 else ''}"
                            )
                            progress.emit("writing_start")
                            job_status[run_id]["message"] = "Writing sections…"

                    elif node == "worker":
                        sections_written += 1
                        if total_tasks:
                            progress.emit(
                                "writing_section",
                                current=sections_written,
                                total=total_tasks
                            )
                        job_status[run_id]["message"] = (
                            f"Writing section {sections_written}"
                            + (f" of {total_tasks}" if total_tasks else "") + "…"
                        )

                    elif node == "reducer":

                        sub = payload  # may contain merge/decide/generate keys
                        if "merged_md" in sub:
                            progress.emit("merging")
                            job_status[run_id]["message"] = "Assembling post…"
                        if "image_specs" in sub:
                            specs = sub.get("image_specs") or []
                            if specs:
                                progress.emit("images_planning")
                                job_status[run_id]["message"] = "Planning images…"
                            else:
                                progress.emit("images_skip")
                        if "final" in sub and sub["final"]:
                            progress.emit("saving")
                            job_status[run_id]["message"] = "Saving blog…"

                    # Keep rolling output up to date
                    output.update(payload)

            except Exception:
                # Fall back to non-streaming if stream not supported
                output = app.invoke(inputs)

            return output

        result = await asyncio.to_thread(_run_with_progress)

        # ── Done ──────────────────────────────────────────────────────────
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

        title_slug = _safe_slug(plan.blog_title) if plan else "blog"
        run_dir = get_run_output_dir(title_slug, run_id)
        markdown_dir = get_markdown_dir(run_dir)

        images_dir = run_dir / "images"
        images_count = len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0

        md_files = list(markdown_dir.glob("*.md"))
        markdown_path = str(md_files[0]) if md_files else None

        if images_count:
            progress.custom(f"Generated {images_count} image{'s' if images_count != 1 else ''}.")

        progress.emit("done")

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
        progress.emit("error")
        progress.custom(f"Detail: {str(e)}")

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
    import uuid
    run_id = uuid.uuid4().hex[:8]
    background_tasks.add_task(generate_blog_async, request, run_id)
    return BlogGenerationResponse(
        run_id=run_id,
        status="processing",
        message="Blog generation started",
        topic=request.topic
    )


@router.get("/blog/status/{run_id}")
async def get_blog_status(run_id: str):
    if run_id not in job_status:
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")

    status = job_status[run_id]
    logs = job_logs.get(run_id, [])

    return {
        "run_id": run_id,
        "logs": logs,
        **status
    }


@router.get("/blog/download/{run_id}/markdown")
async def download_markdown(run_id: str):
    import zipfile
    import io
    from fastapi.responses import StreamingResponse
    
    if run_id not in job_status:
        raise HTTPException(status_code=404, detail="Run ID not found")

    status = job_status[run_id]
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Blog is still {status['status']}")

    markdown_path = status.get("markdown_path")
    if not markdown_path or not Path(markdown_path).exists():
        raise HTTPException(status_code=404, detail="Markdown file not found")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    run_dir = Path(markdown_path).parent.parent
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add markdown
        zip_file.write(markdown_path, f"markdown/{Path(markdown_path).name}")
        
        # Add images if they exist
        images_dir = run_dir / "images"
        if images_dir.exists():
            for img in images_dir.glob("*.png"):
                zip_file.write(img, f"images/{img.name}")
    
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=blog_{run_id}.zip"}
    )


@router.delete("/blog/{run_id}")
async def delete_blog(run_id: str):
    if run_id not in job_status:
        raise HTTPException(status_code=404, detail="Run ID not found")
    del job_status[run_id]
    return {"message": f"Blog {run_id} deleted"}


@router.get("/blog/list")
async def list_blogs():
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


@router.get("/blog/content/{run_id}")
async def get_markdown_content(run_id: str):
    if run_id not in job_status:
        raise HTTPException(status_code=404, detail="Run ID not found")

    status = job_status[run_id]
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Blog is still {status['status']}")

    markdown_path = status.get("markdown_path")
    if not markdown_path or not Path(markdown_path).exists():
        raise HTTPException(status_code=404, detail="Markdown file not found")

    content = Path(markdown_path).read_text(encoding="utf-8")
    return {"content": content, "path": markdown_path}


@router.get("/blog/images/{run_id}/{filename}")
async def get_image(run_id: str, filename: str):
    if run_id not in job_status:
        raise HTTPException(status_code=404, detail="Run ID not found")
    
    status = job_status[run_id]
    markdown_path = status.get("markdown_path")
    if not markdown_path:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Navigate from markdown path to images dir (works for both local_data and sample_data)
    run_dir = Path(markdown_path).parent.parent
    image_path = run_dir / "images" / filename
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(image_path, media_type="image/png")

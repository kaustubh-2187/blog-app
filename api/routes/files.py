"""
File management endpoints.
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.models.responses import FileListResponse
from blog_app.config.paths_config import get_run_output_dir

router = APIRouter()


@router.get("/files/{run_id}", response_model=FileListResponse)
async def list_files(run_id: str):
    """
    List all files for a given run.
    """
    from blog_app.services.file_service import _safe_slug
    
    # Find the run directory
    data_dir = Path("data")
    run_dirs = list(data_dir.glob(f"*_{run_id}"))
    
    if not run_dirs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_dir = run_dirs[0]
    
    files = []
    for file_path in run_dir.rglob("*"):
        if file_path.is_file():
            files.append({
                "name": file_path.name,
                "path": str(file_path.relative_to(run_dir)),
                "size": file_path.stat().st_size,
                "type": file_path.suffix
            })
    
    return FileListResponse(
        run_id=run_id,
        files=files,
        total_files=len(files)
    )


@router.get("/files/{run_id}/download/{file_path:path}")
async def download_file(run_id: str, file_path: str):
    """
    Download a specific file from a run.
    """
    data_dir = Path("data")
    run_dirs = list(data_dir.glob(f"*_{run_id}"))
    
    if not run_dirs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    full_path = run_dirs[0] / file_path
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(path=full_path, filename=full_path.name)
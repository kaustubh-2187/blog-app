import os
from pathlib import Path

CONFIG_PATH = Path("blog_app\config\config.yaml")

DATA_PATH = Path("data")
IMAGES_PATH = Path("images")

def get_run_output_dir(title_slug: str, run_id: str) -> Path:
    """
    Returns: data/{title}_{uuid}/
    """
    folder_name = f"{title_slug}_{run_id}"
    run_dir = DATA_PATH / folder_name
    
    return run_dir

def get_markdown_dir(run_output_dir: Path) -> Path:
    """
    Returns: data/{title}_{uuid}/markdown/
    """
    return run_output_dir / "markdown"

def get_images_dir(run_output_dir: Path) -> Path:
    """
    Returns: data/{title}_{uuid}/images/
    """
    return run_output_dir / "images"
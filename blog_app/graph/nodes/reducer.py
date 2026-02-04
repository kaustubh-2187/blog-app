import sys
import uuid

from dotenv import load_dotenv
from pathlib import Path

from blog_app.config.config_loader import read_yaml
from blog_app.config.paths_config import *

from blog_app.core.state import State
from blog_app.prompts.prompts import BlogPrompts
from blog_app.core.schemas import GlobalImagePlan
from blog_app.services.file_service import _safe_slug
from blog_app.llm.client import llm
from blog_app.services.image_service import ImageService
from blog_app.logger.custom_logger import CustomLogger
from blog_app.exception.custom_exception import CustomException

from langchain_core.messages import SystemMessage, HumanMessage

logger = CustomLogger().get_logger(__name__)
load_dotenv()

class ReducerNode:
    """
    Final reducer logic:
    - merge worker sections
    - decide if images are needed
    - generate/apply images
    """

    @staticmethod
    def merge_content(state: State) -> dict:
        try:
            plan = state["plan"]
            if plan is None:
                raise ValueError("merge_content called without plan.")

            ordered_sections = [md for _, md in sorted(state["sections"], key=lambda x: x[0])]
            body = "\n\n".join(ordered_sections).strip()
            merged_md = f"# {plan.blog_title}\n\n{body}\n"

            logger.info("Content merged successfully")

            return {"merged_md": merged_md}

        except Exception as e:
            logger.error(f"merge_content failed: {e}")
            raise CustomException("merge_content failed", sys)

    @staticmethod
    def decide_images(state: State) -> dict:
        try:
            config = read_yaml(CONFIG_PATH)
            images_enabled = config.get('images_model', {}).get('enabled', True)

            planner = llm.with_structured_output(GlobalImagePlan)
            merged_md = state["merged_md"]
            plan = state["plan"]

            assert plan is not None

            if not images_enabled:
                logger.info("Image generation disabled in config - skipping image planning")
                return {
                    "md_with_placeholders": merged_md,
                    "image_specs": [],
                }

            image_plan = planner.invoke(
                [
                    SystemMessage(content=BlogPrompts.DECIDE_IMAGES_SYSTEM),
                    HumanMessage(
                        content=(
                            f"Blog kind: {plan.blog_kind}\n"
                            f"Topic: {state['topic']}\n\n"
                            "Insert placeholders + propose image prompts.\n\n"
                            f"{merged_md}"
                        )
                    ),
                ]
            )

            return {
                "md_with_placeholders": image_plan.md_with_placeholders,
                "image_specs": [img.model_dump() for img in image_plan.images],
            }

        except Exception as e:
            logger.error(f"decide_images failed: {e}")
            raise CustomException("decide_images failed", sys)


    @staticmethod
    def generate_and_place_images(state: State) -> dict:
        """
        Final reducer step.
        Delegates all image handling to ImageService.
        """
        try:
            plan = state["plan"]
            run_id = state.get("run_id") or uuid.uuid4().hex[:8]
            logger.info(f"Using run_id: {run_id}") 
            assert plan is not None
            assert run_id is not None

            md = state.get("md_with_placeholders") or state["merged_md"]
            image_specs = state.get("image_specs", []) or []

            # Create folder structure
            title_slug = _safe_slug(plan.blog_title)
            run_output_dir = get_run_output_dir(title_slug, run_id)
            markdown_dir = get_markdown_dir(run_output_dir)

            # Create markdown directory
            markdown_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {run_output_dir}")

             # Markdown filename and path
            md_filename = f"{title_slug}.md"
            md_filepath = markdown_dir / md_filename

            # No images → just write markdown
            if not image_specs:
                md_filepath.write_text(md, encoding="utf-8")
                logger.info("No images requested; markdown written directly")
                return {"final": md}
            
            # ← NEW: Create images directory
            images_dir = get_images_dir(run_output_dir)
            images_dir.mkdir(parents=True, exist_ok=True)

            image_service = ImageService(images_dir)

            logger.info("Applying images to markdown")
            md = image_service.apply_images_to_markdown(md, image_specs)

            # Write markdown with updated image paths
            md_filepath.write_text(md, encoding="utf-8")

            logger.info(f"Final markdown written with images to {md_filepath}")

            return {"final": md}

        except Exception as e:
            logger.error(f"generate_and_place_images failed: {e}")
            raise CustomException("generate_and_place_images failed", sys)
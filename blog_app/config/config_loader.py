import os
import yaml

from blog_app.logger.custom_logger import CustomLogger
from blog_app.exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)


def read_yaml(file_path: str):
    """
    Reads a YAML configuration file and returns it as a dict.
    Simple, explicit, and fail-fast.
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found at path: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        logger.info(f"Config loaded successfully from {file_path}")
        return config

    except Exception as e:
        logger.error("Error while reading config.yaml")
        raise CustomException("Failed to read config.yaml", e)

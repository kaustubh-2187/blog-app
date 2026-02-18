import os
import sys

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from blog_app.config.config_loader import read_yaml
from blog_app.config.paths_config import CONFIG_PATH
from blog_app.logger.custom_logger import CustomLogger
from blog_app.exception.custom_exception import CustomException

load_dotenv()
logger = CustomLogger().get_logger(__name__)


class ModelLoader:
    """
    Loads LLMs based on the provider block in config.yaml.

    config.yaml structure expected:
        llm:
          provider: "google"          # active provider
          groq:
            model_name: ...
            temperature: ...
            max_output_tokens: ...
            max_retries: ...
          google:
            model_name: ...
            temperature: ...
            max_output_tokens: ...
            max_retries: ...
    """

    def __init__(self):
        self.config = read_yaml(CONFIG_PATH)
        self.llm_block = self.config["llm"]
        self.provider = self.llm_block.get("provider", "google")
        logger.info(f"ModelLoader initialised — active provider: {self.provider}")

    def load_llm(self, provider_override: str = None):
        """
        Load and return the configured LLM.

        Args:
            provider_override: Optionally bypass config and force a specific
                               provider (e.g. 'groq' or 'google').

        Returns:
            A LangChain chat model instance.
        """
        provider = provider_override or self.provider

        if provider not in self.llm_block:
            raise ValueError(
                f"Provider '{provider}' not found in config.yaml llm block. "
                f"Available: {[k for k in self.llm_block if k != 'provider']}"
            )

        provider_config = self.llm_block[provider]
        model_name   = provider_config.get("model_name")
        temperature  = provider_config.get("temperature", 0.5)
        max_retries  = provider_config.get("max_retries", 1)
        max_tokens   = provider_config.get("max_output_tokens", 2048)

        logger.info(f"Loading LLM — provider: {provider}, model: {model_name}")

        try:
            if provider == "google":
                return ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    max_retries=max_retries,
                )

            elif provider == "groq":
                return ChatGroq(
                    model_name=model_name,
                    groq_api_key=os.getenv("GROQ_API_KEY"),
                    temperature=temperature,
                    max_retries=max_retries,
                )

            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to load LLM — provider: {provider}, error: {e}")
            raise CustomException("Failed to load LLM", sys)


# ── Module-level singleton ────────────────────────────────────────────────────
# Imported by all graph nodes as:  from blog_app.llm.client import llm
_loader = ModelLoader()
llm = _loader.load_llm()

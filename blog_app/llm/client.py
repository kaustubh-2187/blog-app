import os
from blog_app.config.config_loader import read_yaml
from blog_app.config.paths_config import CONFIG_PATH

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

config = read_yaml(CONFIG_PATH)["llm"]["models"]

if config['provider']=="groq":
    llm = ChatGroq(
        model=config["model_name"], 
        groq_api_key=os.getenv("GROQ_API_KEY"),
        max_retries=config["max_retries"]
    )
elif config['provider']=="google":
    llm = ChatGoogleGenerativeAI(
        model=config["model_name"],
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        max_retries=config.get("max_retries", 1),
        temperature=config.get("temperature", 0.7),
    )
else:
    raise ValueError(
        f"Unsupported LLM provider: {config['provider']}"
    )
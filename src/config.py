import os
from typing import Set
from dotenv import load_dotenv

load_dotenv()

# Environment
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "prod")
IS_LOCAL: bool = ENVIRONMENT == "local"
IS_DEV: bool = ENVIRONMENT == "dev"
IS_PROD: bool = ENVIRONMENT == "prod"

# LLM – Groq
GROQ_API_KEY: str = os.environ["GROQ_API_KEY"]
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Telegram
TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_ALLOWED_USERS: Set[int] = set(
    int(x.strip()) for x in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",") if x.strip()
)

# Notion MCP
NOTION_API_KEY: str = os.environ["NOTION_API_KEY"]

# Google Calendar MCP – path to OAuth credentials JSON file from Google Cloud Console
GOOGLE_OAUTH_CREDENTIALS: str = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "gcp-oauth.keys.json")

# Agent
AGENT_NAME: str = os.getenv("AGENT_NAME", "Work Assistant")
AGENT_INSTRUCTIONS: str = os.getenv(
    "AGENT_INSTRUCTIONS",
    (
        "You are a helpful work assistant. "
        "You can interact with Notion and Google services to help the user manage "
        "their tasks, notes, calendar, and documents."
    ),
)
AGENT_LANGUAGE: str = os.getenv("AGENT_LANGUAGE", "English")

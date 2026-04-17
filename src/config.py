import os
from dotenv import load_dotenv

load_dotenv()

# LLM – Groq
GROQ_API_KEY: str = os.environ["GROQ_API_KEY"]
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Telegram
TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]

# Notion MCP
NOTION_API_KEY: str = os.environ["NOTION_API_KEY"]

# Google MCP – path to the OAuth credentials file issued by Google Cloud Console
GOOGLE_CREDENTIALS_FILE: str = os.getenv(
    "GOOGLE_CREDENTIALS_FILE", "credentials.json"
)

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

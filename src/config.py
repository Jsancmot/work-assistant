import os
from pathlib import Path
from typing import Set
from dotenv import load_dotenv

load_dotenv()

# Environment
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "prod")
IS_LOCAL: bool = ENVIRONMENT == "local"
IS_DEV: bool = ENVIRONMENT == "dev"
IS_PRE: bool = ENVIRONMENT == "pre"
IS_PROD: bool = ENVIRONMENT == "prod"

# LLM – HuggingFace Inference API
HF_API_KEY: str = os.environ["HF_API_KEY"]
HF_MODEL: str = os.getenv("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")

# OpenAI (pre/prod)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Local Ollama (local only)
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Telegram
TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_ALLOWED_USERS: Set[int] = set(
    int(x.strip()) for x in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",") if x.strip()
)

# Notion MCP
NOTION_API_KEY: str = os.environ["NOTION_API_KEY"]
NOTION_MCP_URL: str = os.getenv("NOTION_MCP_URL", "")
NOTION_MCP_SECRET: str = os.getenv("NOTION_MCP_SECRET", "")


def get_user_notion_api_key(user_id: int) -> str:
    """Return the Notion API key for a specific Telegram user.

    Looks for NOTION_API_KEY_<user_id> first; falls back to NOTION_API_KEY.
    """
    return os.getenv(f"NOTION_API_KEY_{user_id}", NOTION_API_KEY)

# Google Calendar MCP – path to OAuth credentials JSON file from Google Cloud Console
GOOGLE_OAUTH_CREDENTIALS: str = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "gcp-oauth.keys.json")

# Agent
AGENT_NAME: str = os.getenv("AGENT_NAME", "Work Assistant")

def _build_main_agent_instructions() -> str:
    """Compose the agent system prompt from the base file and per-tool files."""
    prompts_dir = Path(__file__).parent / "prompts"
    base_file = prompts_dir / "main_agent.md"
    base = base_file.read_text(encoding="utf-8") if base_file.exists() else (
        "You are a helpful work assistant. "
        "Only use tools that are actually available to you. "
        "Never invent data or IDs."
    )
    tool_prompts_dir = prompts_dir / "tools"
    tool_sections: list[str] = []
    if tool_prompts_dir.exists():
        for tool_file in sorted(tool_prompts_dir.glob("*.md")):
            tool_sections.append(tool_file.read_text(encoding="utf-8"))
    if tool_sections:
        return base + "\n\n" + "\n\n".join(tool_sections)
    return base

def _build_notion_agent_instructions() -> str:
    """Read the notion agent instructions."""
    prompts_dir = Path(__file__).parent / "prompts"
    base_file = prompts_dir / "notion_agent.md"
    return base_file.read_text(encoding="utf-8") if base_file.exists() else ""

AGENT_INSTRUCTIONS: str = os.getenv("AGENT_INSTRUCTIONS") or _build_main_agent_instructions()
NOTION_AGENT_INSTRUCTIONS: str = _build_notion_agent_instructions()
AGENT_LANGUAGE: str = os.getenv("AGENT_LANGUAGE", "English")

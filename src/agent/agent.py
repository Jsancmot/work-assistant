"""
Agno agent with Notion and Google MCP tools.
"""

import logging

from agno import Agent
from agno.db.sqlite import SqliteDb
from agno.tools.mcp import MCPTools

from src.config import (
    AGENT_INSTRUCTIONS,
    AGENT_NAME,
    AGENT_LANGUAGE,
    ENVIRONMENT,
    HF_API_KEY,
    HF_MODEL,
    IS_LOCAL,
    IS_PRE,
    IS_PROD,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from src.utils import strip_patterns

try:
    from agno.models.ollama import Ollama
except Exception:
    Ollama = None
try:
    from agno.models.huggingface import HuggingFace
except Exception:
    HuggingFace = None
try:
    from agno.models.openai import OpenAIChat
except Exception:
    OpenAIChat = None

logger = logging.getLogger(__name__)


def create_agent(tools: list[MCPTools], user_id: int | None = None) -> Agent:
    """Instantiate and return the work-assistant Agno agent.

    Args:
        tools: List of already-initialised MCPTools instances to give the agent.
        user_id: Telegram user ID used as session identifier for conversation history.
    """
    instructions = f"{AGENT_INSTRUCTIONS} \n\n Always respond in {AGENT_LANGUAGE}."
    session_id = str(user_id) if user_id is not None else "default"

    model_instance = None
    if IS_LOCAL and Ollama is not None:
        model_instance = Ollama(id=OLLAMA_MODEL, host=OLLAMA_HOST)
        logger.info("Using local Ollama model %s at %s", OLLAMA_MODEL, OLLAMA_HOST)
    elif (IS_PRE or IS_PROD) and OpenAIChat is not None and OPENAI_API_KEY:
        model_instance = OpenAIChat(id=OPENAI_MODEL, api_key=OPENAI_API_KEY)
        logger.info("Using OpenAI model %s (env=%s)", OPENAI_MODEL, ENVIRONMENT)
    elif HuggingFace is not None:
        model_instance = HuggingFace(id=HF_MODEL, api_key=HF_API_KEY, max_tokens=1024)
        logger.info("Using HuggingFace model %s (fallback)", HF_MODEL)

    agent = Agent(
        name=AGENT_NAME,
        model=model_instance,
        tools=tools,
        instructions=instructions,
        db=SqliteDb(db_file="/app/data/agent.db"),
        session_id=session_id,
        markdown=True,
        add_history_to_context=True,
        num_history_runs=3,
    )
    logger.info("Agent created successfully")

    agent_funcs = getattr(agent, "functions", None) or {}
    logger.info("agent.functions count: %d", len(agent_funcs))
    for tool in tools:
        tool_funcs = getattr(tool, "functions", None) or {}
        logger.info("tool %s functions count: %d", type(tool).__name__, len(tool_funcs))

    patched = 0
    for func in agent_funcs.values():
        params = getattr(func, "parameters", None)
        if isinstance(params, dict):
            strip_patterns(params)
            patched += 1

    for tool in tools:
        for func in (getattr(tool, "functions", None) or {}).values():
            params = getattr(func, "parameters", None)
            if isinstance(params, dict):
                strip_patterns(params)
                patched += 1

    logger.info("Patched schemas for %d functions", patched)
    return agent

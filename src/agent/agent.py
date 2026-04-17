"""
Agno agent with Notion and Google MCP tools.
"""

import logging

from agno.agent import Agent
from agno.models.groq import Groq

from src.config import AGENT_INSTRUCTIONS, AGENT_NAME, AGENT_LANGUAGE, GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)


def create_agent() -> Agent:
    """Instantiate and return the work-assistant Agno agent."""
    logger.info("Creating Notion MCP tools...")

    from src.tools.notion_mcp import get_notion_tools
    notion_tools = get_notion_tools()

    instructions = f"{AGENT_INSTRUCTIONS} Always respond in {AGENT_LANGUAGE}."

    agent = Agent(
        name=AGENT_NAME,
        model=Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY),
        tools=[notion_tools],
        instructions=instructions,
        markdown=True,
    )
    logger.info("Agent created successfully")
    return agent

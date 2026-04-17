"""
Agno agent with Notion and Google MCP tools.
"""

from agno.agent import Agent
from agno.models.groq import Groq

from src.config import AGENT_INSTRUCTIONS, AGENT_NAME, GROQ_API_KEY, GROQ_MODEL
from src.tools.google_mcp import get_google_tools
from src.tools.notion_mcp import get_notion_tools


def create_agent() -> Agent:
    """Instantiate and return the work-assistant Agno agent."""
    notion_tools = get_notion_tools()
    google_tools = get_google_tools()

    agent = Agent(
        name=AGENT_NAME,
        model=Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY),
        tools=[notion_tools, google_tools],
        instructions=AGENT_INSTRUCTIONS,
        markdown=True,
        show_tool_calls=False,
    )
    return agent

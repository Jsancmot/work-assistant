"""
Agno agent with Notion and Google MCP tools.
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.config import AGENT_INSTRUCTIONS, AGENT_NAME, OPENAI_API_KEY, OPENAI_MODEL
from src.tools.google_mcp import get_google_tools
from src.tools.notion_mcp import get_notion_tools


def create_agent() -> Agent:
    """Instantiate and return the work-assistant Agno agent."""
    notion_tools = get_notion_tools()
    google_tools = get_google_tools()

    agent = Agent(
        name=AGENT_NAME,
        model=OpenAIChat(id=OPENAI_MODEL, api_key=OPENAI_API_KEY),
        tools=[notion_tools, google_tools],
        instructions=AGENT_INSTRUCTIONS,
        markdown=True,
        show_tool_calls=False,
    )
    return agent

"""
Google Calendar MCP tool – wraps @cocal/google-calendar-mcp
via Agno's MCPTools integration.
"""

from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

from src.config import GOOGLE_OAUTH_CREDENTIALS

_google_tools: MCPTools | None = None


def get_google_tools() -> MCPTools:
    """Return a cached MCPTools instance connected to the Google Calendar MCP server."""
    global _google_tools
    if _google_tools is None:
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@cocal/google-calendar-mcp"],
            env={
                "GOOGLE_OAUTH_CREDENTIALS": GOOGLE_OAUTH_CREDENTIALS,
            },
        )
        _google_tools = MCPTools(server_params=server_params)
    return _google_tools

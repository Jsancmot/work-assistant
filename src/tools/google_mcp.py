"""
Google MCP tool – wraps the community Google MCP server
(@modelcontextprotocol/server-gdrive) via Agno's MCPTools integration.

The server gives the agent access to Google Drive (search, read, list files).
Extend the `args` list to enable additional Google services as needed.
"""

from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

from src.config import GOOGLE_CREDENTIALS_FILE

_google_tools: MCPTools | None = None


def get_google_tools() -> MCPTools:
    """Return a cached MCPTools instance connected to the Google MCP server."""
    global _google_tools
    if _google_tools is None:
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-gdrive"],
            env={"GOOGLE_APPLICATION_CREDENTIALS": GOOGLE_CREDENTIALS_FILE},
        )
        _google_tools = MCPTools(server_params=server_params)
    return _google_tools

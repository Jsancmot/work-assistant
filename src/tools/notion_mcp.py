"""
Notion MCP tool – wraps the official Notion MCP server
(@notionhq/notion-mcp-server) via Agno's MCPTools integration.
"""

from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

from src.config import NOTION_API_KEY

_notion_tools: MCPTools | None = None


def get_notion_tools() -> MCPTools:
    """Return a cached MCPTools instance connected to the Notion MCP server."""
    global _notion_tools
    if _notion_tools is None:
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@notionhq/notion-mcp-server"],
            env={"NOTION_API_KEY": NOTION_API_KEY},
        )
        _notion_tools = MCPTools(server_params=server_params)
    return _notion_tools

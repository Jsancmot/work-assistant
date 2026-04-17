"""
Notion MCP tool – wraps the official Notion MCP server
(@notionhq/notion-mcp-server) via Agno's MCPTools integration.
"""

import asyncio
import logging
import os

from agno.tools.mcp import MCPTools

logger = logging.getLogger(__name__)

_notion_tools: MCPTools | None = None


async def _create_notion_tools() -> MCPTools:
    """Create the Notion MCP tools."""
    logger.info("Creating Notion MCP tools...")
    notion_token = os.environ.get("NOTION_TOKEN")
    if not notion_token:
        from src.config import NOTION_API_KEY
        notion_token = NOTION_API_KEY
        os.environ["NOTION_TOKEN"] = notion_token

    mcp_tools = MCPTools(
        command="npx -y @notionhq/notion-mcp-server",
    )
    await mcp_tools.connect()
    return mcp_tools


def get_notion_tools() -> MCPTools:
    """Return cached Notion MCP tools instance."""
    global _notion_tools
    if _notion_tools is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _notion_tools = loop.run_until_complete(_create_notion_tools())
        loop.close()
    return _notion_tools

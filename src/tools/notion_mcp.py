"""
Notion MCP tool – wraps the official Notion MCP server
(@notionhq/notion-mcp-server) via Agno's MCPTools integration.
"""

import asyncio
import concurrent.futures
import logging
import os

from agno.tools.mcp import MCPTools

logger = logging.getLogger(__name__)

_notion_tools: MCPTools | None = None


def get_notion_tools() -> MCPTools:
    """Return cached Notion MCP tools instance."""
    global _notion_tools
    if _notion_tools is None:
        logger.info("Creating Notion MCP tools...")
        notion_token = os.environ.get("NOTION_TOKEN")
        if not notion_token:
            from src.config import NOTION_API_KEY
            notion_token = NOTION_API_KEY
            os.environ["NOTION_TOKEN"] = notion_token

        _notion_tools = MCPTools(
            command="npx -y @notionhq/notion-mcp-server",
        )

        async def _connect():
            await _notion_tools.connect()

        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _connect())
                future.result()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_connect())
            loop.close()

        logger.info(f"Notion MCP tools loaded: {len(_notion_tools.tools)}")

    return _notion_tools
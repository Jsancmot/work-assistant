"""Notion MCP tools via HTTP transport."""

import logging

logger = logging.getLogger(__name__)

_notion_mcp_tools: list | None = None


async def _load_notion_mcp_tools_async() -> list:
    """Load tools from Notion MCP server via HTTP (async)."""
    from src.config import NOTION_API_KEY, NOTION_MCP_URL, NOTION_MCP_SECRET
    
    if not NOTION_API_KEY or not NOTION_MCP_URL:
        raise ValueError("NOTION_API_KEY or NOTION_MCP_URL not configured")
    
    from langchain_mcp_adapters.client import MultiServerMCPClient
    
    client = MultiServerMCPClient({
        "notion": {
            "url": NOTION_MCP_URL,
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {NOTION_MCP_SECRET}",
                "NOTION_KEY": NOTION_API_KEY,
                "Notion-Version": "2022-06-28",
            },
        }
    })
    
    tools = await client.get_tools()
    logger.info(f"Loaded {len(tools)} Notion MCP tools")
    return tools


async def _load_with_retry(max_retries: int = 3, delay: float = 2.0) -> list:
    """Load tools with retry on failure."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return await _load_notion_mcp_tools_async()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning(f"MCP load attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                import asyncio
                await asyncio.sleep(delay)
    raise last_error


def init_notion_mcp_tools() -> None:
    """Load Notion MCP tools at startup. Call once from main."""
    global _notion_mcp_tools
    try:
        import asyncio
        _notion_mcp_tools = asyncio.run(_load_with_retry(max_retries=3, delay=2.0))
        logger.info(f"Loaded {len(_notion_mcp_tools)} Notion MCP tools")
    except Exception as e:
        logger.error(f"Failed to load Notion MCP tools after retries: {e}")
        _notion_mcp_tools = []


def get_notion_tools() -> list:
    """Get Notion MCP tools (pre-loaded)."""
    if _notion_mcp_tools is None:
        init_notion_mcp_tools()
    return _notion_mcp_tools or []
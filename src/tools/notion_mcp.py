"""
Notion tool – wraps Agno's built-in NotionTools (REST API, no subprocess).
Compatible with serverless environments like Vercel.
"""

import logging

from agno.tools.notion import NotionTools

logger = logging.getLogger(__name__)

_notion_tools: NotionTools | None = None


def get_notion_tools() -> NotionTools:
    """Return cached NotionTools instance."""
    global _notion_tools
    if _notion_tools is not None:
        return _notion_tools

    logger.info("Creating Notion tools...")
    from src.config import NOTION_API_KEY

    _notion_tools = NotionTools(api_key=NOTION_API_KEY)
    logger.info("Notion tools ready")
    return _notion_tools
"""
Notion tool – wraps Agno's built-in NotionTools (REST API, no subprocess).
Compatible with serverless environments like Vercel.
"""

import logging

from agno.tools.notion import NotionTools

logger = logging.getLogger(__name__)

# Cache keyed by API key so each user gets their own instance
_notion_tools_cache: dict[str, NotionTools] = {}


def get_notion_tools(api_key: str | None = None) -> NotionTools:
    """Return a NotionTools instance for the given API key.

    If no key is provided, falls back to the global NOTION_API_KEY from config.
    Results are cached per API key.
    """
    if api_key is None:
        from src.config import NOTION_API_KEY
        api_key = NOTION_API_KEY

    if api_key not in _notion_tools_cache:
        logger.info("Creating Notion tools for key ...%s", api_key[-6:])
        _notion_tools_cache[api_key] = NotionTools(api_key=api_key)

    return _notion_tools_cache[api_key]
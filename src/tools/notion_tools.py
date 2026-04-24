"""
Direct Notion tools using official Notion SDK.
LangChain-compatible tools for use with LangGraph.
"""

import json
import logging
from typing import Annotated

from notion_client import AsyncClient
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


class NotionTools:
    """Notion API client wrapper."""
    
    def __init__(self, api_key: str):
        self.client = AsyncClient(auth=api_key)
    
    async def search(self, query: str = ""):
        results = []
        
        search_response = await self.client.search(
            query=query,
            page_size=20,
        )
        results = search_response.get("results", [])
        
        parsed = []
        for r in results:
            obj_type = r.get("object")
            if obj_type == "page":
                title = r.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
            elif obj_type == "database":
                title = r.get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
            else:
                title = "Unknown"
            
            parsed.append({
                "id": r.get("id"),
                "type": obj_type,
                "title": title,
                "url": r.get("url"),
            })
        
        return json.dumps(parsed[:10])
    
    async def list_pages(self):
        response = await self.client.search(
            filter={"value": "page", "property": "object"},
            page_size=50,
        )
        results = response.get("results", [])
        return json.dumps([
            {
                "id": r.get("id"),
                "title": r.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled"),
                "url": r.get("url"),
            }
            for r in results[:20]
        ])
    
    async def list_databases(self):
        response = await self.client.search(
            filter={"value": "database", "property": "object"},
            page_size=20,
        )
        results = response.get("results", [])
        return json.dumps([
            {
                "id": r.get("id"),
                "title": r.get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled"),
                "url": r.get("url"),
            }
            for r in results
        ])
    
    async def get_page(self, page_id: str):
        try:
            page = await self.client.pages.retrieve(page_id=page_id)
            blocks = await self.client.blocks.children.list(block_id=page_id)
            content = []
            for block in blocks.get("results", [])[:20]:
                block_type = block.get("type")
                if block_type == "paragraph":
                    text = block.get("paragraph", {}).get("rich_text", [])
                    if text:
                        content.append("".join(t.get("plain_text", "") for t in text))
            return json.dumps({
                "id": page.get("id"),
                "url": page.get("url"),
                "content": content[:5]
            })
        except Exception as e:
            return f"Error: {e}"
    
    async def create_page(self, parent_id: str | None, title: str, content: str = ""):
        try:
            properties = {"title": {"title": [{"text": {"content": title}}]}}
            page = await self.client.pages.create(
                parent={"page_id": parent_id},
                properties=properties,
            )
            if content:
                await self.client.blocks.children.append(
                    block_id=page["id"],
                    children=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": content}}]}}],
                )
            return json.dumps({"id": page["id"], "url": page["url"]})
        except Exception as e:
            return f"Error: {e}"


_notion_clients: dict[int, NotionTools] = {}


def get_notion_tools(api_key: str, user_id: int | None = None) -> NotionTools:
    key_id = user_id or 0
    if key_id not in _notion_clients:
        _notion_clients[key_id] = NotionTools(api_key)
        logger.info(f"Created Notion client for user {key_id}")
    return _notion_clients[key_id]


@tool
async def notion_search(query: Annotated[str, "Search query for Notion"]) -> str:
    """Search Notion pages and databases."""
    from src.config import NOTION_API_KEY
    tools = get_notion_tools(NOTION_API_KEY)
    return await tools.search(query)


@tool
async def notion_list_databases() -> str:
    """List all Notion databases."""
    from src.config import NOTION_API_KEY
    tools = get_notion_tools(NOTION_API_KEY)
    return await tools.list_databases()


@tool
async def notion_list_pages() -> str:
    """List all Notion pages."""
    from src.config import NOTION_API_KEY
    tools = get_notion_tools(NOTION_API_KEY)
    return await tools.list_pages()


@tool
async def notion_get_page(page_id: Annotated[str, "Notion page ID"]) -> str:
    """Get Notion page content."""
    from src.config import NOTION_API_KEY
    tools = get_notion_tools(NOTION_API_KEY)
    return await tools.get_page(page_id)


@tool
async def notion_create_page(
    title: Annotated[str, "Page title"],
    content: Annotated[str, "Page content"] = "",
) -> str:
    """Create new Notion page."""
    from src.config import NOTION_API_KEY
    tools = get_notion_tools(NOTION_API_KEY)
    return await tools.create_page(None, title, content)
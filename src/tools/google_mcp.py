"""
Google Calendar MCP tool – wraps @cocal/google-calendar-mcp
via Agno's MCPTools integration.
"""

from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

from src.config import GOOGLE_OAUTH_CREDENTIALS
from src.utils import strip_patterns


def get_google_tools() -> MCPTools:
    """Return an MCPTools instance connected to the Google Calendar MCP server.

    The returned instance must be used as an async context manager to start
    the underlying npx subprocess.
    """
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@cocal/google-calendar-mcp"],
        env={
            "GOOGLE_OAUTH_CREDENTIALS": GOOGLE_OAUTH_CREDENTIALS,
        },
    )
    return MCPTools(server_params=server_params)


def patch_tool_schemas(tools: MCPTools) -> None:
    """Remove invalid regex 'pattern' fields from tool parameter schemas.

    Groq rejects JSON schemas with lookahead regexes (e.g. in create-event).
    This patches the schemas in-place after the MCP server has started.
    """
    for func in (getattr(tools, "functions", None) or {}).values():
        params = getattr(func, "parameters", None)
        if isinstance(params, dict):
            strip_patterns(params)

"""
Agent Loop.

High-level factory for creating the multi-agent LangGraph graph.
Responsible only for graph wiring — no message I/O, no hooks.
Inspired by Nanobot's loop.py pattern.
"""

from __future__ import annotations

import inspect
import logging
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.tools import StructuredTool, tool
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

# Cache the detected system-prompt parameter name so we only call inspect once.
_sp_param: str | None = None
_sp_param_resolved = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_sp_param(create_react_agent) -> str | None:
    """Detect which kwarg name create_react_agent accepts for the system prompt."""
    global _sp_param, _sp_param_resolved
    if not _sp_param_resolved:
        accepted = set(inspect.signature(create_react_agent).parameters)
        if "state_modifier" in accepted:
            _sp_param = "state_modifier"
        elif "prompt" in accepted:
            _sp_param = "prompt"
        elif "messages_modifier" in accepted:
            _sp_param = "messages_modifier"
        else:
            logger.warning("create_react_agent: no system-prompt parameter found — prompt omitted")
            _sp_param = None
        _sp_param_resolved = True
    return _sp_param


def _sp_kwargs(param: str | None, system_prompt: str) -> dict[str, Any]:
    """Build the correct kwarg dict for a given system prompt."""
    msg = SystemMessage(content=system_prompt)
    if param == "state_modifier":
        return {"state_modifier": msg}
    if param == "prompt":
        return {"prompt": system_prompt}
    if param == "messages_modifier":
        return {"messages_modifier": lambda msgs: (msg, *msgs)}
    return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_agent(
    tools: list[StructuredTool],
    model,
    system_prompt: str,
    notion_system_prompt: str | None = None,
    user_id: str = "default",
):
    """Create and return a compiled LangGraph multi-agent graph.

    Architecture:
    - An inner **Notion Agent** handles all Notion-specific tools.
    - The outer **Main Agent** receives everything else plus two tools:
      ``gestionar_notion`` (delegates to the inner agent) and
      ``buscar_en_internet`` (DuckDuckGo search).

    Args:
        tools: All available StructuredTool instances.
        model: LangChain chat model (ChatOllama, ChatOpenAI, …).
        system_prompt: System prompt for the main agent.
        notion_system_prompt: System prompt for the Notion sub-agent.
            Defaults to *system_prompt* when not provided.
        user_id: Session identifier string (used in logging only here).

    Returns:
        A compiled LangGraph CompiledGraph ready for ``ainvoke``.
    """
    from langgraph.prebuilt import create_react_agent

    sp_param = _detect_sp_param(create_react_agent)
    checkpointer = MemorySaver()

    # Split tools: Notion-specific vs general
    _notion_keywords = ("notion", "page", "database", "block", "comment")
    notion_tools = [t for t in tools if any(kw in t.name.lower() for kw in _notion_keywords)]
    general_tools = [t for t in tools if t not in notion_tools]

    # ── Inner Notion Agent ────────────────────────────────────────────────────
    n_prompt = notion_system_prompt or system_prompt
    notion_agent = create_react_agent(
        model,
        notion_tools,
        checkpointer=MemorySaver(),
        **_sp_kwargs(sp_param, n_prompt),
    )

    @tool
    async def gestionar_notion(solicitud: str) -> str:
        """Delegate to the Notion Expert Agent.

        ONLY use this tool when the user's request explicitly involves Notion:
        tasks, notes, reading or writing pages/databases.
        Do NOT call it for greetings or general questions.
        Describe the request in detail via 'solicitud'.
        """
        try:
            logger.info("[%s] → Notion Agent: %s", user_id, solicitud[:120])
            res = await notion_agent.ainvoke(
                {"messages": [("user", solicitud)]},
                config={"configurable": {"thread_id": f"notion_sub_{user_id}"}},
            )
            return res["messages"][-1].content
        except Exception as exc:
            return f"The Notion Agent failed: {exc}"

    # ── Internet search tool ──────────────────────────────────────────────────
    @tool
    def buscar_en_internet(query: str) -> str:
        """Real-time internet search via DuckDuckGo.

        Use this for: current news, weather, or any fact requiring up-to-date data.
        Pass a short, direct search query in 'query'.
        """
        from langchain_community.tools import DuckDuckGoSearchRun  # lazy import

        try:
            logger.info("[%s] → Search: %s", user_id, query)
            return DuckDuckGoSearchRun().invoke(query)
        except Exception as exc:
            return f"Search error: {exc}"

    # ── Outer Main Agent ──────────────────────────────────────────────────────
    final_tools = general_tools + [gestionar_notion, buscar_en_internet]
    agent = create_react_agent(
        model,
        final_tools,
        checkpointer=checkpointer,
        **_sp_kwargs(sp_param, system_prompt),
    )

    logger.info(
        "[%s] Agent created — %d total tools (%d notion, %d general)",
        user_id,
        len(final_tools),
        len(notion_tools),
        len(general_tools),
    )
    return agent

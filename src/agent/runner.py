"""
Agent Runner.

Low-level execution layer: invokes the compiled LangGraph agent, emits hook
events, and returns the final text response.
Extracted from langgraph_agent.run_agent and inspired by Nanobot's runner.py.
"""

from __future__ import annotations

import logging
import time

from langchain_core.messages import AIMessage, ToolMessage

from src.agent.hook import AgentHook, NullHook, ToolEvent

logger = logging.getLogger(__name__)


async def run(
    agent,
    message: str,
    user_id: str = "default",
    hook: AgentHook | None = None,
) -> str:
    """Invoke *agent* with *message* and return the final text response.

    Args:
        agent: A compiled LangGraph agent (result of ``loop.create_agent``).
        message: The user's input text.
        user_id: Session identifier (used for the LangGraph thread_id).
        hook: Optional hook to receive lifecycle events.

    Returns:
        The agent's final response as a string.

    Raises:
        Exception: Propagates any unhandled agent error after logging.
    """
    h = hook or NullHook()
    config = {"configurable": {"thread_id": user_id}}

    await h.on_iteration_start(user_id)

    t0 = time.perf_counter()
    logger.info("[%s] run start — %r", user_id, message[:120])

    try:
        result = await agent.ainvoke(
            {"messages": [("user", message)]},
            config=config,
        )

        elapsed = time.perf_counter() - t0
        messages = result.get("messages", [])
        logger.info("[%s] completed in %.2fs — %d msgs", user_id, elapsed, len(messages))

        # Emit tool events for observability / hook consumers
        for msg in messages:
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for call in msg.tool_calls:
                    await h.on_tool_start(
                        user_id,
                        ToolEvent(name=call["name"], args=call.get("args", {})),
                    )
            elif isinstance(msg, ToolMessage):
                await h.on_tool_end(user_id, msg.name or "", str(msg.content)[:500])

            # Debug logging
            if logger.isEnabledFor(logging.DEBUG):
                _log_message(user_id, msg)

        response = ""
        if messages:
            last = messages[-1]
            response = last.content if hasattr(last, "content") else str(last)
        else:
            logger.warning("[%s] Agent returned no messages", user_id)
            response = "No response"

        await h.on_iteration_end(user_id, response)
        return response

    except Exception as exc:
        elapsed = time.perf_counter() - t0
        logger.exception("[%s] Agent error after %.2fs: %s", user_id, elapsed, exc)
        raise


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _log_message(user_id: str, msg) -> None:
    kind = type(msg).__name__
    if isinstance(msg, AIMessage) and msg.tool_calls:
        calls = [f"{c['name']}({c.get('args', {})})" for c in msg.tool_calls]
        logger.debug("[%s] %s → tool_calls: %s", user_id, kind, calls)
    elif isinstance(msg, ToolMessage):
        logger.debug("[%s] ToolMessage name=%r → %s", user_id, msg.name, str(msg.content)[:200])
    elif isinstance(msg, AIMessage):
        logger.debug("[%s] %s → %s", user_id, kind, str(msg.content)[:200])
    else:
        logger.debug("[%s] %s", user_id, kind)

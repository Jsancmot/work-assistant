"""
LangGraph agent with Notion and Google MCP tools.
Replaces Agno agent for better tool-calling control.
"""

import json
import logging
import time

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


def create_langgraph_agent(
    tools: list[StructuredTool],
    model,
    system_prompt: str,
    user_id: int | None = None,
):
    """Create a LangGraph ReAct agent with tools.

    Args:
        tools: List of StructuredTool instances
        model: LLM model instance (e.g., ChatOllama)
        system_prompt: System instructions
        user_id: Optional user ID for session isolation
    """
    from langgraph.prebuilt import create_react_agent
    import inspect

    session_id = str(user_id) if user_id is not None else "default"

    checkpointer = MemorySaver()
    system_message = SystemMessage(content=system_prompt)

    # The system-prompt parameter was renamed across LangGraph 0.2.x releases:
    #   messages_modifier  → state_modifier → prompt
    # Detect at runtime which one this install accepts.
    accepted = set(inspect.signature(create_react_agent).parameters)
    if "state_modifier" in accepted:
        sp_kwargs: dict = {"state_modifier": system_message}
    elif "prompt" in accepted:
        sp_kwargs = {"prompt": system_prompt}
    elif "messages_modifier" in accepted:
        sp_kwargs = {"messages_modifier": lambda msgs: [system_message] + list(msgs)}
    else:
        logger.warning("create_react_agent: no system-prompt parameter found — prompt will be omitted")
        sp_kwargs = {}

    agent = create_react_agent(model, tools, checkpointer=checkpointer, **sp_kwargs)

    logger.info(f"LangGraph agent created: {len(tools)} tools, session_id={session_id}")

    return agent


async def run_agent(agent, user_message: str, user_id: int | None = None):
    """Run the agent with a user message."""
    session_id = str(user_id) if user_id is not None else "default"
    config = {"configurable": {"thread_id": session_id}}

    logger.info(f"[{session_id}] run_agent start — message: {user_message!r}")
    t_start = time.perf_counter()

    try:
        result = await agent.ainvoke(
            {"messages": [("user", user_message)]},
            config=config,
        )

        elapsed = time.perf_counter() - t_start
        messages = result.get("messages", [])
        logger.info(
            f"[{session_id}] ainvoke completed in {elapsed:.2f}s — {len(messages)} messages in thread"
        )

        # Log every message in the returned thread for debugging
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__
            if isinstance(msg, AIMessage) and msg.tool_calls:
                calls = [
                    f"{c['name']}({json.dumps(c.get('args', {}))[:120]})"
                    for c in msg.tool_calls
                ]
                logger.info(f"[{session_id}] msg[{i}] {msg_type} → tool_calls: {calls}")
            elif isinstance(msg, ToolMessage):
                content_preview = str(msg.content)[:200]
                logger.info(
                    f"[{session_id}] msg[{i}] ToolMessage name={msg.name!r} → {content_preview}"
                )
            elif isinstance(msg, AIMessage):
                logger.info(
                    f"[{session_id}] msg[{i}] {msg_type} → {str(msg.content)[:200]}"
                )
            else:
                logger.debug(f"[{session_id}] msg[{i}] {msg_type}")

        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                return last_message.content
            return str(last_message)

        logger.warning(f"[{session_id}] No messages returned by agent")
        return "No response"

    except Exception as e:
        elapsed = time.perf_counter() - t_start
        logger.exception(f"[{session_id}] Agent error after {elapsed:.2f}s: {e}")
        return f"Error: {str(e)}"

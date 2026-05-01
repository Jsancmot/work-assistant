"""
LangGraph agent with Notion and Google MCP tools.
Replaces Agno agent for better tool-calling control.
"""

import functools
import inspect
import logging
import time

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool, tool
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

_langgraph_param_checked = False
_langgraph_sp_param = None


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

    global _langgraph_param_checked, _langgraph_sp_param

    session_id = str(user_id) if user_id is not None else "default"

    checkpointer = MemorySaver()
    system_message = SystemMessage(content=system_prompt)

    if not _langgraph_param_checked:
        accepted = set(inspect.signature(create_react_agent).parameters)
        if "state_modifier" in accepted:
            _langgraph_sp_param = "state_modifier"
        elif "prompt" in accepted:
            _langgraph_sp_param = "prompt"
        elif "messages_modifier" in accepted:
            _langgraph_sp_param = "messages_modifier"
        _langgraph_param_checked = True

    if _langgraph_sp_param == "state_modifier":
        sp_kwargs = {"state_modifier": system_message}
    elif _langgraph_sp_param == "prompt":
        sp_kwargs = {"prompt": system_prompt}
    elif _langgraph_sp_param == "messages_modifier":
        sp_kwargs = {"messages_modifier": lambda msgs: (system_message, *msgs)}
    else:
        logger.warning("create_react_agent: no system-prompt parameter found — prompt will be omitted")
        sp_kwargs = {}

    # Separate notion tools from general tools
    notion_tools = [t for t in tools if "notion" in t.name.lower() or "search" in t.name.lower() or "page" in t.name.lower() or "API" in t.name]
    general_tools = [t for t in tools if t not in notion_tools]

    # Create specialized Notion Agent
    from src.config import NOTION_AGENT_INSTRUCTIONS
    notion_system_prompt = NOTION_AGENT_INSTRUCTIONS
    notion_agent = create_react_agent(
        model, 
        notion_tools,
        # Checkpointer not strictly necessary for sub-agent unless we want sub-memory
        checkpointer=MemorySaver(),
        **({"state_modifier": SystemMessage(content=notion_system_prompt)} if _langgraph_sp_param == "state_modifier" else
           {"prompt": notion_system_prompt} if _langgraph_sp_param == "prompt" else
           {"messages_modifier": lambda msgs: (SystemMessage(content=notion_system_prompt), *msgs)} if _langgraph_sp_param == "messages_modifier" else {})
    )

    @tool
    async def gestionar_notion(solicitud: str) -> str:
        """
        Delegate this task to the Notion Expert Agent.
        ONLY use this tool if the user's request explicitly refers to Notion
        (tasks, notes, reading documents or writing information to the system or wiki).
        Do NOT use this tool for greetings, casual questions, or polite responses like "Good morning".
        If the user just greets, return the greeting directly.
        Pass a detailed description in 'solicitud'.
        """
        try:
            logger.info(f"[{session_id}] Delegating to Notion Agent: {solicitud}")
            res = await notion_agent.ainvoke(
                {"messages": [("user", solicitud)]},
                config={"configurable": {"thread_id": f"notion_sub_{session_id}"}}
            )
            return res["messages"][-1].content
        except Exception as e:
            return f"The Notion Agent failed to process: {e}"

    # The outer agent (general) only has the delegation tool + any non-notion tools
    @tool
    def buscar_en_internet(query: str) -> str:
        """
        Perform a real-time internet search.
        ALWAYS use this when the user asks about: current news, the weather, or real-world information that requires up-to-date data for today.
        Pass a concise and direct search query in 'query'.
        """
        from langchain_community.tools import DuckDuckGoSearchRun
        try:
            logger.info(f"[{session_id}] Internet search: {query}")
            search = DuckDuckGoSearchRun()
            return search.invoke(query)
        except Exception as e:
            return f"There was an error searching the internet: {e}"

    final_tools = general_tools + [gestionar_notion, buscar_en_internet]
    agent = create_react_agent(model, final_tools, checkpointer=checkpointer, **sp_kwargs)

    logger.info(f"LangGraph Multi-Agent created: {len(final_tools)} general tools, session_id={session_id}")

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
        if logger.isEnabledFor(logging.DEBUG):
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    calls = [f"{c['name']}({c.get('args', {})})" for c in msg.tool_calls]
                    logger.debug(f"[{session_id}] msg[{i}] {msg_type} → tool_calls: {calls}")
                elif isinstance(msg, ToolMessage):
                    content_preview = str(msg.content)[:200]
                    logger.debug(
                        f"[{session_id}] msg[{i}] ToolMessage name={msg.name!r} → {content_preview}"
                    )
                elif isinstance(msg, AIMessage):
                    logger.debug(
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

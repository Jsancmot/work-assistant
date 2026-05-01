"""
Agent hook system.

Provides a lifecycle event interface (inspired by Nanobot) so that channels
(Telegram, CLI, …) can react to agent events without coupling to the runner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolEvent:
    """Metadata emitted when the agent invokes a tool."""

    name: str
    args: dict[str, Any] = field(default_factory=dict)


class AgentHook:
    """Base hook — all methods are no-ops so subclasses only override what they need."""

    async def on_iteration_start(self, user_id: str) -> None:
        """Called at the very start of a new user-message processing cycle."""

    async def on_tool_start(self, user_id: str, event: ToolEvent) -> None:
        """Called just before a tool is invoked."""

    async def on_tool_end(self, user_id: str, name: str, result: str) -> None:
        """Called after a tool returns its result."""

    async def on_message_chunk(self, user_id: str, chunk: str) -> None:
        """Called for each streamed token/chunk from the LLM (if streaming is enabled)."""

    async def on_iteration_end(self, user_id: str, response: str) -> None:
        """Called after the agent finishes producing its final response."""


class NullHook(AgentHook):
    """Explicit no-op hook — use when no side-effects are needed."""


class CompositeHook(AgentHook):
    """Combines multiple hooks, calling each in sequence."""

    def __init__(self, *hooks: AgentHook) -> None:
        self._hooks = hooks

    async def on_iteration_start(self, user_id: str) -> None:
        for h in self._hooks:
            await h.on_iteration_start(user_id)

    async def on_tool_start(self, user_id: str, event: ToolEvent) -> None:
        for h in self._hooks:
            await h.on_tool_start(user_id, event)

    async def on_tool_end(self, user_id: str, name: str, result: str) -> None:
        for h in self._hooks:
            await h.on_tool_end(user_id, name, result)

    async def on_message_chunk(self, user_id: str, chunk: str) -> None:
        for h in self._hooks:
            await h.on_message_chunk(user_id, chunk)

    async def on_iteration_end(self, user_id: str, response: str) -> None:
        for h in self._hooks:
            await h.on_iteration_end(user_id, response)

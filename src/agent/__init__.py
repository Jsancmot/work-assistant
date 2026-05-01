"""
Agent package.

Nanobot-inspired modular architecture:
  - hook     : Lifecycle event interface (AgentHook, CompositeHook)
  - skills   : Dynamic Markdown skill loader (SkillRegistry)
  - context  : System-prompt assembler (ContextBuilder)
  - memory   : Per-user file-backed long-term memory (MemoryStore)
  - loop     : LangGraph graph factory (create_agent)
  - runner   : Low-level execution with hook emission (run)
"""

from src.agent.hook import AgentHook, CompositeHook, NullHook, ToolEvent
from src.agent.skills import SkillRegistry
from src.agent.context import ContextBuilder
from src.agent.memory import MemoryStore
from src.agent import loop, runner

__all__ = [
    "AgentHook",
    "CompositeHook",
    "NullHook",
    "ToolEvent",
    "SkillRegistry",
    "ContextBuilder",
    "MemoryStore",
    "loop",
    "runner",
]

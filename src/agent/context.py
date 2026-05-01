"""
Context Builder.

Assembles the final system prompt from the base instructions, active skills
(Markdown files), memory, and language preference.
Inspired by Nanobot's context.py pattern.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.agent.skills import SkillRegistry

logger = logging.getLogger(__name__)

_DEFAULT_BASE_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "main_agent.md"
_DEFAULT_NOTION_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "notion_agent.md"


class ContextBuilder:
    """Builds the system prompt dynamically.

    Args:
        base_prompt: The root system instructions (contents of main_agent.md).
        skills: A SkillRegistry providing tool-specific Markdown docs.
        language: Language the agent should respond in.
    """

    def __init__(
        self,
        base_prompt: str,
        skills: SkillRegistry | None = None,
        language: str = "Spanish",
    ) -> None:
        self._base = base_prompt
        self._skills = skills or SkillRegistry()
        self._language = language

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        active_skills: list[str] | None = None,
        memory: str | None = None,
    ) -> str:
        """Return the fully assembled system prompt.

        Args:
            active_skills: List of skill names to inject. Pass ``None`` to
                include all available skills (default behaviour).
            memory: Optional memory content to append at the end.
        """
        parts: list[str] = [self._base, f"Always respond in {self._language}."]

        if active_skills is not None:
            for name in active_skills:
                content = self._skills.load(name)
                if content:
                    parts.append(content)
                else:
                    logger.warning("Skill '%s' not found — skipping.", name)
        else:
            for content in self._skills.load_all().values():
                parts.append(content)

        if memory:
            parts.append(f"## Long-term Memory\n{memory}")

        return "\n\n".join(parts)

    @property
    def available_skills(self) -> list[str]:
        return self._skills.list_skills()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def load_base_prompt(path: Path | None = None) -> str:
    """Read the main agent base prompt from disk."""
    p = path or _DEFAULT_BASE_PROMPT_PATH
    if p.exists():
        return p.read_text(encoding="utf-8")
    logger.warning("Base prompt not found at %s — using empty string.", p)
    return ""


def load_notion_prompt(path: Path | None = None) -> str:
    """Read the Notion sub-agent prompt from disk."""
    p = path or _DEFAULT_NOTION_PROMPT_PATH
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""

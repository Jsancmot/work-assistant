"""
Skill Registry.

Loads Markdown skill files from src/prompts/tools/ and makes them available
to the ContextBuilder. Inspired by Nanobot's skills loader pattern.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_SKILLS_DIR = Path(__file__).parent.parent / "prompts" / "tools"


class SkillRegistry:
    """Loads and caches skill Markdown files from a directory.

    Each .md file in the skills directory represents one skill whose name is
    the file stem (e.g. ``google_calendar.md`` → ``"google_calendar"``).
    """

    def __init__(self, skills_dir: Path | None = None) -> None:
        self._dir = skills_dir or _DEFAULT_SKILLS_DIR
        self._cache: dict[str, str] = {}

    def load_all(self) -> dict[str, str]:
        """Return all skills keyed by stem name, loading from disk on first call."""
        if not self._cache and self._dir.exists():
            for f in sorted(self._dir.glob("*.md")):
                self._cache[f.stem] = f.read_text(encoding="utf-8")
            logger.debug("Loaded %d skills from %s", len(self._cache), self._dir)
        return self._cache

    def load(self, name: str) -> str | None:
        """Return a single skill by name, or None if it doesn't exist."""
        return self.load_all().get(name)

    def list_skills(self) -> list[str]:
        """Return the names of all available skills."""
        return list(self.load_all().keys())

    def reload(self) -> None:
        """Invalidate the cache so skills are reloaded from disk on next access."""
        self._cache.clear()

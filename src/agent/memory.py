"""
Memory Store.

Persists per-user long-term memory as a Markdown file, following the same
lightweight file-based approach used by Nanobot (MEMORY.md, USER.md).
Each user has their own file under the data directory.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path("/app/data/memory")


class MemoryStore:
    """Simple file-backed memory for a single user.

    Args:
        user_id: Identifies the user (Telegram user ID as string works well).
        data_dir: Directory where memory files are stored.
            Defaults to ``/app/data/memory`` (Docker-friendly path).
    """

    def __init__(self, user_id: str, data_dir: Path | None = None) -> None:
        self._user_id = user_id
        self._dir = data_dir or _DEFAULT_DATA_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / f"{user_id}.md"

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def load(self) -> str:
        """Return the full memory content, or an empty string if none exists yet."""
        if self._file.exists():
            return self._file.read_text(encoding="utf-8")
        return ""

    def save(self, content: str) -> None:
        """Overwrite the memory file with *content*."""
        self._file.write_text(content.strip(), encoding="utf-8")
        logger.debug("[%s] Memory saved (%d chars)", self._user_id, len(content))

    def append(self, fact: str) -> None:
        """Append a timestamped fact to the memory file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        existing = self.load()
        updated = (existing + f"\n- [{timestamp}] {fact}").strip()
        self.save(updated)
        logger.debug("[%s] Memory appended: %s", self._user_id, fact)

    def clear(self) -> None:
        """Delete the memory file for this user."""
        if self._file.exists():
            self._file.unlink()
            logger.info("[%s] Memory cleared", self._user_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def exists(self) -> bool:
        return self._file.exists()

    @property
    def path(self) -> Path:
        return self._file

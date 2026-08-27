"""REPL session — convenience wrapper around SessionManager for interactive chat."""

from typing import Any
from typing import Optional

from ..session.session_manager import SessionManager


class ReplSession:
    """High-level session API for the interactive REPL."""

    def __init__(self, db_path: str | None = None) -> None:
        path = db_path or "~/.jebat/sessions.db"
        self._sm = SessionManager(path)
        self.session_id: str = ""
        self.name: str = ""

    def create_or_load(self, name: str | None = None) -> str:
        """Start a new session with the given name (defaults to auto)."""
        import datetime

        title = name or f"repl-{datetime.datetime.now():%Y%m%d-%H%M%S}"
        self.session_id = self._sm.create_session(title=title)
        self.name = title
        return self.session_id

    def add_message(
        self,
        role: str,
        content: str,
        tool_calls: Optional[str] = None,
        tokens: int = 0,
    ) -> None:
        if not self.session_id:
            raise RuntimeError("No active session — call create_or_load first")
        self._sm.add_message(self.session_id, role, content, tool_calls, tokens)

    def load_history(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.session_id:
            return []
        return self._sm.load_history(self.session_id, limit=limit)
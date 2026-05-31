"""Session persistence manager.

Provides SQLite-backed session storage with FTS5 full-text search for
cross-session message recall.
"""

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from typing import Optional


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at REAL,
            updated_at REAL,
            metadata TEXT
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT REFERENCES sessions(id),
            role TEXT,
            content TEXT,
            tool_calls TEXT,
            tokens INTEGER,
            created_at REAL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
            USING fts5(session_id, role, content);
    """)


class SessionManager:
    def __init__(self, db_path: str = "~/.jebat/sessions.db") -> None:
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        _init_schema(self.conn)

    def create_session(
        self, title: str | None = None, metadata: dict[str, Any] | None = None
    ) -> str:
        sess_id = str(uuid.uuid4())
        now = time.time()
        self.conn.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?)",
            (sess_id, title, now, now, str(metadata) if metadata else None),
        )
        self.conn.commit()
        return sess_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[str] = None,
        tokens: int = 0,
    ) -> None:
        now = time.time()
        self.conn.execute(
            """INSERT INTO messages
               (session_id, role, content, tool_calls, tokens, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                role,
                content,
                json.dumps(tool_calls) if tool_calls else None,
                tokens,
                now,
            ),
        )
        # FTS5 trigger not used — insert manually
        self.conn.execute(
            "INSERT INTO messages_fts (rowid, session_id, role, content) VALUES (last_insert_rowid(), ?, ?, ?)",
            (session_id, role, content),
        )
        self.conn.commit()

    def load_history(
        self, session_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        cur = self.conn.execute(
            """SELECT role, content, tool_calls, tokens, created_at
               FROM messages
               WHERE session_id = ?
               ORDER BY id DESC
               LIMIT ?""",
            (session_id, limit),
        )
        rows = cur.fetchall()
        # reverse to chronological order
        rows = list(reversed(rows))
        return [
            {
                "role": r["role"],
                "content": r["content"],
                "tool_calls": r["tool_calls"],
                "tokens": r["tokens"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
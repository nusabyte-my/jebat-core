"""JEBAT Session Manager — SQLite-backed conversation persistence.

Stores sessions and messages with FTS5 full-text search for cross-session recall.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Session Message ──────────────────────────────────────────────────────

@dataclass
class Message:
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    tokens: int = 0
    created_at: float = 0.0


@dataclass
class Session:
    id: str
    title: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Session Manager ──────────────────────────────────────────────────────

class SessionManager:
    """Manages conversation sessions with SQLite persistence and FTS5 search."""

    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            db_path = Path.home() / ".jebat" / "sessions.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._init_schema()
        return self._conn

    def _init_schema(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT DEFAULT '[]',
                tokens INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                compressed INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, id);
            -- FTS5 virtual table for full-text search
            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
                USING fts5(session_id, role, content, tokenize='unicode61');
        """)

    def create_session(self, title: str = "", metadata: dict | None = None) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())[:8]
        now = time.time()
        self.conn.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?)",
            (session_id, title, now, now, json.dumps(metadata or {})),
        )
        self.conn.commit()
        return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: list[dict] | None = None,
        tokens: int = 0,
        compressed: bool = False,
    ) -> int:
        """Add a message to a session. Returns message ID."""
        now = time.time()
        cursor = self.conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_calls, tokens, created_at, compressed) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, role, content, json.dumps(tool_calls or []), tokens, now, 1 if compressed else 0),
        )
        msg_id = cursor.lastrowid
        # Update session timestamp
        self.conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )
        # Index in FTS5
        try:
            self.conn.execute(
                "INSERT INTO messages_fts (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )
        except sqlite3.IntegrityError:
            pass  # Duplicate row ID
        self.conn.commit()
        return msg_id

    def load_history(self, session_id: str, limit: int = 50) -> list[Message]:
        """Load recent messages from a session (newest first, returned oldest-first)."""
        rows = self.conn.execute(
            "SELECT role, content, tool_calls, tokens, created_at FROM messages "
            "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        messages = []
        for row in reversed(rows):
            messages.append(Message(
                role=row["role"],
                content=row["content"],
                tool_calls=json.loads(row["tool_calls"] or "[]"),
                tokens=row["tokens"],
                created_at=row["created_at"],
            ))
        return messages

    def get_session(self, session_id: str) -> Session | None:
        """Get session metadata."""
        row = self.conn.execute(
            "SELECT id, title, created_at, updated_at, metadata FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return Session(
            id=row["id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def list_sessions(self, limit: int = 20) -> list[Session]:
        """List recent sessions."""
        rows = self.conn.execute(
            "SELECT id, title, created_at, updated_at, metadata FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            Session(
                id=r["id"],
                title=r["title"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                metadata=json.loads(r["metadata"] or "{}"),
            )
            for r in rows
        ]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages. Returns True if deleted."""
        cursor = self.conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def search_messages(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search across all messages using FTS5.

        Returns list of {session_id, role, snippet, title} dicts.
        """
        if not query.strip():
            return []
        try:
            rows = self.conn.execute(
                """SELECT DISTINCT s.id, s.title, m.role,
                          snippet(messages_fts, 2, '**', '**', '...', 32) AS snippet
                   FROM messages_fts fts
                   JOIN sessions s ON fts.session_id = s.id
                   JOIN messages m ON m.session_id = fts.session_id
                   WHERE messages_fts MATCH ?
                   ORDER BY s.updated_at DESC
                   LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [
                {"session_id": r[0], "title": r[1], "role": r[2], "snippet": r[3]}
                for r in rows
            ]
        except sqlite3.OperationalError:
            # FTS5 syntax error (bad query)
            return []

    def update_title(self, session_id: str, title: str) -> None:
        self.conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (title, time.time(), session_id),
        )
        self.conn.commit()

    def message_count(self, session_id: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return row["cnt"] if row else 0

    def total_tokens(self, session_id: str) -> int:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(tokens), 0) as total FROM messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return row["total"] if row else 0

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
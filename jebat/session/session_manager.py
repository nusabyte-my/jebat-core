"""Session persistence manager.

Provides SQLite-backed session storage with FTS5 full-text search for
cross-session message recall.
"""

import json
import re
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

    def list_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent sessions, newest first."""
        cur = self.conn.execute(
            """SELECT s.id, s.title, s.created_at, s.updated_at,
                      COUNT(m.id) as msg_count
               FROM sessions s
               LEFT JOIN messages m ON m.session_id = s.id
               GROUP BY s.id
               ORDER BY s.updated_at DESC
               LIMIT ?""",
            (limit,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"] or "(untitled)",
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "msg_count": r["msg_count"],
            }
            for r in rows
        ]

    def search_messages(
        self, query: str, limit: int = 10, role_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """Full-text search across all sessions' messages using FTS5.

        Args:
            query: FTS5 search query (supports boolean expressions).
            limit: Maximum results to return.
            role_filter: Optional comma-separated roles to filter by.

        Returns:
            List of matching messages with session context.
        """
        sql = """SELECT m.id, m.session_id, s.title as session_title,
                        m.role, m.content, m.created_at,
                        snippet(messages_fts, 3, '<b>', '</b>', '...', 64) as snippet
                 FROM messages_fts
                 JOIN messages m ON messages_fts.rowid = m.id
                 JOIN sessions s ON m.session_id = s.id
                 WHERE messages_fts MATCH ?"""
        params: list[Any] = [query]

        if role_filter:
            roles = [r.strip() for r in role_filter.split(",")]
            placeholders = ", ".join(["?" for _ in roles])
            sql += f" AND m.role IN ({placeholders})"
            params.extend(roles)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        cur = self.conn.execute(sql, params)
        rows = cur.fetchall()
        return [
            {
                "id": r["id"],
                "session_id": r["session_id"],
                "session_title": r["session_title"] or "(untitled)",
                "role": r["role"],
                "content": r["content"][:500],
                "created_at": r["created_at"],
                "snippet": re.sub(r'<[^>]+>', '', r["snippet"] or "").strip(),
            }
            for r in rows
        ]
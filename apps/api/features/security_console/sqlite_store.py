from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SecurityConsoleSQLiteStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS targets (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_findings_session ON findings(session_id);
                CREATE INDEX IF NOT EXISTS idx_runs_session ON runs(session_id);
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
                """
            )

    def load_all(self) -> dict[str, Any]:
        with self._connect() as conn:
            targets = self._load_table(conn, "targets")
            sessions = self._load_table(conn, "sessions")
            findings = self._load_grouped_table(conn, "findings")
            runs = self._load_grouped_table(conn, "runs")
            messages = self._load_grouped_table(conn, "messages")
        return {
            "targets": targets,
            "sessions": sessions,
            "findings": findings,
            "runs": runs,
            "messages": messages,
        }

    def replace_all(self, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM targets")
            conn.execute("DELETE FROM sessions")
            conn.execute("DELETE FROM findings")
            conn.execute("DELETE FROM runs")
            conn.execute("DELETE FROM messages")
            self._insert_table(conn, "targets", payload.get("targets", []))
            self._insert_table(conn, "sessions", payload.get("sessions", []))
            self._insert_grouped_table(conn, "findings", payload.get("findings", {}))
            self._insert_grouped_table(conn, "runs", payload.get("runs", {}))
            self._insert_grouped_table(conn, "messages", payload.get("messages", {}))

    def upsert_target(self, row: dict[str, Any]) -> None:
        self._upsert_row("targets", row["id"], row)

    def upsert_session(self, row: dict[str, Any]) -> None:
        self._upsert_row("sessions", row["id"], row)

    def upsert_finding(self, session_id: str, row: dict[str, Any]) -> None:
        self._upsert_grouped_row("findings", row["id"], session_id, row)

    def upsert_run(self, session_id: str, row: dict[str, Any]) -> None:
        self._upsert_grouped_row("runs", row["id"], session_id, row)

    def upsert_message(self, session_id: str, row: dict[str, Any]) -> None:
        self._upsert_grouped_row("messages", row["id"], session_id, row)

    def is_empty(self) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM sessions").fetchone()
            return not row or int(row["count"]) == 0

    def _load_table(self, conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
        rows = conn.execute(f"SELECT payload FROM {table}").fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def _load_grouped_table(self, conn: sqlite3.Connection, table: str) -> dict[str, list[dict[str, Any]]]:
        rows = conn.execute(f"SELECT session_id, payload FROM {table} ORDER BY rowid ASC").fetchall()
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(row["session_id"], []).append(json.loads(row["payload"]))
        return grouped

    def _insert_table(self, conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> None:
        conn.executemany(
            f"INSERT INTO {table} (id, payload) VALUES (?, ?)",
            [(row["id"], json.dumps(row)) for row in rows],
        )

    def _insert_grouped_table(
        self,
        conn: sqlite3.Connection,
        table: str,
        grouped: dict[str, list[dict[str, Any]]],
    ) -> None:
        conn.executemany(
            f"INSERT INTO {table} (id, session_id, payload) VALUES (?, ?, ?)",
            [
                (row["id"], session_id, json.dumps(row))
                for session_id, rows in grouped.items()
                for row in rows
            ],
        )

    def _upsert_row(self, table: str, row_id: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {table} (id, payload) VALUES (?, ?)",
                (row_id, json.dumps(payload)),
            )

    def _upsert_grouped_row(
        self,
        table: str,
        row_id: str,
        session_id: str,
        payload: dict[str, Any],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {table} (id, session_id, payload) VALUES (?, ?, ?)",
                (row_id, session_id, json.dumps(payload)),
            )

"""Database repository layer with real PostgreSQL queries via asyncpg.

Each repository wraps a single table and exposes typed CRUD helpers.
All queries go through DatabaseManager (asyncpg pool).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class BaseRepository:
    """Generic repository providing CRUD operations against PostgreSQL."""

    def __init__(self, table: str, db: Any = None):
        self.table = table
        self._db = db  # DatabaseManager — lazily resolved

    @property
    def db(self) -> Any:
        """Resolve the DatabaseManager lazily to avoid circular imports."""
        if self._db is None:
            from jebat.database.connection_manager import get_db_manager
            self._db = get_db_manager()
        return self._db

    # -- CRUD helpers ------------------------------------------------------

    async def create(self, **kwargs: Any) -> dict[str, Any]:
        """Insert a row and return the inserted record."""
        columns = list(kwargs.keys())
        values = [kwargs[c] for c in columns]
        # Convert dicts/lists to JSON strings for JSONB columns
        for i, v in enumerate(values):
            if isinstance(v, (dict, list)):
                values[i] = json.dumps(v)
            elif isinstance(v, UUID):
                values[i] = str(v)

        placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
        cols = ", ".join(columns)
        query = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders}) RETURNING *"
        row = await self.db.fetchrow(query, *values)
        return row or {}

    async def get_by_id(self, id: UUID) -> Optional[dict[str, Any]]:
        """Fetch a single row by primary key (assumes column ``id``)."""
        return await self.db.fetchrow(
            f"SELECT * FROM {self.table} WHERE id = $1", str(id)
        )

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch rows with pagination."""
        return await self.db.fetch(
            f"SELECT * FROM {self.table} ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit,
            offset,
        )

    async def update(self, id: UUID, **kwargs: Any) -> Optional[dict[str, Any]]:
        """Update a row by id and return the updated record."""
        if not kwargs:
            return await self.get_by_id(id)
        set_parts: list[str] = []
        values: list[Any] = []
        for i, (k, v) in enumerate(kwargs.items(), start=1):
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            elif isinstance(v, UUID):
                v = str(v)
            set_parts.append(f"{k} = ${i}")
            values.append(v)
        values.append(str(id))
        query = (
            f"UPDATE {self.table} SET {', '.join(set_parts)}, updated_at = NOW() "
            f"WHERE id = ${len(values)} RETURNING *"
        )
        return await self.db.fetchrow(query, *values)

    async def delete(self, id: UUID) -> bool:
        """Delete a row by id. Returns True if a row was deleted."""
        status = await self.db.execute(
            f"DELETE FROM {self.table} WHERE id = $1", str(id)
        )
        return "DELETE 1" in status

    async def count(self) -> int:
        """Return total row count."""
        result = await self.db.fetchval(f"SELECT COUNT(*) FROM {self.table}")
        return result or 0

    async def exists(self, id: UUID) -> bool:
        """Check if a row exists by id."""
        result = await self.db.fetchval(
            f"SELECT EXISTS(SELECT 1 FROM {self.table} WHERE id = $1)", str(id)
        )
        return bool(result)


# ---------------------------------------------------------------------------
# Concrete repositories
# ---------------------------------------------------------------------------

class UserRepository(BaseRepository):
    def __init__(self, db: Any = None):
        super().__init__("users", db)

    async def get_by_username(self, username: str) -> Optional[dict[str, Any]]:
        return await self.db.fetchrow(
            "SELECT * FROM users WHERE username = $1", username
        )

    async def get_by_email(self, email: str) -> Optional[dict[str, Any]]:
        return await self.db.fetchrow(
            "SELECT * FROM users WHERE email = $1", email
        )

    async def get_active_users(self) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM users WHERE is_active = true ORDER BY created_at DESC"
        )

    async def get_admin_users(self) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM users WHERE is_admin = true AND is_active = true"
        )


class AgentRepository(BaseRepository):
    def __init__(self, db: Any = None):
        super().__init__("agents", db)

    async def get_by_state(self, state: str) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM agents WHERE state = $1 AND is_active = true", state
        )

    async def get_by_type(self, agent_type: str) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM agents WHERE type = $1 AND is_active = true", agent_type
        )


class TaskRepository(BaseRepository):
    def __init__(self, db: Any = None):
        super().__init__("tasks", db)

    async def get_by_user(self, user_id: UUID) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM tasks WHERE user_id = $1 ORDER BY created_at DESC",
            str(user_id),
        )

    async def get_by_agent(self, agent_id: UUID) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM tasks WHERE agent_id = $1 ORDER BY created_at DESC",
            str(agent_id),
        )

    async def get_by_status(self, status: str) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM tasks WHERE status = $1 ORDER BY created_at DESC", status
        )

    async def get_pending_tasks(self) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM tasks WHERE status = 'PENDING' ORDER BY created_at ASC"
        )

    async def update_status(self, task_id: UUID, status: str) -> None:
        await self.db.execute(
            "UPDATE tasks SET status = $1, updated_at = NOW() WHERE id = $2",
            status,
            str(task_id),
        )

    async def complete_task(self, task_id: UUID, output: Any = None) -> None:
        output_json = json.dumps(output) if output else None
        await self.db.execute(
            "UPDATE tasks SET status = 'COMPLETED', output_data = $1, "
            "completed_at = NOW(), updated_at = NOW() WHERE id = $2",
            output_json,
            str(task_id),
        )


# ---------------------------------------------------------------------------
# Memory repositories (M0–M4)
# ---------------------------------------------------------------------------

class MemoryM0Repository(BaseRepository):
    def __init__(self, db: Any = None):
        super().__init__("memory_m0", db)

    async def get_by_user(self, user_id: UUID, limit: int = 100) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM memory_m0 WHERE user_id = $1 "
            "AND expires_at > NOW() ORDER BY heat_score DESC LIMIT $2",
            str(user_id),
            limit,
        )

    async def get_by_session(self, session_id: UUID, limit: int = 100) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM memory_m0 WHERE session_id = $1 "
            "AND expires_at > NOW() ORDER BY heat_score DESC LIMIT $2",
            str(session_id),
            limit,
        )

    async def get_expired(self) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM memory_m0 WHERE expires_at <= NOW()"
        )

    async def cleanup_expired(self) -> int:
        """Delete expired entries and return count."""
        status = await self.db.execute("DELETE FROM memory_m0 WHERE expires_at <= NOW()")
        return int(status.split()[-1]) if status else 0


class MemoryM1Repository(BaseRepository):
    def __init__(self, db: Any = None):
        super().__init__("memory_m1", db)

    async def get_by_session(self, session_id: UUID, limit: int = 100) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM memory_m1 WHERE session_id = $1 "
            "AND expires_at > NOW() ORDER BY heat_score DESC LIMIT $2",
            str(session_id),
            limit,
        )

    async def get_by_user(self, user_id: UUID, limit: int = 100) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM memory_m1 WHERE user_id = $1 "
            "AND expires_at > NOW() ORDER BY heat_score DESC LIMIT $2",
            str(user_id),
            limit,
        )


class MemoryM2Repository(BaseRepository):
    def __init__(self, db: Any = None):
        super().__init__("memory_m2", db)

    async def get_by_user(self, user_id: UUID, limit: int = 100) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM memory_m2 WHERE user_id = $1 "
            "AND expires_at > NOW() ORDER BY heat_score DESC LIMIT $2",
            str(user_id),
            limit,
        )

    async def get_expired(self) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM memory_m2 WHERE expires_at <= NOW()"
        )


class MemoryM3Repository(BaseRepository):
    def __init__(self, db: Any = None):
        super().__init__("memory_m3", db)

    async def search_by_tags(self, tags: List[str]) -> list[dict[str, Any]]:
        """Find entries whose tags array overlaps with the given tags."""
        return await self.db.fetch(
            "SELECT * FROM memory_m3 WHERE tags && $1 ORDER BY heat_score DESC",
            tags,
        )

    async def get_by_user(self, user_id: UUID, limit: int = 100) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM memory_m3 WHERE user_id = $1 "
            "AND expires_at > NOW() ORDER BY heat_score DESC LIMIT $2",
            str(user_id),
            limit,
        )


class MemoryM4Repository(BaseRepository):
    def __init__(self, db: Any = None):
        super().__init__("memory_m4", db)

    async def search_by_content(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM memory_m4 WHERE content ILIKE '%' || $1 || '%' "
            "ORDER BY heat_score DESC LIMIT $2",
            query,
            limit,
        )

    async def get_by_user(self, user_id: UUID, limit: int = 100) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM memory_m4 WHERE user_id = $1 ORDER BY heat_score DESC LIMIT $2",
            str(user_id),
            limit,
        )


# ---------------------------------------------------------------------------
# Skill repositories
# ---------------------------------------------------------------------------

class SkillRepository(BaseRepository):
    def __init__(self, db: Any = None):
        super().__init__("skills", db)

    async def get_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return await self.db.fetchrow(
            "SELECT * FROM skills WHERE skill_name = $1", name
        )

    async def get_active_skills(self) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM skills WHERE is_active = true ORDER BY skill_name"
        )


class SkillExecutionRepository(BaseRepository):
    def __init__(self, db: Any = None):
        super().__init__("skill_executions", db)

    async def get_by_skill(self, skill_id: UUID, limit: int = 50) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM skill_executions WHERE skill_id = $1 "
            "ORDER BY created_at DESC LIMIT $2",
            str(skill_id),
            limit,
        )

    async def get_by_status(self, status: str, limit: int = 50) -> list[dict[str, Any]]:
        return await self.db.fetch(
            "SELECT * FROM skill_executions WHERE status = $1 "
            "ORDER BY created_at DESC LIMIT $2",
            status,
            limit,
        )

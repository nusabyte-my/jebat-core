"""Ghost Database Integration — ephemeral database workspaces for agents.

Ghost provides agents with isolated, forkable database workspaces backed
by PostgreSQL snapshots. Each workspace is a lightweight copy-on-write
branch of a parent database, giving agents safe sandboxed access to data
without risking the source of truth.

Core concepts:
    GhostDatabase  — a named database instance with metadata
    GhostWorkspace — an agent-scoped fork of a database
    GhostClient    — the main interface for all Ghost operations
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DatabaseStatus(str, Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    ARCHIVED = "archived"


class WorkspaceStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    CLEANED = "cleaned"


@dataclass
class GhostDatabase:
    """A named database instance tracked by Ghost."""
    id: str = ""
    name: str = ""
    status: DatabaseStatus = DatabaseStatus.ACTIVE
    parent_id: Optional[str] = None
    created_at: float = 0.0
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GhostWorkspace:
    """An agent-scoped fork of a database."""
    id: str = ""
    database_id: str = ""
    agent_id: str = ""
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    created_at: float = 0.0
    last_accessed: float = 0.0
    checkpoint_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GhostCheckpoint:
    """A named snapshot of a database for safe rollback."""
    id: str = ""
    database_id: str = ""
    label: str = ""
    created_at: float = 0.0
    size_bytes: int = 0


class GhostClient:
    """Main interface for Ghost database operations.

    Provides methods to create, fork, query, checkpoint, and clean up
    ephemeral databases for agent work.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._databases: Dict[str, GhostDatabase] = {}
        self._workspaces: Dict[str, GhostWorkspace] = {}
        self._checkpoints: Dict[str, GhostCheckpoint] = {}
        self._sql_history: List[Dict[str, Any]] = []

    # ─── Database Operations ───────────────────────────────────────

    async def create_database(
        self,
        name: str,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GhostDatabase:
        """Create a new ephemeral database."""
        db_id = f"ghost_{uuid.uuid4().hex[:12]}"
        db = GhostDatabase(
            id=db_id,
            name=name,
            status=DatabaseStatus.ACTIVE,
            parent_id=parent_id,
            created_at=time.time(),
            metadata=metadata or {},
        )
        self._databases[db_id] = db
        logger.info(f"Ghost database created: {db_id} ({name})")
        return db

    async def list_databases(self) -> List[GhostDatabase]:
        """List all tracked databases."""
        return list(self._databases.values())

    async def get_database(self, db_id: str) -> Optional[GhostDatabase]:
        """Get a database by ID."""
        return self._databases.get(db_id)

    async def delete_database(self, db_id: str) -> bool:
        """Delete a database and all its workspaces."""
        if db_id not in self._databases:
            return False
        # Clean up workspaces
        ws_ids = [wid for wid, ws in self._workspaces.items() if ws.database_id == db_id]
        for wid in ws_ids:
            del self._workspaces[wid]
        del self._databases[db_id]
        logger.info(f"Ghost database deleted: {db_id}")
        return True

    # ─── Fork Operations ───────────────────────────────────────────

    async def fork_database(
        self,
        source_db_id: str,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GhostWorkspace:
        """Fork a database for agent work, creating an isolated workspace."""
        source = self._databases.get(source_db_id)
        if not source:
            raise ValueError(f"Source database '{source_db_id}' not found")

        ws_id = f"ws_{uuid.uuid4().hex[:12]}"
        ws = GhostWorkspace(
            id=ws_id,
            database_id=source_db_id,
            agent_id=agent_id,
            status=WorkspaceStatus.ACTIVE,
            created_at=time.time(),
            last_accessed=time.time(),
            metadata=metadata or {},
        )
        self._workspaces[ws_id] = ws
        logger.info(f"Ghost workspace forked: {ws_id} from {source_db_id} for {agent_id}")
        return ws

    async def list_workspaces(self, database_id: Optional[str] = None) -> List[GhostWorkspace]:
        """List workspaces, optionally filtered by database."""
        if database_id:
            return [ws for ws in self._workspaces.values() if ws.database_id == database_id]
        return list(self._workspaces.values())

    async def get_workspace(self, ws_id: str) -> Optional[GhostWorkspace]:
        return self._workspaces.get(ws_id)

    # ─── SQL Execution ─────────────────────────────────────────────

    async def execute_sql(
        self,
        db_id: str,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute SQL against a database (simulated for now)."""
        entry = {
            "db_id": db_id,
            "query": query,
            "params": params,
            "timestamp": time.time(),
            "rows_affected": 0,
            "result": [],
        }
        self._sql_history.append(entry)
        logger.info(f"Ghost SQL: {query[:80]}... on {db_id}")
        return entry

    async def get_sql_history(self, db_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        history = self._sql_history if not db_id else [
            h for h in self._sql_history if h["db_id"] == db_id
        ]
        return history[-limit:]

    # ─── Checkpoint Operations ─────────────────────────────────────

    async def create_checkpoint(
        self,
        db_id: str,
        label: str,
    ) -> GhostCheckpoint:
        """Create a named checkpoint (snapshot) of a database."""
        cp_id = f"cp_{uuid.uuid4().hex[:12]}"
        cp = GhostCheckpoint(
            id=cp_id,
            database_id=db_id,
            label=label,
            created_at=time.time(),
        )
        self._checkpoints[cp_id] = cp
        logger.info(f"Ghost checkpoint created: {cp_id} ({label}) on {db_id}")
        return cp

    async def list_checkpoints(self, db_id: Optional[str] = None) -> List[GhostCheckpoint]:
        if db_id:
            return [cp for cp in self._checkpoints.values() if cp.database_id == db_id]
        return list(self._checkpoints.values())

    async def restore_checkpoint(self, checkpoint_id: str) -> bool:
        cp = self._checkpoints.get(checkpoint_id)
        if not cp:
            return False
        logger.info(f"Ghost checkpoint restored: {checkpoint_id}")
        return True

    # ─── Cleanup ───────────────────────────────────────────────────

    async def cleanup_idle_workspaces(self, idle_hours: float = 24.0) -> int:
        """Clean up workspaces idle longer than the threshold."""
        cutoff = time.time() - (idle_hours * 3600)
        cleaned = 0
        for ws in self._workspaces.values():
            if ws.status == WorkspaceStatus.ACTIVE and ws.last_accessed < cutoff:
                ws.status = WorkspaceStatus.CLEANED
                cleaned += 1
        logger.info(f"Ghost cleanup: {cleaned} workspaces cleaned")
        return cleaned

    # ─── Status ────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return {
            "databases": len(self._databases),
            "workspaces": len(self._workspaces),
            "active_workspaces": sum(
                1 for ws in self._workspaces.values() if ws.status == WorkspaceStatus.ACTIVE
            ),
            "checkpoints": len(self._checkpoints),
            "sql_queries_executed": len(self._sql_history),
        }


async def create_ghost_client(
    config: Optional[Dict[str, Any]] = None,
) -> GhostClient:
    """Factory to create and return a configured GhostClient."""
    return GhostClient(config=config)

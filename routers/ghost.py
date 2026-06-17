"""Ghost Database API router — REST endpoints for ephemeral database operations.

Endpoints:
    GET  /api/ghost/status        — Ghost system status
    GET  /api/ghost/databases     — List all databases
    POST /api/ghost/databases     — Create a new database
    GET  /api/ghost/databases/{id}— Get database by ID
    DELETE /api/ghost/databases/{id} — Delete a database
    POST /api/ghost/fork          — Fork a database for agent work
    GET  /api/ghost/workspaces    — List workspaces (optional ?database_id=)
    GET  /api/ghost/workspaces/{id} — Get workspace by ID
    POST /api/ghost/sql           — Execute SQL against a database
    GET  /api/ghost/sql/history   — Get SQL execution history
    POST /api/ghost/checkpoint    — Create a checkpoint
    GET  /api/ghost/checkpoints   — List checkpoints
    POST /api/ghost/checkpoint/restore — Restore a checkpoint
    POST /api/ghost/cleanup       — Clean up idle workspaces
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jebat.features.ghost.ghost_integration import GhostClient, create_ghost_client

router = APIRouter(prefix="/api/ghost", tags=["ghost"])

# Singleton client — initialized lazily
_client: Optional[GhostClient] = None


async def _get_client() -> GhostClient:
    global _client
    if _client is None:
        _client = await create_ghost_client()
    return _client


# ─── Request / Response models ──────────────────────────────────────

class CreateDatabaseRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Database name")
    parent_id: Optional[str] = Field(default=None, description="Parent database ID to clone from")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional metadata")


class ForkRequest(BaseModel):
    source_db_id: str = Field(..., description="Source database ID to fork")
    agent_id: str = Field(..., description="Agent ID for the workspace")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecuteSqlRequest(BaseModel):
    db_id: str = Field(..., description="Database ID to query")
    query: str = Field(..., min_length=1, description="SQL query to execute")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters")


class CheckpointRequest(BaseModel):
    db_id: str = Field(..., description="Database ID")
    label: str = Field(..., min_length=1, description="Checkpoint label")


class CleanupRequest(BaseModel):
    idle_hours: float = Field(default=24.0, ge=0.5, le=720, description="Idle threshold in hours")


# ─── Endpoints ──────────────────────────────────────────────────────

@router.get("/status", summary="Ghost system status")
async def ghost_status() -> Dict[str, Any]:
    """Get Ghost system status.

    Returns the current state of the Ghost subsystem including database count,
    workspace count, and overall health.
    """
    client = await _get_client()
    return client.get_status()


@router.get("/databases", summary="List all databases")
async def list_databases() -> Dict[str, Any]:
    """List all Ghost databases.

    Returns every ephemeral database managed by Ghost, including their
    status, size, and metadata.
    """
    client = await _get_client()
    dbs = await client.list_databases()
    return {"databases": [_db_to_dict(d) for d in dbs], "total": len(dbs)}


@router.post("/databases", summary="Create a new database")
async def create_database(req: CreateDatabaseRequest) -> Dict[str, Any]:
    """Create a new ephemeral database.

    Provision a fresh isolated database. Optionally clone from an existing
    parent database by providing `parent_id`.
    """
    client = await _get_client()
    db = await client.create_database(name=req.name, parent_id=req.parent_id, metadata=req.metadata)
    return _db_to_dict(db)


@router.get("/databases/{db_id}", summary="Get database by ID")
async def get_database(db_id: str) -> Dict[str, Any]:
    """Get a database by ID.

    Retrieve full details for a single database including status, size,
    parent reference, and metadata.
    """
    client = await _get_client()
    db = await client.get_database(db_id)
    if not db:
        raise HTTPException(status_code=404, detail=f"Database '{db_id}' not found")
    return _db_to_dict(db)


@router.delete("/databases/{db_id}", summary="Delete a database")
async def delete_database(db_id: str) -> Dict[str, Any]:
    """Delete a database and all its workspaces.

    Permanently removes the database and every workspace forked from it.
    Checkpoints associated with this database are also removed.
    """
    client = await _get_client()
    deleted = await client.delete_database(db_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Database '{db_id}' not found")
    return {"deleted": True, "database_id": db_id}


@router.post("/fork", summary="Fork database for agent work")
async def fork_database(req: ForkRequest) -> Dict[str, Any]:
    """Fork a database for isolated agent work.

    Create a workspace copy of the source database scoped to a specific agent.
    The workspace starts as a snapshot of the source at fork time, giving the
    agent its own private data sandbox.
    """
    client = await _get_client()
    try:
        ws = await client.fork_database(source_db_id=req.source_db_id, agent_id=req.agent_id, metadata=req.metadata)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _ws_to_dict(ws)


@router.get("/workspaces", summary="List workspaces")
async def list_workspaces(database_id: Optional[str] = None) -> Dict[str, Any]:
    """List workspaces, optionally filtered by database ID.

    Returns all active agent workspaces. Pass `?database_id=` to narrow
    results to forks of a specific database.
    """
    client = await _get_client()
    workspaces = await client.list_workspaces(database_id=database_id)
    return {"workspaces": [_ws_to_dict(w) for w in workspaces], "total": len(workspaces)}


@router.get("/workspaces/{ws_id}", summary="Get workspace by ID")
async def get_workspace(ws_id: str) -> Dict[str, Any]:
    """Get a workspace by ID.

    Retrieve details for a specific agent workspace including its parent
    database, agent ID, status, and last-accessed timestamp.
    """
    client = await _get_client()
    ws = await client.get_workspace(ws_id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{ws_id}' not found")
    return _ws_to_dict(ws)


@router.post("/sql", summary="Execute SQL query")
async def execute_sql(req: ExecuteSqlRequest) -> Dict[str, Any]:
    """Execute SQL against a Ghost database.

    Run an arbitrary SQL statement against a database. The database must
    exist or a 404 is returned. Query results and metadata are recorded
    in the SQL history.
    """
    client = await _get_client()
    db = await client.get_database(req.db_id)
    if not db:
        raise HTTPException(status_code=404, detail=f"Database '{req.db_id}' not found")
    result = await client.execute_sql(db_id=req.db_id, query=req.query, params=req.params)
    return result


@router.get("/sql/history", summary="SQL execution history")
async def sql_history(db_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Get SQL execution history.

    Returns recent SQL queries executed against Ghost databases, ordered by
    most recent first. Optionally filter by `?database_id=`.
    """
    client = await _get_client()
    history = await client.get_sql_history(db_id=db_id, limit=limit)
    return {"history": history, "total": len(history)}


@router.post("/checkpoint", summary="Create a checkpoint")
async def create_checkpoint(req: CheckpointRequest) -> Dict[str, Any]:
    """Create a named checkpoint (snapshot) of a database.

    Take a point-in-time snapshot of the database state. Checkpoints can
    later be restored to revert the database to this exact state.
    """
    client = await _get_client()
    cp = await client.create_checkpoint(db_id=req.db_id, label=req.label)
    return _cp_to_dict(cp)


@router.get("/checkpoints", summary="List checkpoints")
async def list_checkpoints(db_id: Optional[str] = None) -> Dict[str, Any]:
    """List checkpoints.

    Returns all checkpoints across databases, or filtered to a single
    database via `?database_id=`.
    """
    client = await _get_client()
    checkpoints = await client.list_checkpoints(db_id=db_id)
    return {"checkpoints": [_cp_to_dict(c) for c in checkpoints], "total": len(checkpoints)}


@router.post("/checkpoints/{checkpoint_id}/restore", summary="Restore from checkpoint")
async def restore_checkpoint(checkpoint_id: str) -> Dict[str, Any]:
    """Restore a database from a checkpoint.

    Reverts the database to the state captured in the specified checkpoint.
    All data written after the checkpoint was created is discarded.
    """
    client = await _get_client()
    restored = await client.restore_checkpoint(checkpoint_id=checkpoint_id)
    if not restored:
        raise HTTPException(status_code=404, detail=f"Checkpoint '{checkpoint_id}' not found")
    return {"restored": True, "checkpoint_id": checkpoint_id}


@router.post("/cleanup", summary="Clean up idle workspaces")
async def cleanup_idle_workspaces(req: CleanupRequest) -> Dict[str, Any]:
    """Clean up workspaces idle longer than the threshold.

    Reclaims resources by removing workspaces that haven't been accessed
    within the specified idle window (default: 24 hours).
    """
    client = await _get_client()
    cleaned = await client.cleanup_idle_workspaces(idle_hours=req.idle_hours)
    return {"cleaned": cleaned, "idle_hours": req.idle_hours}


# ─── Serialization helpers ──────────────────────────────────────────

def _db_to_dict(db) -> Dict[str, Any]:
    return {
        "id": db.id,
        "name": db.name,
        "status": db.status.value,
        "parent_id": db.parent_id,
        "created_at": db.created_at,
        "size_bytes": db.size_bytes,
        "metadata": db.metadata,
    }


def _ws_to_dict(ws) -> Dict[str, Any]:
    return {
        "id": ws.id,
        "database_id": ws.database_id,
        "agent_id": ws.agent_id,
        "status": ws.status.value,
        "created_at": ws.created_at,
        "last_accessed": ws.last_accessed,
        "checkpoint_id": ws.checkpoint_id,
        "metadata": ws.metadata,
    }


def _cp_to_dict(cp) -> Dict[str, Any]:
    return {
        "id": cp.id,
        "database_id": cp.database_id,
        "label": cp.label,
        "created_at": cp.created_at,
        "size_bytes": cp.size_bytes,
    }

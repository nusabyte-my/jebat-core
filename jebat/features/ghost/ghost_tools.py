"""
JEBAT Ghost Tools — Registered tools for Ghost database operations.

These tools are registered with JEBAT's tool registry and available to
agents via the standard tool calling mechanism. They wrap the Ghost CLI
for database operations optimized for agent workflows.

All tools require Ghost CLI installed and authenticated.
"""

from __future__ import annotations

from typing import Any

from jebat.tools import register_tool

from jebat.features.ghost.ghost_integration import (
    GhostClient,
    get_ghost_client,
    GhostDatabase,
    GhostQueryResult,
)


def _ensure_ghost_available() -> GhostClient:
    """Ensure Ghost CLI is available and return client."""
    try:
        return get_ghost_client()
    except RuntimeError as e:
        raise RuntimeError(
            f"Ghost CLI not available: {e}. "
            "Install with: curl -fsSL https://install.ghost.build | sh"
        )


# ── Database Lifecycle ──────────────────────────────────────────────────

@register_tool(
    "ghost_create_db",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Database name (lowercase, alphanumeric, hyphens)",
            },
            "dedicated": {
                "type": "boolean",
                "description": "Create as dedicated (persistent) database",
                "default": False,
            },
        },
        "required": ["name"],
    },
    safety_tier="confirm",
    timeout=60,
    description="Create a new ephemeral Ghost Postgres database for agent work",
)
async def ghost_create_db_tool(name: str, dedicated: bool = False) -> dict[str, Any]:
    """Create a new ephemeral Ghost Postgres database for agent work.
    
    Ephemeral databases are automatically paused when idle and can be
    forked for isolated agent work. Use dedicated=True for persistent DBs.
    """
    client = _ensure_ghost_available()
    db = await client.create_db(name, dedicated)
    return db.to_dict()


@register_tool(
    "ghost_fork_db",
    schema={
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "description": "Source database name to fork from",
            },
            "name": {
                "type": "string",
                "description": "Name for the new forked database",
            },
            "dedicated": {
                "type": "boolean",
                "description": "Create fork as dedicated (persistent) database",
                "default": False,
            },
        },
        "required": ["source", "name"],
    },
    safety_tier="confirm",
    timeout=60,
    description="Fork an existing Ghost database for isolated agent work",
)
async def ghost_fork_db_tool(source: str, name: str, dedicated: bool = False) -> dict[str, Any]:
    """Fork an existing Ghost database for isolated agent work.
    
    Forking creates an instant copy with copy-on-write semantics.
    Perfect for creating checkpoints or isolated agent workspaces.
    """
    client = _ensure_ghost_available()
    db = await client.fork_db(source, name, dedicated)
    return db.to_dict()


@register_tool(
    "ghost_delete_db",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Database name to delete",
            },
            "force": {
                "type": "boolean",
                "description": "Force delete without confirmation",
                "default": True,
            },
        },
        "required": ["name"],
    },
    safety_tier="dangerous",
    timeout=30,
    description="Delete a Ghost database permanently",
)
async def ghost_delete_db_tool(name: str, force: bool = True) -> dict[str, Any]:
    """Delete a Ghost database permanently. Use with caution!"""
    client = _ensure_ghost_available()
    success = await client.delete_db(name, force)
    return {"success": success, "name": name, "action": "deleted"}


@register_tool(
    "ghost_list_dbs",
    schema={
        "type": "object",
        "properties": {},
    },
    safety_tier="auto",
    timeout=15,
    description="List all Ghost databases with status",
)
async def ghost_list_dbs_tool() -> dict[str, Any]:
    """List all Ghost databases with their status."""
    client = _ensure_ghost_available()
    dbs = await client.list_databases()
    return {
        "databases": [db.to_dict() for db in dbs],
        "count": len(dbs),
    }


# ── SQL Execution ──────────────────────────────────────────────────────

@register_tool(
    "ghost_sql",
    schema={
        "type": "object",
        "properties": {
            "database": {
                "type": "string",
                "description": "Database name to query",
            },
            "query": {
                "type": "string",
                "description": "SQL query to execute",
            },
        },
        "required": ["database", "query"],
    },
    safety_tier="confirm",
    timeout=60,
    description="Execute a SQL query on a Ghost database",
)
async def ghost_sql_tool(database: str, query: str) -> dict[str, Any]:
    """Execute a SQL query on a Ghost database.
    
    For read queries (SELECT), use safety_tier=confirm.
    For write queries (INSERT, UPDATE, DELETE, DDL), use safety_tier=dangerous.
    """
    client = _ensure_ghost_available()
    result = await client.execute_sql(database, query)
    if result.error:
        return {"error": result.error}
    return {
        "rows": result.rows,
        "columns": result.columns,
        "row_count": result.row_count,
        "execution_time_ms": result.execution_time_ms,
    }


@register_tool(
    "ghost_connect",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Database name",
            },
        },
        "required": ["name"],
    },
    safety_tier="auto",
    timeout=15,
    description="Get connection string for a Ghost database",
)
async def ghost_connect_tool(name: str) -> dict[str, Any]:
    """Get connection string for a Ghost database (for external tools like psql)."""
    client = _ensure_ghost_available()
    conn_str = await client.get_connection_string(name)
    return {"connection_string": conn_str, "database": name}


# ── State Management ───────────────────────────────────────────────────

@register_tool(
    "ghost_pause_db",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Database name to pause",
            },
        },
        "required": ["name"],
    },
    safety_tier="confirm",
    timeout=15,
    description="Pause a running Ghost database to save resources",
)
async def ghost_pause_db_tool(name: str) -> dict[str, Any]:
    """Pause a running Ghost database to save resources."""
    client = _ensure_ghost_available()
    success = await client.pause_db(name)
    return {"success": success, "name": name, "action": "paused"}


@register_tool(
    "ghost_resume_db",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Database name to resume",
            },
        },
        "required": ["name"],
    },
    safety_tier="confirm",
    timeout=30,
    description="Resume a paused Ghost database",
)
async def ghost_resume_db_tool(name: str) -> dict[str, Any]:
    """Resume a paused Ghost database."""
    client = _ensure_ghost_available()
    success = await client.resume_db(name)
    return {"success": success, "name": name, "action": "resumed"}


@register_tool(
    "ghost_share_db",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Database name to share",
            },
            "expiry_hours": {
                "type": "integer",
                "description": "Share link expiry in hours",
                "default": 24,
            },
        },
        "required": ["name"],
    },
    safety_tier="confirm",
    timeout=15,
    description="Create a shareable link for a Ghost database",
)
async def ghost_share_db_tool(name: str, expiry_hours: int = 24) -> dict[str, Any]:
    """Create a shareable link for a Ghost database."""
    client = _ensure_ghost_available()
    share_url = await client.share_db(name, expiry_hours)
    return {"share_url": share_url, "database": name, "expires_in_hours": expiry_hours}


# ── Agent Workflow Helpers ─────────────────────────────────────────────

@register_tool(
    "ghost_agent_workspace",
    schema={
        "type": "object",
        "properties": {
            "agent_name": {
                "type": "string",
                "description": "Agent identifier (e.g., 'researcher', 'pentest', 'coder')",
            },
            "task_name": {
                "type": "string",
                "description": "Descriptive task name for the workspace",
            },
            "base_db": {
                "type": "string",
                "description": "Optional base database to fork from",
                "default": "",
            },
        },
        "required": ["agent_name", "task_name"],
    },
    safety_tier="confirm",
    timeout=60,
    description="Create isolated agent workspace with dedicated/forked database",
)
async def ghost_agent_workspace_tool(agent_name: str, task_name: str, base_db: str = "") -> dict[str, Any]:
    """Create an isolated agent workspace with a dedicated/forked database.
    
    This is the primary workflow for agents:
    1. Creates/forks a database named `agent-{agent_name}-{task_name}`
    2. Returns connection info and database object
    3. Agent can use `ghost_sql` for its work
    4. On completion, can checkpoint or cleanup
    """
    client = _ensure_ghost_available()
    
    # Sanitize names
    safe_agent = agent_name.lower().replace(" ", "-")[:20]
    safe_task = task_name.lower().replace(" ", "-")[:30]
    db_name = f"agent-{safe_agent}-{safe_task}"
    
    if base_db:
        # Fork from base for context continuity
        db = await client.fork_db(base_db, db_name, dedicated=False)
    else:
        # Create fresh ephemeral DB
        db = await client.create_db(db_name, dedicated=False)
    
    return {
        "database": db.to_dict(),
        "workspace_name": db_name,
        "agent_name": agent_name,
        "task_name": task_name,
        "connection_string": db.connection_string,
        "usage": f"Use ghost_sql with database='{db_name}' for queries",
    }


@register_tool(
    "ghost_checkpoint",
    schema={
        "type": "object",
        "properties": {
            "source_db": {
                "type": "string",
                "description": "Source database to checkpoint",
            },
            "checkpoint_name": {
                "type": "string",
                "description": "Name for the checkpoint (e.g., 'pre-refactor', 'research-done')",
            },
        },
        "required": ["source_db", "checkpoint_name"],
    },
    safety_tier="confirm",
    timeout=60,
    description="Create a checkpoint fork of agent database for rollback/recovery",
)
async def ghost_checkpoint_tool(source_db: str, checkpoint_name: str) -> dict[str, Any]:
    """Create a checkpoint fork for agent state recovery.
    
    Usage: Before risky operations, create checkpoint.
    On failure: fork from checkpoint to recover.
    """
    client = _ensure_ghost_available()
    
    cp_name = f"{source_db}-checkpoint-{checkpoint_name}"
    db = await client.fork_db(source_db, cp_name, dedicated=False)
    
    return {
        "checkpoint": db.to_dict(),
        "source_db": source_db,
        "checkpoint_name": checkpoint_name,
        "recovery": f"Use ghost_fork_db with source='{cp_name}' to recover",
    }


@register_tool(
    "ghost_cleanup_agent_workspaces",
    schema={
        "type": "object",
        "properties": {
            "agent_prefix": {
                "type": "string",
                "description": "Agent prefix to match (e.g., 'agent-researcher-')",
                "default": "agent-",
            },
            "older_than_hours": {
                "type": "integer",
                "description": "Delete workspaces older than this many hours",
                "default": 24,
            },
            "dry_run": {
                "type": "boolean",
                "description": "List what would be deleted without deleting",
                "default": True,
            },
        },
    },
    safety_tier="dangerous",
    timeout=60,
    description="Clean up old agent workspace databases",
)
async def ghost_cleanup_agent_workspaces_tool(
    agent_prefix: str = "agent-",
    older_than_hours: int = 24,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Clean up old agent workspace databases.
    
    Use dry_run=True first to see what would be deleted.
    """
    client = _ensure_ghost_available()
    dbs = await client.list_databases()
    
    import datetime
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=older_than_hours)
    
    to_delete = []
    for db in dbs:
        if db.name.startswith(agent_prefix):
            # Check creation time if available
            if db.created_at:
                try:
                    created = datetime.datetime.fromisoformat(db.created_at.replace('Z', '+00:00'))
                    if created < cutoff:
                        to_delete.append(db.name)
                except Exception:
                    pass
            else:
                to_delete.append(db.name)
    
    if not dry_run:
        deleted = []
        for name in to_delete:
            success = await client.delete_db(name, force=True)
            if success:
                deleted.append(name)
        return {"deleted": deleted, "count": len(deleted), "dry_run": False}
    else:
        return {"would_delete": to_delete, "count": len(to_delete), "dry_run": True}


__all__ = [
    # DB Lifecycle
    "ghost_create_db_tool",
    "ghost_fork_db_tool",
    "ghost_delete_db_tool",
    "ghost_list_dbs_tool",
    # SQL
    "ghost_sql_tool",
    "ghost_connect_tool",
    # State
    "ghost_pause_db_tool",
    "ghost_resume_db_tool",
    # Workflow
    "ghost_agent_workspace_tool",
    "ghost_checkpoint_tool",
    "ghost_cleanup_agent_workspaces_tool",
    "ghost_share_db_tool",
]
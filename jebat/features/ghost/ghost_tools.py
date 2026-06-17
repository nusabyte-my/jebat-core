"""Ghost JEBAT Tools — 14 registered tools for database operations.

These tools are registered with the JEBAT tool registry and can be
invoked by the agent orchestrator or directly via the API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from jebat.features.ghost.ghost_integration import GhostClient, create_ghost_client

logger = logging.getLogger(__name__)


@dataclass
class GhostTool:
    """A single Ghost tool definition."""
    name: str
    description: str
    category: str
    handler: Optional[Callable] = None
    parameters: Dict[str, str] = field(default_factory=dict)


class GhostToolRegistry:
    """Registry of 14 Ghost tools for JEBAT agent use."""

    def __init__(self):
        self._client: Optional[GhostClient] = None
        self._tools: Dict[str, GhostTool] = {}
        self._register_all()

    async def _ensure_client(self) -> GhostClient:
        if self._client is None:
            self._client = await create_ghost_client()
        return self._client

    def _register_all(self) -> None:
        """Register all 14 Ghost tools."""
        tools = [
            GhostTool(
                name="ghost.status",
                description="Check Ghost CLI availability and system status",
                category="system",
                parameters={},
            ),
            GhostTool(
                name="ghost.create",
                description="Create a new ephemeral database",
                category="database",
                parameters={"name": "Database name", "parent_id": "Optional parent DB to clone from"},
            ),
            GhostTool(
                name="ghost.list",
                description="List all Ghost databases and their status",
                category="database",
                parameters={},
            ),
            GhostTool(
                name="ghost.get",
                description="Get detailed info about a specific database",
                category="database",
                parameters={"db_id": "Database ID"},
            ),
            GhostTool(
                name="ghost.delete",
                description="Delete a Ghost database and all its workspaces",
                category="database",
                parameters={"db_id": "Database ID"},
            ),
            GhostTool(
                name="ghost.fork",
                description="Fork a database into an isolated agent workspace",
                category="workspace",
                parameters={"source_db_id": "Source database ID", "agent_id": "Agent identifier"},
            ),
            GhostTool(
                name="ghost.workspace.list",
                description="List all active agent workspaces",
                category="workspace",
                parameters={"database_id": "Optional filter by database"},
            ),
            GhostTool(
                name="ghost.workspace.get",
                description="Get details of a specific workspace",
                category="workspace",
                parameters={"ws_id": "Workspace ID"},
            ),
            GhostTool(
                name="ghost.sql",
                description="Execute SQL query against a database",
                category="query",
                parameters={"db_id": "Database ID", "query": "SQL query string", "params": "Optional query parameters"},
            ),
            GhostTool(
                name="ghost.sql.history",
                description="View recent SQL execution history",
                category="query",
                parameters={"db_id": "Optional filter by database", "limit": "Max results"},
            ),
            GhostTool(
                name="ghost.checkpoint.create",
                description="Create a named checkpoint (snapshot) of a database",
                category="checkpoint",
                parameters={"db_id": "Database ID", "label": "Checkpoint label"},
            ),
            GhostTool(
                name="ghost.checkpoint.list",
                description="List all checkpoints for a database",
                category="checkpoint",
                parameters={"db_id": "Optional filter by database"},
            ),
            GhostTool(
                name="ghost.checkpoint.restore",
                description="Restore a database to a previous checkpoint",
                category="checkpoint",
                parameters={"checkpoint_id": "Checkpoint ID"},
            ),
            GhostTool(
                name="ghost.cleanup",
                description="Clean up idle workspaces older than threshold",
                category="maintenance",
                parameters={"hours": "Idle threshold in hours"},
            ),
        ]
        for tool in tools:
            self._tools[tool.name] = tool

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {"name": t.name, "description": t.description, "category": t.category, "parameters": t.parameters}
            for t in self._tools.values()
        ]

    def get_tool(self, name: str) -> Optional[GhostTool]:
        return self._tools.get(name)

    async def execute(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a Ghost tool by name."""
        tool = self._tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}

        client = await self._ensure_client()

        try:
            if tool_name == "ghost.status":
                return {"success": True, "data": client.get_status()}

            elif tool_name == "ghost.create":
                db = await client.create_database(
                    name=kwargs.get("name", "unnamed"),
                    parent_id=kwargs.get("parent_id"),
                )
                return {"success": True, "data": {"id": db.id, "name": db.name, "status": db.status.value}}

            elif tool_name == "ghost.list":
                dbs = await client.list_databases()
                return {"success": True, "data": [{"id": d.id, "name": d.name, "status": d.status.value} for d in dbs]}

            elif tool_name == "ghost.get":
                db = await client.get_database(kwargs.get("db_id", ""))
                if not db:
                    return {"success": False, "error": "Database not found"}
                return {"success": True, "data": {"id": db.id, "name": db.name, "status": db.status.value}}

            elif tool_name == "ghost.delete":
                ok = await client.delete_database(kwargs.get("db_id", ""))
                return {"success": ok}

            elif tool_name == "ghost.fork":
                ws = await client.fork_database(
                    source_db_id=kwargs.get("source_db_id", ""),
                    agent_id=kwargs.get("agent_id", "unknown"),
                )
                return {"success": True, "data": {"id": ws.id, "database_id": ws.database_id, "agent_id": ws.agent_id}}

            elif tool_name == "ghost.workspace.list":
                wss = await client.list_workspaces(database_id=kwargs.get("database_id"))
                return {"success": True, "data": [{"id": w.id, "agent_id": w.agent_id, "status": w.status.value} for w in wss]}

            elif tool_name == "ghost.workspace.get":
                ws = await client.get_workspace(kwargs.get("ws_id", ""))
                if not ws:
                    return {"success": False, "error": "Workspace not found"}
                return {"success": True, "data": {"id": ws.id, "agent_id": ws.agent_id, "status": ws.status.value}}

            elif tool_name == "ghost.sql":
                result = await client.execute_sql(
                    db_id=kwargs.get("db_id", ""),
                    query=kwargs.get("query", ""),
                    params=kwargs.get("params"),
                )
                return {"success": True, "data": result}

            elif tool_name == "ghost.sql.history":
                history = await client.get_sql_history(
                    db_id=kwargs.get("db_id"),
                    limit=kwargs.get("limit", 50),
                )
                return {"success": True, "data": history}

            elif tool_name == "ghost.checkpoint.create":
                cp = await client.create_checkpoint(
                    db_id=kwargs.get("db_id", ""),
                    label=kwargs.get("label", "unnamed"),
                )
                return {"success": True, "data": {"id": cp.id, "label": cp.label}}

            elif tool_name == "ghost.checkpoint.list":
                cps = await client.list_checkpoints(db_id=kwargs.get("db_id"))
                return {"success": True, "data": [{"id": c.id, "label": c.label} for c in cps]}

            elif tool_name == "ghost.checkpoint.restore":
                ok = await client.restore_checkpoint(kwargs.get("checkpoint_id", ""))
                return {"success": ok}

            elif tool_name == "ghost.cleanup":
                cleaned = await client.cleanup_idle_workspaces(
                    idle_hours=kwargs.get("hours", 24),
                )
                return {"success": True, "data": {"cleaned": cleaned}}

            return {"success": False, "error": f"Tool '{tool_name}' not implemented"}

        except Exception as e:
            logger.error(f"Ghost tool '{tool_name}' failed: {e}")
            return {"success": False, "error": str(e)}


# Singleton registry instance
ghost_tool_registry = GhostToolRegistry()

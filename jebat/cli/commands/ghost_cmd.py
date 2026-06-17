"""Ghost CLI — command handlers for database operations.

Usage:
    jebat ghost status              # Check Ghost CLI availability
    jebat ghost list                # List all databases
    jebat ghost create my-db        # Create ephemeral DB
    jebat ghost fork main-db agent  # Fork for agent work
    jebat ghost sql my-db "SELECT *" # Execute SQL
    jebat ghost workspace coder     # List agent workspaces
    jebat ghost checkpoint main pre-refactor # Checkpoint
    jebat ghost cleanup --hours 24  # Clean old workspaces
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, List, Optional

from jebat.features.ghost.ghost_integration import GhostClient, create_ghost_client


class GhostCommand:
    """CLI command handler for Ghost database operations."""

    def __init__(self):
        self.client: Optional[GhostClient] = None

    async def _ensure_client(self) -> GhostClient:
        if self.client is None:
            self.client = await create_ghost_client()
        return self.client

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        """Register ghost subcommands on an argparse subparsers group."""
        ghost_parser = subparsers.add_parser("ghost", help="Ghost database operations")
        ghost_sub = ghost_parser.add_subparsers(dest="ghost_cmd")

        # status
        ghost_sub.add_parser("status", help="Check Ghost availability")

        # list
        ghost_sub.add_parser("list", help="List all databases")

        # create
        create_p = ghost_sub.add_parser("create", help="Create ephemeral DB")
        create_p.add_argument("name", help="Database name")
        create_p.add_argument("--parent", help="Parent database ID to clone from")

        # fork
        fork_p = ghost_sub.add_parser("fork", help="Fork for agent work")
        fork_p.add_argument("source_db", help="Source database ID or name")
        fork_p.add_argument("agent_id", help="Agent identifier")

        # sql
        sql_p = ghost_sub.add_parser("sql", help="Execute SQL")
        sql_p.add_argument("db_id", help="Database ID")
        sql_p.add_argument("query", help="SQL query")

        # workspace
        ws_p = ghost_sub.add_parser("workspace", help="List agent workspaces")
        ws_p.add_argument("agent_id", nargs="?", help="Filter by agent")

        # checkpoint
        cp_p = ghost_sub.add_parser("checkpoint", help="Create checkpoint")
        cp_p.add_argument("db_id", help="Database ID")
        cp_p.add_argument("label", help="Checkpoint label")

        # cleanup
        cleanup_p = ghost_sub.add_parser("cleanup", help="Clean idle workspaces")
        cleanup_p.add_argument("--hours", type=float, default=24, help="Idle threshold (hours)")

    async def handle(self, args: argparse.Namespace) -> str:
        """Route to the appropriate handler."""
        cmd = getattr(args, "ghost_cmd", None)
        if not cmd:
            return "Usage: jebat ghost <command>"

        client = await self._ensure_client()
        handlers = {
            "status": self._status,
            "list": self._list,
            "create": self._create,
            "fork": self._fork,
            "sql": self._sql,
            "workspace": self._workspace,
            "checkpoint": self._checkpoint,
            "cleanup": self._cleanup,
        }
        handler = handlers.get(cmd)
        if not handler:
            return f"Unknown ghost command: {cmd}"
        return await handler(client, args)

    async def _status(self, client: GhostClient, args: argparse.Namespace) -> str:
        status = client.get_status()
        lines = [
            "Ghost Database Integration — Status",
            f"  Databases:   {status['databases']}",
            f"  Workspaces:  {status['workspaces']} ({status['active_workspaces']} active)",
            f"  Checkpoints: {status['checkpoints']}",
            f"  SQL queries: {status['sql_queries_executed']}",
        ]
        return "\n".join(lines)

    async def _list(self, client: GhostClient, args: argparse.Namespace) -> str:
        dbs = await client.list_databases()
        if not dbs:
            return "No databases found. Create one with: jebat ghost create <name>"
        lines = ["Ghost Databases:"]
        for db in dbs:
            lines.append(f"  {db.id}  {db.name:<20s}  [{db.status.value}]")
        return "\n".join(lines)

    async def _create(self, client: GhostClient, args: argparse.Namespace) -> str:
        db = await client.create_database(name=args.name, parent_id=args.parent)
        return f"Database created: {db.id} ({db.name})"

    async def _fork(self, client: GhostClient, args: argparse.Namespace) -> str:
        ws = await client.fork_database(source_db_id=args.source_db, agent_id=args.agent_id)
        return f"Workspace forked: {ws.id} for agent {ws.agent_id} from {ws.database_id}"

    async def _sql(self, client: GhostClient, args: argparse.Namespace) -> str:
        result = await client.execute_sql(db_id=args.db_id, query=args.query)
        return f"SQL executed on {args.db_id}: {result.get('query', '')[:60]}..."

    async def _workspace(self, client: GhostClient, args: argparse.Namespace) -> str:
        wss = await client.list_workspaces()
        if args.agent_id:
            wss = [w for w in wss if w.agent_id == args.agent_id]
        if not wss:
            return "No workspaces found."
        lines = ["Agent Workspaces:"]
        for ws in wss:
            lines.append(f"  {ws.id}  agent={ws.agent_id:<12s}  db={ws.database_id}  [{ws.status.value}]")
        return "\n".join(lines)

    async def _checkpoint(self, client: GhostClient, args: argparse.Namespace) -> str:
        cp = await client.create_checkpoint(db_id=args.db_id, label=args.label)
        return f"Checkpoint created: {cp.id} ({cp.label}) on {args.db_id}"

    async def _cleanup(self, client: GhostClient, args: argparse.Namespace) -> str:
        cleaned = await client.cleanup_idle_workspaces(idle_hours=args.hours)
        return f"Cleaned {cleaned} idle workspaces (threshold: {args.hours}h)"


def run_ghost_command(args: argparse.Namespace) -> None:
    """Entry point for ghost CLI commands."""
    cmd = GhostCommand()
    result = asyncio.run(cmd.handle(args))
    print(result)

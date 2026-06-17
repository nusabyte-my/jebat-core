"""
JEBAT Ghost Integration — Database platform for AI agents.

Ghost provides unlimited Postgres databases with forking, ephemeral instances,
and native MCP integration. This module wraps the Ghost CLI and provides
JEBAT-native tools for agent workflows.

Requirements:
- Ghost CLI installed: curl -fsSL https://install.ghost.build | sh
- Authenticated: ghost init && ghost login

Documentation: https://ghost.build
MCP Tools: 25+ available via `ghost mcp`
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GhostDatabase:
    """Represents a Ghost database."""
    name: str
    connection_string: str = ""
    status: str = "unknown"
    is_dedicated: bool = False
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "connection_string": self.connection_string,
            "status": self.status,
            "is_dedicated": self.is_dedicated,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


@dataclass
class GhostQueryResult:
    """Result of a SQL query execution."""
    rows: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    error: Optional[str] = None


class GhostClient:
    """
    Ghost database client for JEBAT agents.
    
    Wraps the `ghost` CLI for database operations optimized for agent workflows.
    Provides instant database creation, forking, and SQL execution.
    
    Example:
        ghost = GhostClient()
        db = await ghost.create_db("research-topic")
        await ghost.execute_sql(db.name, "CREATE TABLE findings (...)")
        results = await ghost.execute_sql(db.name, "SELECT * FROM findings")
    """
    
    def __init__(self, ghost_cli: str = "ghost", timeout: int = 30):
        self.ghost_cli = ghost_cli
        self.timeout = timeout
        self._check_cli_available()
    
    def _check_cli_available(self) -> None:
        """Verify Ghost CLI is installed and accessible."""
        try:
            result = subprocess.run(
                [self.ghost_cli, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError("Ghost CLI not found")
        except FileNotFoundError:
            raise RuntimeError(
                "Ghost CLI not installed. Install with: "
                "curl -fsSL https://install.ghost.build | sh"
            )
    
    def _run(self, args: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Execute a ghost CLI command."""
        cmd = [self.ghost_cli] + args
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout or self.timeout,
            env={**os.environ, "GHOST_OUTPUT_FORMAT": "json"},
        )
    
    async def _run_async(self, args: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Execute a ghost CLI command asynchronously."""
        cmd = [self.ghost_cli] + args
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "GHOST_OUTPUT_FORMAT": "json"},
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout or self.timeout,
        )
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=proc.returncode,
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else "",
        )
    
    # ── Database Lifecycle ──────────────────────────────────────────────
    
    async def create_db(self, name: str, dedicated: bool = False) -> GhostDatabase:
        """Create a new ephemeral database."""
        cmd = ["create-dedicated" if dedicated else "create", name, "--format", "json"]
        result = await self._run_async(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create database: {result.stderr}")
        data = json.loads(result.stdout)
        return GhostDatabase(
            name=data.get("name", name),
            connection_string=data.get("connection_string", ""),
            status="active",
            is_dedicated=dedicated,
            created_at=data.get("created_at", ""),
        )
    
    async def fork_db(self, source: str, name: str, dedicated: bool = False) -> GhostDatabase:
        """Fork an existing database for isolated agent work."""
        cmd = ["fork-dedicated" if dedicated else "fork", source, name, "--format", "json"]
        result = await self._run_async(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fork database: {result.stderr}")
        data = json.loads(result.stdout)
        return GhostDatabase(
            name=data.get("name", name),
            connection_string=data.get("connection_string", ""),
            status="active",
            is_dedicated=dedicated,
            created_at=data.get("created_at", ""),
        )
    
    async def delete_db(self, name: str, force: bool = False) -> bool:
        """Delete a database."""
        cmd = ["delete", name]
        if force:
            cmd.append("--force")
        result = await self._run_async(cmd)
        return result.returncode == 0
    
    async def get_connection_string(self, name: str) -> str:
        """Get connection string for a database."""
        result = await self._run_async(["connect", name, "--format", "json"])
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get connection string: {result.stderr}")
        data = json.loads(result.stdout)
        return data.get("connection_string", "")
    
    # ── SQL Execution ──────────────────────────────────────────────────
    
    async def execute_sql(
        self,
        database: str,
        query: str,
        params: Optional[List[Any]] = None,
    ) -> GhostQueryResult:
        """Execute a SQL query on a database."""
        cmd = ["sql", database, query]
        if params:
            # Ghost doesn't support parameterized queries via CLI directly
            # We'll use string interpolation with caution (agents should sanitize)
            pass
        result = await self._run_async(cmd)
        if result.returncode != 0:
            return GhostQueryResult(error=result.stderr)
        try:
            data = json.loads(result.stdout)
            return GhostQueryResult(
                rows=data.get("rows", []),
                columns=data.get("columns", []),
                row_count=data.get("row_count", len(data.get("rows", []))),
                execution_time_ms=data.get("execution_time_ms", 0.0),
            )
        except json.JSONDecodeError:
            return GhostQueryResult(error="Failed to parse query result")
    
    # ── Utility ────────────────────────────────────────────────────────
    
    async def list_databases(self) -> List[GhostDatabase]:
        """List all databases."""
        result = await self._run_async(["list", "--format", "json"])
        if result.returncode != 0:
            raise RuntimeError(f"Failed to list databases: {result.stderr}")
        data = json.loads(result.stdout)
        return [
            GhostDatabase(
                name=d.get("name", ""),
                connection_string=d.get("connection_string", ""),
                status=d.get("status", "unknown"),
                is_dedicated=d.get("is_dedicated", False),
                created_at=d.get("created_at", ""),
            )
            for d in data
        ]
    
    async def pause_db(self, name: str) -> bool:
        """Pause a running database to save resources."""
        result = await self._run_async(["pause", name])
        return result.returncode == 0
    
    async def resume_db(self, name: str) -> bool:
        """Resume a paused database."""
        result = await self._run_async(["resume", name])
        return result.returncode == 0
    
    async def share_db(self, name: str, expiry_hours: int = 24) -> str:
        """Create a shareable link for a database."""
        result = await self._run_async(
            ["share", name, "--expiry-hours", str(expiry_hours), "--format", "json"]
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to share database: {result.stderr}")
        data = json.loads(result.stdout)
        return data.get("share_url", "")


# Singleton instance
_ghost_client: Optional[GhostClient] = None


def get_ghost_client(timeout: int = 30) -> GhostClient:
    """Get or create singleton GhostClient."""
    global _ghost_client
    if _ghost_client is None:
        _ghost_client = GhostClient(timeout=timeout)
    return _ghost_client


# Convenience functions
async def ghost_create_db(name: str, dedicated: bool = False) -> GhostDatabase:
    """Create a new database."""
    return await get_ghost_client().create_db(name, dedicated)


async def ghost_fork_db(source: str, name: str, dedicated: bool = False) -> GhostDatabase:
    """Fork a database."""
    return await get_ghost_client().fork_db(source, name, dedicated)


async def ghost_sql(database: str, query: str) -> GhostQueryResult:
    """Execute SQL query."""
    return await get_ghost_client().execute_sql(database, query)


async def ghost_fork_checkpoint(source: str, checkpoint_name: str) -> GhostDatabase:
    """Create a checkpoint fork for agent state recovery."""
    return await get_ghost_client().fork_db(source, checkpoint_name, dedicated=False)


async def ghost_list_databases() -> List[GhostDatabase]:
    """List all databases."""
    return await get_ghost_client().list_databases()


async def ghost_delete_db(name: str, force: bool = False) -> bool:
    """Delete a database."""
    return await get_ghost_client().delete_db(name, force)


__all__ = [
    "GhostClient",
    "GhostDatabase",
    "GhostQueryResult",
    "get_ghost_client",
    "ghost_create_db",
    "ghost_fork_db",
    "ghost_sql",
    "ghost_fork_checkpoint",
    "ghost_list_databases",
    "ghost_delete_db",
]
"""
JEBAT Ghost Features — Database platform for AI agents.

Ghost provides unlimited Postgres databases with forking, ephemeral instances,
and native MCP integration. This module wraps the Ghost CLI and provides
JEBAT-native tools for agent workflows.

Requirements:
- Ghost CLI installed: curl -fsSL https://install.ghost.build | sh
- Authenticated: ghost init && ghost login

Documentation: https://ghost.build
MCP Tools: 25+ available via `ghost mcp`
"""

from .ghost_integration import (
    GhostClient,
    GhostDatabase,
    GhostQueryResult,
    get_ghost_client,
    ghost_create_db,
    ghost_fork_db,
    ghost_sql,
    ghost_fork_checkpoint,
    ghost_list_databases,
    ghost_delete_db,
)

from .ghost_tools import (
    ghost_create_db_tool,
    ghost_fork_db_tool,
    ghost_delete_db_tool,
    ghost_list_dbs_tool,
    ghost_sql_tool,
    ghost_connect_tool,
    ghost_pause_db_tool,
    ghost_resume_db_tool,
    ghost_agent_workspace_tool,
    ghost_checkpoint_tool,
    ghost_cleanup_agent_workspaces_tool,
    ghost_share_db_tool,
)

__all__ = [
    # Classes
    "GhostClient",
    "GhostDatabase",
    "GhostQueryResult",
    # Integration functions
    "get_ghost_client",
    "ghost_create_db",
    "ghost_fork_db",
    "ghost_sql",
    "ghost_fork_checkpoint",
    "ghost_list_databases",
    "ghost_delete_db",
    # Tools
    "ghost_create_db_tool",
    "ghost_fork_db_tool",
    "ghost_delete_db_tool",
    "ghost_list_dbs_tool",
    "ghost_sql_tool",
    "ghost_connect_tool",
    "ghost_pause_db_tool",
    "ghost_resume_db_tool",
    "ghost_agent_workspace_tool",
    "ghost_checkpoint_tool",
    "ghost_cleanup_agent_workspaces_tool",
    "ghost_share_db_tool",
]
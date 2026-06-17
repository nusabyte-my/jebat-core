"""Ghost Database Integration — ephemeral database workspaces for agents."""

from jebat.features.ghost.ghost_integration import (
    GhostClient,
    GhostDatabase,
    GhostWorkspace,
    create_ghost_client,
)
from jebat.features.ghost.ghost_tools import (
    GhostToolRegistry,
    ghost_tool_registry,
)

__all__ = [
    "GhostClient",
    "GhostDatabase",
    "GhostWorkspace",
    "create_ghost_client",
    "GhostToolRegistry",
    "ghost_tool_registry",
]

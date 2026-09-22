"""Single source of truth for JEBAT's MCP protocol + server identity.

Previously these values were duplicated across ``mcp_server.py``, ``mcp_client.py``
and ``mcp_transport.py`` with *conflicting* protocol versions: the client offered
the oldest revision (``2024-11-05``) while the server defaulted to the newest
(``2026-07-28``), so JEBAT's own client and server always negotiated down to the
lowest common version. The server version was a hardcoded ``0.1.0`` that drifted
from the real package version.

Everything that speaks MCP now imports from here.
"""
from __future__ import annotations

# ── JSON-RPC ─────────────────────────────────────────────────────────────────
JSONRPC_VERSION = "2.0"

# ── MCP protocol revision we actually speak ──────────────────────────────────
# The latest revision JEBAT implements. Clients SHOULD offer the newest they
# support; the server echoes it back when it can.
MCP_PROTOCOL_VERSION = "2026-07-28"

# Revisions accepted on the wire (oldest → newest). A client offering any of
# these is honoured; anything else falls back to MCP_PROTOCOL_VERSION.
SUPPORTED_PROTOCOL_VERSIONS: tuple[str, ...] = (
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
    "2026-07-28",
)

# ── Server / client identity ─────────────────────────────────────────────────
SERVER_NAME = "jebat-mcp-server"

# Track the JEBAT package version so server, CLI, page and pyproject share one number.
try:
    from jebat import __version__ as _PKG_VERSION
except Exception:  # pragma: no cover - defensive import fallback
    _PKG_VERSION = "0.0.0+unknown"
SERVER_VERSION: str = _PKG_VERSION

# The client reports the same package version (it ships inside JEBAT).
CLIENT_NAME = "jebat-cli"
CLIENT_VERSION = SERVER_VERSION

__all__ = [
    "JSONRPC_VERSION",
    "MCP_PROTOCOL_VERSION",
    "SUPPORTED_PROTOCOL_VERSIONS",
    "SERVER_NAME",
    "SERVER_VERSION",
    "CLIENT_NAME",
    "CLIENT_VERSION",
]

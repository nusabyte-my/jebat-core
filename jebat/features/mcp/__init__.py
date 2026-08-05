"""JEBAT MCP Client Feature — connects to external MCP servers.

Exposes MCPClient for connecting to MCP servers via stdio or HTTP,
auto-discovering tools and registering them in JEBAT's tool registry.
"""

from .mcp_client import (
    HTTPTransport,
    MCPClient,
    MCPError,
    MCPServerConfig,
    MCPToolInfo,
    MCPResourceInfo,
    StdioTransport,
    TransportType,
)

__all__ = [
    "MCPClient",
    "MCPError",
    "MCPServerConfig",
    "MCPToolInfo",
    "MCPResourceInfo",
    "StdioTransport",
    "HTTPTransport",
    "TransportType",
]
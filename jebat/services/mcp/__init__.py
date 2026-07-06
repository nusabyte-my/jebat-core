"""
JEBAT MCP (Model Context Protocol) Package

Provides standardized communication protocol for AI clients, enabling:
- Tool discovery and invocation
- Resource access and management
- Prompt template management
- Session management and heartbeat
- Real-time event broadcasting
- JSON-RPC 2.0 compliant protocol implementation
"""

from .protocol_server import (
    MCPCapability,
    MCPMessage,
    MCPProtocolServer,
    MCPSession,
)

__all__ = [
    "MCPProtocolServer",
    "MCPCapability",
    "MCPSession",
    "MCPMessage",
]

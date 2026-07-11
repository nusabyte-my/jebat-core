"""MCP (Model Context Protocol) SERVER for JEBAT CLI Agent.

Makes JEBAT a tool PROVIDER that IDEs (VS Code, Cursor, Windsurf, JetBrains)
connect TO via the MCP protocol. The server exposes all registered JEBAT tools
as MCP tools with proper JSON Schema input definitions, and dispatches
incoming tool calls to the JEBAT tool registry.

Transport: stdio (JSON-RPC 2.0 messages, one per line, over stdin/stdout)
           HTTP (SSE + StreamableHTTP, for remote IDE connections)

Protocol version: 2024-11-05

Usage:
    # Start MCP server (IDE connects via stdio)
    jebat mcp serve

    # Start MCP server on HTTP port
    jebat mcp serve --transport http --port 8099
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from jebat.tools import TOOL_REGISTRY, ToolDef, call_tool

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

MCP_PROTOCOL_VERSION = "2024-11-05"
JSONRPC_VERSION = "2.0"
SERVER_NAME = "jebat-mcp-server"
SERVER_VERSION = "0.1.0"


# ── Data Structures ────────────────────────────────────────────────────────

@dataclass
class MCPCapabilities:
    """Server capabilities announced during initialization."""
    tools: bool = True
    resources: bool = False  # Future: expose JEBAT knowledge base
    prompts: bool = False    # Future: expose JEBAT skill prompts
    logging: bool = True
    experimental: Dict[str, bool] = field(default_factory=dict)


class TransportMode(str, Enum):
    STDIO = "stdio"
    HTTP = "http"


# ── JSON-RPC Helpers ────────────────────────────────────────────────────────

def make_response(request_id: Any, result: Any) -> str:
    """Create a JSON-RPC success response."""
    return json.dumps({
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "result": result,
    })


def make_error(request_id: Any, code: int, message: str, data: Any = None) -> str:
    """Create a JSON-RPC error response."""
    error_obj = {"code": code, "message": message}
    if data is not None:
        error_obj["data"] = data
    return json.dumps({
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": error_obj,
    })


def make_notification(method: str, params: Dict = None) -> str:
    """Create a JSON-RPC notification (no id, no response expected)."""
    obj = {"jsonrpc": JSONRPC_VERSION, "method": method}
    if params:
        obj["params"] = params
    return json.dumps(obj)


# ── Error Codes ──────────────────────────────────────────────────────────────

class MCPError:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    # MCP-specific
    TOOL_NOT_FOUND = -32001
    TOOL_EXECUTION_ERROR = -32002
    RESOURCE_NOT_FOUND = -32003
    PROMPT_NOT_FOUND = -32004


# ── Tool Schema Builder ──────────────────────────────────────────────────────

def build_tool_schema(tool_def: ToolDef) -> Dict[str, Any]:
    """Convert a JEBAT ToolDef into an MCP tool definition with JSON Schema.

    MCP tool format:
    {
        "name": "tool_name",
        "description": "What this tool does",
        "inputSchema": {
            "type": "object",
            "properties": { ... },
            "required": [ ... ]
        }
    }
    """
    # ToolDef stores params in .schema (JSON Schema format)
    # JSON Schema is already in MCP-compatible format — pass through directly
    schema = tool_def.schema or {"type": "object", "properties": {}}
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    input_schema = {
        "type": "object",
        "properties": properties,
    }
    if required:
        input_schema["required"] = required

    return {
        "name": tool_def.name,
        "description": tool_def.description or f"JEBAT tool: {tool_def.name}",
        "inputSchema": input_schema,
    }


# ── MCP Server Core ──────────────────────────────────────────────────────────

class MCPServer:
    """MCP Server that exposes JEBAT tools to IDEs.

    Handles the full MCP protocol lifecycle:
    1. initialize → server announces capabilities
    2. tools/list → returns all registered JEBAT tools as MCP tools
    3. tools/call → dispatches to JEBAT tool registry and returns result
    4. resources/list → (future) returns JEBAT knowledge resources
    5. prompts/list → (future) returns JEBAT skill prompts

    The server can run on stdio (for local IDE integration) or HTTP
    (for remote IDE connections over network).
    """

    def __init__(self, transport: TransportMode = TransportMode.STDIO,
                 http_port: int = 8099, host: str = "127.0.0.1"):
        self.transport = transport
        self.http_port = http_port
        self.host = host
        self.capabilities = MCPCapabilities()
        self.client_info: Dict[str, Any] = {}
        self._initialized = False
        self._tools_loaded = False
        self._request_handlers: Dict[str, Any] = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "prompts/list": self._handle_prompts_list,
            "ping": self._handle_ping,
            "logging/setLevel": self._handle_set_log_level,
            "completion/complete": self._handle_completion,
        }

    # ── Request Dispatch ──────────────────────────────────────────────────

    async def handle_request(self, request: Dict[str, Any]) -> Optional[str]:
        """Process a single JSON-RPC request and return the response string.

        Returns None for notifications (no response expected).
        """
        request_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        # Notifications have no id — we handle but don't respond
        if request_id is None and method:
            handler = self._request_handlers.get(method)
            if handler:
                try:
                    await handler(params)
                except Exception as e:
                    logger.warning(f"Notification handler error: {e}")
            return None

        # Validate required fields
        if "jsonrpc" not in request or request["jsonrpc"] != JSONRPC_VERSION:
            return make_error(request_id, MCPError.INVALID_REQUEST,
                              "Invalid JSON-RPC version")

        if not method:
            return make_error(request_id, MCPError.INVALID_REQUEST,
                              "Missing method")

        # Check initialization requirement
        if method != "initialize" and not self._initialized:
            return make_error(request_id, MCPError.INVALID_REQUEST,
                              "Server not initialized. Send 'initialize' first.")

        # Dispatch to handler
        handler = self._request_handlers.get(method)
        if handler is None:
            return make_error(request_id, MCPError.METHOD_NOT_FOUND,
                              f"Method not found: {method}")

        try:
            result = await handler(params)
            return make_response(request_id, result)
        except Exception as e:
            logger.error(f"Handler error for {method}: {e}\n{traceback.format_exc()}")
            return make_error(request_id, MCPError.INTERNAL_ERROR,
                              str(e), data={"traceback": traceback.format_exc()})

    # ── Handler Methods ──────────────────────────────────────────────────

    async def _handle_initialize(self, params: Dict) -> Dict:
        """Handle MCP initialize request — announce server capabilities."""
        self.client_info = params.get("clientInfo", {})
        client_name = self.client_info.get("name", "unknown")
        client_version = self.client_info.get("version", "unknown")

        logger.info(f"MCP client connecting: {client_name} v{client_version}")

        self._initialized = True

        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": True},
                "logging": {},
                "experimental": self.capabilities.experimental,
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        }

    def _ensure_tools_loaded(self) -> None:
        """Import all JEBAT tool modules to populate TOOL_REGISTRY."""
        if self._tools_loaded:
            return
        try:
            from jebat.features.fileops import file_ops
            from jebat.features.terminal import terminal_exec
            from jebat.features.browser import browser
            from jebat.features.vision import vision
            from jebat.features.search import web_search
            from jebat.features.auth import auth
            from jebat.features.cron import cron
            from jebat.features.wiki import wiki
            from jebat.features.image_gen import image_gen
        except ImportError:
            pass  # Some modules may not be available in all environments
        self._tools_loaded = True
        logger.info(f"MCP server loaded {len(TOOL_REGISTRY)} tools into registry")

    async def _handle_tools_list(self, params: Dict) -> Dict:
        """Return all registered JEBAT tools as MCP tool definitions."""
        self._ensure_tools_loaded()
        tools = []
        for name, tool_def in TOOL_REGISTRY.items():
            tools.append(build_tool_schema(tool_def))
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict) -> Dict:
        """Execute a tool call requested by the IDE."""
        self._ensure_tools_loaded()
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name not in TOOL_REGISTRY:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Tool not found: {tool_name}"}],
            }

        tool_def = TOOL_REGISTRY[tool_name]

        # Safety tier check — dangerous tools require confirmation
        if tool_def.safety_tier == "dangerous":
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"Tool '{tool_name}' is in the dangerous safety tier. "
                            f"Requires explicit confirmation in CLI mode."
                }],
            }

        try:
            # Dispatch to JEBAT tool registry
            result = await call_tool(tool_name, **arguments)

            # Convert result to MCP content format
            if isinstance(result, str):
                content = [{"type": "text", "text": result}]
            elif isinstance(result, dict):
                # Try to serialize; if it has 'content' key in MCP format, use it
                if "content" in result and isinstance(result["content"], list):
                    content = result["content"]
                else:
                    content = [{"type": "text", "text": json.dumps(result, indent=2)}]
            elif isinstance(result, list):
                content = [{"type": "text", "text": json.dumps(result, indent=2)}]
            else:
                content = [{"type": "text", "text": str(result)}]

            return {"content": content}

        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"Tool execution error: {type(e).__name__}: {e}"
                }],
            }

    async def _handle_resources_list(self, params: Dict) -> Dict:
        """Return available resources (future: JEBAT knowledge base)."""
        # Not yet implemented — return empty
        return {"resources": []}

    async def _handle_prompts_list(self, params: Dict) -> Dict:
        """Return available prompts (future: JEBAT skill prompts)."""
        # Not yet implemented — return empty
        return {"prompts": []}

    async def _handle_ping(self, params: Dict) -> Dict:
        """Health check ping."""
        return {"status": "ok", "timestamp": str(asyncio.get_event_loop().time())}

    async def _handle_set_log_level(self, params: Dict) -> None:
        """Set server log level (notification — no response)."""
        level = params.get("level", "info")
        level_map = {
            "debug": logging.DEBUG, "info": logging.INFO,
            "warning": logging.WARNING, "error": logging.ERROR,
        }
        if level in level_map:
            logger.setLevel(level_map[level])
            # Notify client of level change
            sys.stderr.write(make_notification("notifications/message", {
                "level": level,
                "data": f"Log level set to {level}",
            }) + "\n")

    async def _handle_completion(self, params: Dict) -> Dict:
        """Handle completion requests (future: tool name completion)."""
        return {"completion": {"values": [], "hasMore": False, "total": 0}}

    # ── Stdio Transport ──────────────────────────────────────────────────

    async def run_stdio(self) -> None:
        """Run the MCP server on stdio transport.

        Reads JSON-RPC messages from stdin (one per line),
        processes them, and writes responses to stdout.

        This is the mode used by IDEs that launch JEBAT as a
        subprocess (VS Code, Cursor, Windsurf, JetBrains).
        """
        logger.info(f"Starting MCP server on stdio transport")
        sys.stderr.write(f"[JEBAT MCP Server] Starting on stdio, "
                         f"protocol v{MCP_PROTOCOL_VERSION}\n")
        sys.stderr.flush()

        # Read/write on the raw file descriptors. connect_read_pipe() and
        # sys.stdin.buffer.detach().read(1) both treat a subprocess pipe as an
        # immediate EOF and kill the server, so we use os.read/os.write which
        # block correctly until the IDE sends data or closes the pipe.
        infd = sys.stdin.fileno()
        outfd = sys.stdout.fileno()

        def blocking_readline() -> Optional[bytes]:
            data = b""
            while True:
                chunk = os.read(infd, 1)
                if chunk == b"":
                    # EOF — client disconnected
                    return data if data else None
                data += chunk
                if chunk == b"\n":
                    return data

        async def read_line() -> Optional[bytes]:
            return await asyncio.get_event_loop().run_in_executor(None, blocking_readline)

        def write_line(payload: bytes) -> None:
            os.write(outfd, payload + b"\n")

        try:
            while True:
                raw = await read_line()
                if raw is None:
                    logger.info("MCP client disconnected (EOF)")
                    break

                line = raw.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line.decode("utf-8", errors="replace"))
                except json.JSONDecodeError as e:
                    write_line(make_error(None, MCPError.PARSE_ERROR,
                                          f"JSON parse error: {e}").encode())
                    continue

                response = await self.handle_request(request)
                if response is not None:
                    write_line(response.encode())

        except Exception as e:
            logger.error(f"Stdio server error: {e}")
            sys.stderr.write(f"[JEBAT MCP Server] Error: {e}\n")

    # ── HTTP Transport (SSE + StreamableHTTP) ────────────────────────────

    async def run_http(self) -> None:
        """Run the MCP server on HTTP transport.

        Implements the MCP StreamableHTTP specification:
        - POST /message — client sends JSON-RPC requests
        - GET /sse — server sends SSE notifications to client

        This mode allows remote IDEs to connect over network.
        """
        from httpx import ASGITransport, AsyncClient
        import uvicorn  # type: ignore
        from starlette.applications import Starlette  # type: ignore
        from starlette.routing import Route  # type: ignore
        from starlette.responses import JSONResponse, Response  # type: ignore
        import sse_starlette  # type: ignore

        logger.info(f"Starting MCP server on HTTP transport: {self.host}:{self.http_port}")
        sys.stderr.write(f"[JEBAT MCP Server] Starting on HTTP "
                         f"{self.host}:{self.http_port}\n")

        server_instance = self
        sse_connections: List = []

        async def handle_message(request):
            """Handle POST /message — client sends JSON-RPC request."""
            try:
                body = await request.json()
            except json.JSONDecodeError:
                return JSONResponse({"jsonrpc": JSONRPC_VERSION, "id": None,
                                     "error": {"code": MCPError.PARSE_ERROR,
                                               "message": "Invalid JSON"}},
                                    status_code=400)

            response = await server_instance.handle_request(body)
            if response is None:
                # Notification — no response
                return Response(status_code=204)
            return JSONResponse(json.loads(response))

        async def handle_sse(request):
            """Handle GET /sse — establish SSE connection for notifications."""
            async with sse_starlette.EventSourceResponse(request) as event_generator:
                sse_connections.append(event_generator)
                try:
                    async for event in event_generator:
                        pass  # Keep connection alive
                finally:
                    sse_connections.remove(event_generator)

        routes = [
            Route("/message", endpoint=handle_message, methods=["POST"]),
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
        ]
        app = Starlette(routes=routes)

        config = uvicorn.Config(app, host=self.host, port=self.http_port,
                                log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


# ── CLI Entrypoint ──────────────────────────────────────────────────────────

def run_server(transport: str = "stdio", port: int = 8099, host: str = "127.0.0.1"):
    """Start the MCP server — called from jebat mcp serve CLI command."""
    transport_mode = TransportMode(transport)
    server = MCPServer(transport=transport_mode, http_port=port, host=host)

    if transport_mode == TransportMode.STDIO:
        asyncio.run(server.run_stdio())
    elif transport_mode == TransportMode.HTTP:
        asyncio.run(server.run_http())
    else:
        raise ValueError(f"Unsupported transport: {transport}")


# ── IDE Configuration Templates ─────────────────────────────────────────────

IDE_CONFIGS = {
    "vscode": {
        "description": "VS Code MCP extension config (settings.json)",
        "config": {
            "mcp": {
                "servers": {
                    "jebat": {
                        "command": "jebat",
                        "args": ["mcp", "serve", "--transport", "stdio"],
                    }
                }
            }
        },
    },
    "cursor": {
        "description": "Cursor IDE MCP config (.cursor/mcp.json)",
        "config": {
            "mcpServers": {
                "jebat": {
                    "command": "jebat",
                    "args": ["mcp", "serve", "--transport", "stdio"],
                }
            }
        },
    },
    "windsurf": {
        "description": "Windsurf MCP config (.windsurf/mcp.json)",
        "config": {
            "mcpServers": {
                "jebat": {
                    "command": "jebat",
                    "args": ["mcp", "serve", "--transport", "stdio"],
                }
            }
        },
    },
    "jetbrains": {
        "description": "JetBrains AI Assistant MCP config",
        "config": {
            "mcpServers": {
                "jebat": {
                    "command": "jebat",
                    "args": ["mcp", "serve", "--transport", "stdio"],
                }
            }
        },
    },
    "http-remote": {
        "description": "Remote HTTP config (any IDE connecting over network)",
        "config": {
            "mcpServers": {
                "jebat": {
                    "url": "http://127.0.0.1:8099/message",
                    "transport": "http",
                }
            }
        },
    },
    "vscode-insider": {
        "description": "VS Code Insider MCP config (settings.json)",
        "config": {
            "mcp": {
                "servers": {
                    "jebat": {
                        "command": "jebat",
                        "args": ["mcp", "serve", "--transport", "stdio"],
                    }
                }
            }
        },
    },
}


def print_ide_configs():
    """Print IDE configuration templates for setting up JEBAT MCP."""
    for ide_name, ide_config in IDE_CONFIGS.items():
        print(f"\n{'='*60}")
        print(f"  {ide_name.upper()} — {ide_config['description']}")
        print(f"{'='*60}")
        print(json.dumps(ide_config["config"], indent=2))
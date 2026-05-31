"""MCP (Model Context Protocol) Client for JEBAT CLI Agent.

Connects to external MCP servers via two transports:
  - stdio: Launch subprocess, communicate via JSON-RPC over stdin/stdout
  - HTTP: Connect to SSE / StreamableHTTP endpoints

On connection, auto-disovers tools from the MCP server and registers
them in JEBAT's tool registry so the agent can call remote MCP tools
just like built-in ones.

Config is loaded from ~/.jebat/config.yaml under the 'mcp' key.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

import httpx

from jebat.config import JebatConfig, load_config
from jebat.tools import TOOL_REGISTRY, ToolDef, register_tool

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

MCP_PROTOCOL_VERSION = "2024-11-05"
JSONRPC_VERSION = "2.0"


class TransportType(str, Enum):
    STDIO = "stdio"
    HTTP = "http"


# ── Data Structures ────────────────────────────────────────────────────────

@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server connection.

    Attributes:
        name: Human-readable server name (used as prefix for registered tools).
        transport: 'stdio' or 'http'.
        command: For stdio — the command to launch the subprocess.
        args: For stdio — additional args passed to the subprocess.
        env: For stdio — extra env vars for the subprocess.
        url: For http — the SSE/StreamableHTTP endpoint URL.
        headers: For http — optional HTTP headers (e.g. auth tokens).
        enabled: Whether this server should be started.
        timeout: Default call timeout in seconds.
    """
    name: str
    transport: TransportType = TransportType.STDIO
    command: str = ""
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    url: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    timeout: int = 30


@dataclass
class MCPToolInfo:
    """A tool discovered from an MCP server."""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class MCPResourceInfo:
    """A resource discovered from an MCP server."""
    uri: str
    name: str
    description: str = ""
    mime_type: str = ""


# ── JSON-RPC Helpers ───────────────────────────────────────────────────────

def _make_request(method: str, params: Optional[Dict[str, Any]] = None,
                   request_id: Optional[str] = None) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 request message."""
    return {
        "jsonrpc": JSONRPC_VERSION,
        "method": method,
        "params": params or {},
        "id": request_id or str(uuid.uuid4()),
    }


def _make_notification(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 notification (no id, no response expected)."""
    return {
        "jsonrpc": JSONRPC_VERSION,
        "method": method,
        "params": params or {},
    }


def _is_error_response(response: Dict[str, Any]) -> bool:
    """Check if a JSON-RPC response contains an error."""
    return "error" in response and response["error"] is not None


def _extract_result(response: Dict[str, Any]) -> Any:
    """Extract the result field from a JSON-RPC response."""
    if _is_error_response(response):
        err = response["error"]
        raise MCPError(
            code=err.get("code", -1),
            message=err.get("message", "Unknown MCP error"),
            data=err.get("data"),
        )
    return response.get("result")


class MCPError(Exception):
    """Error returned by an MCP server via JSON-RPC."""

    def __init__(self, code: int = -1, message: str = "", data: Any = None):
        super().__init__(f"MCP error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data


# ── Transport: stdio ───────────────────────────────────────────────────────

class StdioTransport:
    """Communicate with an MCP server over subprocess stdin/stdout.

    The server is launched as a subprocess; messages are exchanged as
    JSON-RPC over stdin/stdout using newline-delimited JSON (NDJSON).
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self._reader_lock = asyncio.Lock()
        self._writer_lock = asyncio.Lock()
        self._pending: Dict[str, asyncio.Future] = {}

    async def start(self) -> None:
        """Launch the subprocess."""
        cmd = [self.config.command] + self.config.args
        env = {**os.environ, **self.config.env}

        logger.info(f"Starting MCP stdio server '{self.config.name}': {cmd}")

        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        # Start background reader to dispatch responses
        asyncio.create_task(self._read_stdout())

        # Drain stderr to prevent buffer blocking
        asyncio.create_task(self._drain_stderr())

    async def stop(self) -> None:
        """Terminate the subprocess gracefully."""
        if self.process is None:
            return

        logger.info(f"Stopping MCP stdio server '{self.config.name}'")

        # Try graceful shutdown first
        if self.process.stdin:
            try:
                # Send a best-effort close notification
                notification = _make_notification("shutdown")
                line = json.dumps(notification) + "\n"
                self.process.stdin.write(line.encode("utf-8"))
                await self.process.stdin.drain()
            except Exception:
                pass

            self.process.stdin.close()

        try:
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning(f"Force-killing MCP server '{self.config.name}'")
            self.process.kill()
            await self.process.wait()

        self.process = None

        # Cancel any pending requests
        for fut in self._pending.values():
            if not fut.done():
                fut.cancel()
        self._pending.clear()

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request and wait for the matching response."""
        if self.process is None or self.process.stdin is None:
            raise MCPError(-1, f"Stdio server '{self.config.name}' not running")

        request_id = request.get("id")
        if request_id is None:
            # Notification — no response expected
            await self._write_line(json.dumps(request))
            return {}

        # Register future for this request id
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = fut

        await self._write_line(json.dumps(request))

        # Wait for response with timeout
        try:
            return await asyncio.wait_for(fut, timeout=self.config.timeout)
        except asyncio.TimeoutError:
            self._pending.pop(request_id, None)
            raise MCPError(-1, f"Timeout waiting for response from '{self.config.name}' (id={request_id})")

    async def _write_line(self, data: str) -> None:
        """Write a single JSON line to stdin."""
        async with self._writer_lock:
            if self.process and self.process.stdin:
                self.process.stdin.write((data + "\n").encode("utf-8"))
                await self.process.stdin.drain()

    async def _read_stdout(self) -> None:
        """Read stdout line-by-line and dispatch to pending requests."""
        if self.process is None or self.process.stdout is None:
            return

        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    # EOF — server exited
                    logger.info(f"MCP server '{self.config.name}' stdout closed")
                    break

                line = line.decode("utf-8").strip()
                if not line:
                    continue

                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from '{self.config.name}': {line[:200]}")
                    continue

                # Dispatch response to pending request
                msg_id = message.get("id")
                if msg_id is not None and msg_id in self._pending:
                    fut = self._pending.pop(msg_id)
                    if not fut.done():
                        fut.set_result(message)
                else:
                    # Could be a notification from server
                    logger.debug(f"Received server notification from '{self.config.name}': {message}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error reading from '{self.config.name}': {e}")

    async def _drain_stderr(self) -> None:
        """Drain stderr to prevent subprocess blocking."""
        if self.process is None or self.process.stderr is None:
            return

        try:
            while True:
                line = await self.process.stderr.readline()
                if not line:
                    break
                logger.debug(f"MCP stderr [{self.config.name}]: {line.decode('utf-8').strip()}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error reading stderr from '{self.config.name}': {e}")

    def is_running(self) -> bool:
        """Check if the subprocess is alive."""
        return self.process is not None and self.process.returncode is None


# ── Transport: HTTP (SSE / StreamableHTTP) ─────────────────────────────────

class HTTPTransport:
    """Communicate with an MCP server over HTTP (SSE / StreamableHTTP).

    Uses httpx for async HTTP. The MCP HTTP transport sends JSON-RPC
    requests via POST and receives responses via SSE event streams.
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None
        self._session_id: Optional[str] = None

    async def start(self) -> None:
        """Initialize the HTTP client connection."""
        logger.info(f"Connecting to MCP HTTP server '{self.config.name}' at {self.config.url}")

        self.client = httpx.AsyncClient(
            base_url=self.config.url,
            headers=self.config.headers,
            timeout=httpx.Timeout(self.config.timeout, connect=10.0),
        )

    async def stop(self) -> None:
        """Close the HTTP client."""
        if self.client is not None:
            logger.info(f"Disconnecting from MCP HTTP server '{self.config.name}'")
            await self.client.aclose()
            self.client = None

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request via HTTP POST and return the response.

        For SSE endpoints, reads the event stream until a matching
        response is received. For StreamableHTTP, reads the direct
        JSON response.
        """
        if self.client is None:
            raise MCPError(-1, f"HTTP server '{self.config.name}' not connected")

        request_id = request.get("id")
        if request_id is None:
            # Notification — send but don't wait
            try:
                await self.client.post("/", json=request)
            except Exception as e:
                logger.warning(f"Failed to send notification to '{self.config.name}': {e}")
            return {}

        headers = {}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        try:
            response = await self.client.post("/", json=request, headers=headers)

            # Capture session id if provided
            new_session = response.headers.get("Mcp-Session-Id")
            if new_session:
                self._session_id = new_session

            # Parse the response body
            content_type = response.headers.get("content-type", "")

            if "text/event-stream" in content_type:
                # SSE response — parse events to find our result
                return await self._parse_sse_response(response, request_id)
            else:
                # Direct JSON response
                return response.json()

        except httpx.TimeoutException:
            raise MCPError(-1, f"Timeout calling MCP HTTP server '{self.config.name}'")
        except httpx.HTTPStatusError as e:
            raise MCPError(-1, f"HTTP error from '{self.config.name}': {e.response.status_code}")
        except Exception as e:
            raise MCPError(-1, f"Error communicating with '{self.config.name}': {e}")

    async def _parse_sse_response(self, response: httpx.Response,
                                    request_id: str) -> Dict[str, Any]:
        """Parse SSE event stream to find the JSON-RPC response matching request_id."""
        # httpx doesn't natively stream SSE; we parse the full text
        text = response.text
        for block in text.split("\n\n"):
            data_lines = []
            for line in block.split("\n"):
                if line.startswith("data:"):
                    data_lines.append(line[5:].strip())
                elif line.startswith("event:"):
                    event_type = line[6:].strip()

            if not data_lines:
                continue

            for data_str in data_lines:
                try:
                    message = json.loads(data_str)
                    if message.get("id") == request_id:
                        return message
                except json.JSONDecodeError:
                    continue

        raise MCPError(-1, f"No matching response found in SSE stream from '{self.config.name}' (id={request_id})")

    def is_running(self) -> bool:
        """Check if the HTTP client is connected."""
        return self.client is not None and not self.client.is_closed


# ── MCPClient — the main client orchestrator ────────────────────────────────

class MCPClient:
    """MCP Client that connects to MCP servers, discovers tools,
    and registers them in JEBAT's tool registry.

    Usage:
        client = MCPClient()
        await client.start_all()       # connects to all configured servers
        # ... tools are now in TOOL_REGISTRY ...
        await client.stop_all()        # cleanup
    """

    def __init__(self, config: Optional[JebatConfig] = None):
        """Initialize MCPClient. Loads config from ~/.jebat/config.yaml
        if not provided.
        """
        self.config = config or load_config()
        self._servers: Dict[str, MCPServerConfig] = {}
        self._transports: Dict[str, StdioTransport | HTTPTransport] = {}
        self._server_info: Dict[str, Dict[str, Any]] = {}
        self._discovered_tools: Dict[str, List[MCPToolInfo]] = {}
        self._discovered_resources: Dict[str, List[MCPResourceInfo]] = {}
        self._registered_tool_names: Dict[str, List[str]] = {}  # server_name -> [jebat_tool_names]
        self._started = False

        self._load_server_configs()

    # ── Config Loading ─────────────────────────────────────────────────────

    def _load_server_configs(self) -> None:
        """Load MCP server configs from the 'mcp' key in JEBAT config."""
        mcp_config = self.config.get("mcp", {})
        if not mcp_config:
            logger.info("No MCP servers configured")
            return

        servers = mcp_config.get("servers", [])
        if isinstance(mcp_config, dict) and "servers" not in mcp_config:
            # Allow flat dict where each key is a server name
            servers = []
            for name, srv in mcp_config.items():
                if isinstance(srv, dict):
                    srv_copy = dict(srv)
                    srv_copy["name"] = name
                    servers.append(srv_copy)

        for srv in servers:
            try:
                server_cfg = self._parse_server_config(srv)
                if server_cfg.enabled:
                    self._servers[server_cfg.name] = server_cfg
                    logger.info(f"Loaded MCP server config: {server_cfg.name} ({server_cfg.transport.value})")
            except Exception as e:
                logger.error(f"Failed to parse MCP server config: {e}")

    def _parse_server_config(self, raw: Dict[str, Any]) -> MCPServerConfig:
        """Parse a raw config dict into a MCPServerConfig."""
        transport_str = raw.get("transport", "stdio").lower()
        transport = TransportType(transport_str)

        env_overrides = raw.get("env", {})
        # Expand env values that reference os.environ (e.g. "${HOME}")
        resolved_env = {}
        for k, v in env_overrides.items():
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                env_key = v[2:-1]
                resolved_env[k] = os.environ.get(env_key, "")
            else:
                resolved_env[k] = str(v)

        return MCPServerConfig(
            name=raw.get("name", "unnamed"),
            transport=transport,
            command=raw.get("command", ""),
            args=raw.get("args", []),
            env=resolved_env,
            url=raw.get("url", ""),
            headers=raw.get("headers", {}),
            enabled=raw.get("enabled", True),
            timeout=raw.get("timeout", 30),
        )

    # ── Lifecycle Management ───────────────────────────────────────────────

    async def start_all(self) -> None:
        """Connect to all configured MCP servers, initialize them,
        discover tools, and register them in JEBAT's tool registry.
        """
        if self._started:
            logger.warning("MCPClient already started")
            return

        self._started = True

        for name, cfg in self._servers.items():
            try:
                await self.start_server(name)
            except Exception as e:
                logger.error(f"Failed to start MCP server '{name}': {e}")

    async def start_server(self, name: str) -> None:
        """Start a single MCP server, perform handshake, discover tools."""
        cfg = self._servers.get(name)
        if cfg is None:
            raise ValueError(f"Unknown MCP server: {name}")

        # Create and start transport
        transport = self._create_transport(cfg)
        await transport.start()
        self._transports[name] = transport

        # MCP handshake: initialize
        init_result = await self._initialize(name)

        # Discover tools
        await self._discover_tools(name)

        # Discover resources
        try:
            await self._discover_resources(name)
        except Exception as e:
            logger.warning(f"Failed to discover resources from '{name}': {e}")

        logger.info(f"MCP server '{name}' started and tools registered")

    async def stop_all(self) -> None:
        """Disconnect from all MCP servers and clean up."""
        for name in list(self._transports.keys()):
            try:
                await self.stop_server(name)
            except Exception as e:
                logger.error(f"Error stopping MCP server '{name}': {e}")

        # Unregister all MCP tools from JEBAT registry
        for name, tool_names in self._registered_tool_names.items():
            for tn in tool_names:
                if tn in TOOL_REGISTRY:
                    del TOOL_REGISTRY[tn]
                    logger.info(f"Unregistered MCP tool '{tn}'")

        self._registered_tool_names.clear()
        self._started = False

    async def stop_server(self, name: str) -> None:
        """Stop a single MCP server and unregister its tools."""
        transport = self._transports.get(name)
        if transport is None:
            return

        await transport.stop()
        del self._transports[name]

        # Unregister this server's tools
        tool_names = self._registered_tool_names.pop(name, [])
        for tn in tool_names:
            if tn in TOOL_REGISTRY:
                del TOOL_REGISTRY[tn]
                logger.info(f"Unregistered MCP tool '{tn}'")

    def _create_transport(self, cfg: MCPServerConfig) -> StdioTransport | HTTPTransport:
        """Create the appropriate transport for the given config."""
        if cfg.transport == TransportType.STDIO:
            return StdioTransport(cfg)
        elif cfg.transport == TransportType.HTTP:
            return HTTPTransport(cfg)
        else:
            raise ValueError(f"Unsupported transport type: {cfg.transport}")

    # ── MCP Protocol: Initialize ───────────────────────────────────────────

    async def _initialize(self, server_name: str) -> Dict[str, Any]:
        """Perform the MCP initialize handshake.

        Sends an 'initialize' request with client capabilities, then
        sends 'initialized' notification once the server responds.
        """
        transport = self._transports[server_name]

        request = _make_request("initialize", {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {},
                "resources": {},
            },
            "clientInfo": {
                "name": "jebat-cli",
                "version": "1.0.0",
            },
        })

        response = await transport.send_request(request)
        result = _extract_result(response)

        self._server_info[server_name] = result

        logger.info(f"Initialized MCP server '{server_name}': "
                     f"protocol={result.get('protocolVersion')}, "
                     f"server={result.get('serverInfo', {}).get('name', 'unknown')}")

        # Send initialized notification
        notification = _make_notification("notifications/initialized")
        await transport.send_request(notification)

        return result

    # ── MCP Protocol: List Tools ───────────────────────────────────────────

    async def _discover_tools(self, server_name: str) -> List[MCPToolInfo]:
        """List tools from the MCP server and register them in JEBAT."""
        transport = self._transports[server_name]

        request = _make_request("tools/list")
        response = await transport.send_request(request)
        result = _extract_result(response)

        tools_data = result.get("tools", [])
        discovered = []

        for tool_data in tools_data:
            tool_info = MCPToolInfo(
                name=tool_data.get("name", ""),
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {"type": "object", "properties": {}}),
            )
            discovered.append(tool_info)

            # Register in JEBAT tool registry
            jebat_tool_name = f"mcp_{server_name}_{tool_info.name}"
            handler = self._make_tool_handler(server_name, tool_info.name)

            register_tool(
                jebat_tool_name,
                handler=handler,
                schema=tool_info.input_schema,
                safety_tier="auto",
                timeout=self._servers[server_name].timeout,
                max_output=100_000,
                description=f"[MCP:{server_name}] {tool_info.description}",
            )

            self._registered_tool_names.setdefault(server_name, []).append(jebat_tool_name)
            logger.info(f"Registered MCP tool: {jebat_tool_name}")

        self._discovered_tools[server_name] = discovered
        return discovered

    def _make_tool_handler(self, server_name: str, mcp_tool_name: str) -> Callable[..., Coroutine[Any, Any, Any]]:
        """Create an async handler that routes tool calls through MCP.

        The handler accepts **kwargs matching the tool's input schema
        and forwards them as a tools/call request to the MCP server.
        """
        async def handler(**kwargs: Any) -> Any:
            transport = self._transports.get(server_name)
            if transport is None:
                raise MCPError(-1, f"MCP server '{server_name}' is not connected")

            request = _make_request("tools/call", {
                "name": mcp_tool_name,
                "arguments": kwargs,
            })

            response = await transport.send_request(request)
            result = _extract_result(response)

            # MCP tools/call result has 'content' array
            content = result.get("content", [])
            if isinstance(content, list):
                # Concatenate text items; return structured content if mixed
                text_parts = []
                for item in content:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "image":
                        # Return image data as-is for callers that can handle it
                        return content
                    elif item.get("type") == "resource":
                        return content

                if text_parts:
                    return "\n".join(text_parts)
                return content

            # Fallback: return raw result
            return result

        # Give the handler a readable name for debugging
        handler.__name__ = f"mcp_handler_{server_name}_{mcp_tool_name}"
        handler.__doc__ = f"MCP tool '{mcp_tool_name}' from server '{server_name}'"

        return handler

    # ── MCP Protocol: Call Tool ────────────────────────────────────────────

    async def call_tool(self, server_name: str, tool_name: str,
                        arguments: Dict[str, Any]) -> Any:
        """Call a tool on an MCP server directly (bypassing JEBAT registry).

        Useful for testing or when you need the raw MCP response.
        """
        transport = self._transports.get(server_name)
        if transport is None:
            raise MCPError(-1, f"MCP server '{server_name}' is not connected")

        request = _make_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })

        response = await transport.send_request(request)
        return _extract_result(response)

    # ── MCP Protocol: List Resources ───────────────────────────────────────

    async def _discover_resources(self, server_name: str) -> List[MCPResourceInfo]:
        """List resources from the MCP server."""
        transport = self._transports[server_name]

        request = _make_request("resources/list")
        response = await transport.send_request(request)
        result = _extract_result(response)

        resources_data = result.get("resources", [])
        discovered = []

        for res_data in resources_data:
            res_info = MCPResourceInfo(
                uri=res_data.get("uri", ""),
                name=res_data.get("name", ""),
                description=res_data.get("description", ""),
                mime_type=res_data.get("mimeType", ""),
            )
            discovered.append(res_info)

        self._discovered_resources[server_name] = discovered
        logger.info(f"Discovered {len(discovered)} resources from '{server_name}'")
        return discovered

    async def read_resource(self, server_name: str, uri: str) -> Any:
        """Read a resource from an MCP server."""
        transport = self._transports.get(server_name)
        if transport is None:
            raise MCPError(-1, f"MCP server '{server_name}' is not connected")

        request = _make_request("resources/read", {"uri": uri})
        response = await transport.send_request(request)
        return _extract_result(response)

    # ── Status ──────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get status of all MCP server connections."""
        status = {}
        for name, cfg in self._servers.items():
            transport = self._transports.get(name)
            is_connected = transport is not None and transport.is_running()
            status[name] = {
                "transport": cfg.transport.value,
                "connected": is_connected,
                "tools_discovered": len(self._discovered_tools.get(name, [])),
                "resources_discovered": len(self._discovered_resources.get(name, [])),
                "tools_registered": len(self._registered_tool_names.get(name, [])),
                "server_info": self._server_info.get(name, {}),
            }
        return status

    def list_discovered_tools(self, server_name: Optional[str] = None) -> List[MCPToolInfo]:
        """List all discovered MCP tools, optionally filtered by server."""
        if server_name:
            return self._discovered_tools.get(server_name, [])
        all_tools = []
        for tools in self._discovered_tools.values():
            all_tools.extend(tools)
        return all_tools

    def list_discovered_resources(self, server_name: Optional[str] = None) -> List[MCPResourceInfo]:
        """List all discovered MCP resources, optionally filtered by server."""
        if server_name:
            return self._discovered_resources.get(server_name, [])
        all_resources = []
        for resources in self._discovered_resources.values():
            all_resources.extend(resources)
        return all_resources
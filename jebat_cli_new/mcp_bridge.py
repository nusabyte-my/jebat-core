"""MCP bridge for the CLI agent — call configured MCP servers as native tools.

Turns any server registered under ``mcp:`` in ``~/.jebat/config.yaml`` (or the
file named by ``JEBAT_MCP_CONFIG``) into two agent-loop tools:

- ``mcp_describe``  -> tools/list (+resources/list) for one server
- ``mcp_call``      -> tools/call on one server (server, tool, arguments)

Transports and wire protocol come from ``jebat.features.mcp.mcp_client``
(StdioTransport / HTTPTransport / request helpers) so the CLI speaks the same
MCP revision as the server side. This module adds only what the CLI needs:
config resolution with an env override, a one-shot session per operation, and
text extraction for the ReAct loop.

Servers can opt into a per-call approval gate with ``"require_approval": true``
in their config entry; otherwise ``mcp_call`` runs free like ``read_file`` —
the solution's ``llm_tools`` allowlist is the boundary (``mcp_describe`` is
always read-only).
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_CONFIG_PATH = Path.home() / ".jebat" / "config.yaml"


class MCPBridgeError(Exception):
    """User-facing bridge error (unknown server, transport failure, ...)."""


# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------


def config_path() -> Path:
    override = os.environ.get("JEBAT_MCP_CONFIG", "").strip()
    return Path(override) if override else DEFAULT_CONFIG_PATH


def _load_mcp_section() -> Dict[str, Dict[str, Any]]:
    import yaml

    path = config_path()
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 — surface as bridge error
        raise MCPBridgeError(f"cannot read {path}: {exc}")
    mcp = data.get("mcp") or {}
    if not isinstance(mcp, dict):
        return {}
    servers: Dict[str, Dict[str, Any]] = {}
    entries = mcp.get("servers")
    if isinstance(entries, dict):  # mcp.servers.<name> form
        for name, raw in entries.items():
            servers[str(name)] = dict(raw or {}, name=str(name))
    elif isinstance(entries, list):  # mcp.servers: [ {name: ...}, ... ]
        for raw in entries:
            raw = dict(raw or {})
            servers[str(raw.get("name") or f"server-{len(servers)}")] = raw
    else:  # flat form: mcp.<name> = {...}
        for name, raw in mcp.items():
            if isinstance(raw, dict):
                servers[str(name)] = dict(raw, name=str(name))
    return servers


def list_servers(include_disabled: bool = True) -> List[Dict[str, Any]]:
    """Describe the configured MCP servers (no connections made)."""
    out = []
    for name, raw in sorted(_load_mcp_section().items()):
        enabled = bool(raw.get("enabled", True))
        if not enabled and not include_disabled:
            continue
        command = " ".join(
            [str(raw.get("command", ""))] + [str(a) for a in raw.get("args", [])]
        ).strip()
        out.append(
            {
                "name": name,
                "transport": str(raw.get("transport", "stdio")),
                "enabled": enabled,
                "command": command or None,
                "url": raw.get("url") or None,
                "timeout": raw.get("timeout", 30),
                "require_approval": bool(raw.get("require_approval", False)),
            }
        )
    return out


def server_requires_approval(name: str) -> bool:
    """True when the server's config entry opts into per-call approval."""
    try:
        raw = _load_mcp_section().get(str(name)) or {}
    except MCPBridgeError:
        return False
    return bool(raw.get("require_approval", False))


def _server_config(name: str):
    """Build an MCPServerConfig for `name` (env refs expanded like the canonical parser)."""
    from jebat.features.mcp.mcp_client import MCPServerConfig, TransportType

    servers = _load_mcp_section()
    raw = servers.get(name)
    if raw is None:
        known = ", ".join(sorted(servers)) or "(none configured)"
        raise MCPBridgeError(f"unknown MCP server {name!r} — configured: {known}")
    if not bool(raw.get("enabled", True)):
        raise MCPBridgeError(f"MCP server {name!r} is disabled in {config_path()}")
    env: Dict[str, str] = {}
    for key, value in (raw.get("env") or {}).items():
        value = str(value)
        if value.startswith("${") and value.endswith("}"):
            value = os.environ.get(value[2:-1], "")
        env[key] = value
    return MCPServerConfig(
        name=name,
        transport=TransportType(str(raw.get("transport", "stdio")).lower()),
        command=str(raw.get("command", "")),
        args=[str(a) for a in raw.get("args", [])],
        env=env,
        url=str(raw.get("url", "")),
        headers=dict(raw.get("headers") or {}),
        enabled=True,
        timeout=int(raw.get("timeout", 30)),
    )


# ---------------------------------------------------------------------------
# Session (one-shot start -> initialize -> use -> stop)
# ---------------------------------------------------------------------------


class _Session:
    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.transport = None
        self.server_info: Dict[str, Any] = {}

    async def __aenter__(self) -> "_Session":
        from jebat.features.mcp.mcp_client import (
            CLIENT_NAME,
            CLIENT_VERSION,
            HTTPTransport,
            MCP_PROTOCOL_VERSION,
            StdioTransport,
            TransportType,
            _extract_result,
            _make_notification,
            _make_request,
        )

        if self.cfg.transport == TransportType.STDIO:
            if not self.cfg.command:
                raise MCPBridgeError(f"stdio server {self.cfg.name!r} has no command")
            self.transport = StdioTransport(self.cfg)
        else:
            self.transport = HTTPTransport(self.cfg)
        await self.transport.start()
        response = await self.transport.send_request(
            _make_request(
                "initialize",
                {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {"tools": {}, "resources": {}},
                    "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
                },
            )
        )
        self.server_info = _extract_result(response) or {}
        await self.transport.send_request(_make_notification("notifications/initialized"))
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self.transport is not None:
            try:
                await self.transport.stop()
            except Exception:  # noqa: BLE001 — teardown must not mask results
                pass

    async def request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        from jebat.features.mcp.mcp_client import _extract_result, _make_request

        assert self.transport is not None, "session not entered"
        response = await self.transport.send_request(_make_request(method, params))
        return _extract_result(response)


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def _extract_text(result: Dict[str, Any]) -> str:
    parts: List[str] = []
    for item in result.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
            parts.append(str(item["text"]))
    if not parts and result.get("structuredContent") is not None:
        parts.append(json.dumps(result["structuredContent"], ensure_ascii=False))
    text = "\n".join(parts).strip()
    return text or json.dumps(result, ensure_ascii=False)[:2000]


async def _describe_async(server: str) -> Dict[str, Any]:
    cfg = _server_config(server)
    async with _Session(cfg) as session:
        result = await session.request("tools/list", {})
        tools = []
        for tool in result.get("tools") or []:
            if not isinstance(tool, dict):
                continue
            schema = tool.get("inputSchema") or {}
            annotations = tool.get("annotations") or {}
            tools.append(
                {
                    "name": tool.get("name"),
                    "description": (tool.get("description") or "").strip(),
                    "required": list(schema.get("required") or []),
                    "read_only_hint": annotations.get("readOnlyHint"),
                }
            )
        resources: List[str] = []
        try:
            res = await session.request("resources/list", {})
            resources = [str(item.get("uri")) for item in (res.get("resources") or [])][:50]
        except Exception:  # noqa: BLE001 — server may not support resources
            pass
        return {
            "server": server,
            "protocol": session.server_info.get("protocolVersion"),
            "server_info": session.server_info.get("serverInfo"),
            "tool_count": len(tools),
            "tools": tools,
            "resources": resources,
        }


async def _call_async(server: str, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _server_config(server)
    async with _Session(cfg) as session:
        result = await session.request(
            "tools/call", {"name": tool, "arguments": arguments or {}}
        )
        return {
            "server": server,
            "tool": tool,
            "is_error": bool(result.get("isError", False)),
            "text": _extract_text(result),
        }


# ---------------------------------------------------------------------------
# Sync facade + tool handlers
# ---------------------------------------------------------------------------


def _run_sync(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # Already inside a loop (e.g. an async host calling the sync handler):
    # run the coroutine on its own loop in a worker thread.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def describe_server(server: str) -> Dict[str, Any]:
    return _run_sync(_describe_async(server))


def call_tool(server: str, tool: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _run_sync(_call_async(server, tool, arguments or {}))


def handle_mcp_describe(args: Dict[str, Any]) -> str:
    server = str(args.get("server") or "").strip()
    if not server:
        return "[MCP_ERROR] server is required (configured: " + (
            ", ".join(s["name"] for s in list_servers()) or "none"
        ) + ")"
    try:
        result = describe_server(server)
    except MCPBridgeError as exc:
        return f"[MCP_ERROR] {exc}"
    except Exception as exc:  # noqa: BLE001 — report, don't kill the loop
        return f"[MCP_ERROR] {type(exc).__name__}: {exc}"
    return json.dumps(result, ensure_ascii=False, indent=2)[:20000]


def handle_mcp_call(args: Dict[str, Any]) -> str:
    server = str(args.get("server") or "").strip()
    tool = str(args.get("tool") or "").strip()
    arguments = args.get("arguments") or {}
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments or "{}")
        except json.JSONDecodeError as exc:
            return f"[MCP_ERROR] arguments is not valid JSON: {exc}"
    if not server or not tool:
        return "[MCP_ERROR] server and tool are required"
    if not isinstance(arguments, dict):
        return "[MCP_ERROR] arguments must be a JSON object"
    try:
        out = call_tool(server, tool, arguments)
    except MCPBridgeError as exc:
        return f"[MCP_ERROR] {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"[MCP_ERROR] {type(exc).__name__}: {exc}"
    return (
        f"[mcp {server}/{tool}] is_error={out['is_error']}\n{out['text']}"
    )

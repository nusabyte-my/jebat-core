"""MCP (Model Context Protocol) SERVER for JEBAT CLI Agent.

Makes JEBAT a tool PROVIDER that IDEs (VS Code, Cursor, Windsurf, JetBrains)
connect TO via the MCP protocol. The server exposes all registered JEBAT tools
as MCP tools with proper JSON Schema input definitions, and dispatches
incoming tool calls to the JEBAT tool registry.

Transport: stdio (JSON-RPC 2.0 messages, one per line, over stdin/stdout)
           HTTP (SSE + StreamableHTTP, for remote IDE connections)

Protocol versions: 2024-11-05, 2025-03-26, 2025-06-18

Usage:
    # Start MCP server (IDE connects via stdio)
    jebat mcp serve

    # Start MCP server on HTTP port
    jebat mcp serve --transport http --port 8099
"""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import os
import sys
import traceback
import subprocess
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from jebat.tools import TOOL_REGISTRY, ToolDef, call_tool, classify_tool_call
from .mcp_prompts import PromptInputError

logger = logging.getLogger(__name__)

# ── Constants (single source: jebat.features.mcp.protocol) ─────────────────

from .protocol import (
    JSONRPC_VERSION,
    MCP_PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    SUPPORTED_PROTOCOL_VERSIONS,
)


# ── Tracking & Severity ──────────────────────────────────────────────────────

_RECENT_ERRORS: "deque[Dict[str, Any]]" = deque(maxlen=50)
_TOOL_CALL_COUNTS: Dict[str, int] = {}
_TOOL_ERROR_COUNTS: Dict[str, int] = {}
# Per-tool latency ring for p50/p95 (ms). Bounded so the metrics resource
# stays cheap no matter how long the server runs.
_TOOL_LATENCIES: Dict[str, "deque[float]"] = {}
_TOOL_LATENCY_RING = 200


def _record_tool_latency(tool_name: str, duration_ms: float) -> None:
    ring = _TOOL_LATENCIES.setdefault(tool_name, deque(maxlen=_TOOL_LATENCY_RING))
    ring.append(duration_ms)


def _percentile(ring: "deque[float]", pct: float) -> float:
    if not ring:
        return 0.0
    ordered = sorted(ring)
    idx = min(len(ordered) - 1, max(0, round(pct * (len(ordered) - 1))))
    return ordered[idx]


def _build_metrics_json() -> str:
    tools = []
    for name in sorted(_TOOL_CALL_COUNTS):
        ring = _TOOL_LATENCIES.get(name)
        tools.append({
            "tool": name,
            "calls": _TOOL_CALL_COUNTS[name],
            "errors": _TOOL_ERROR_COUNTS.get(name, 0),
            "latency_ms": {
                "p50": round(_percentile(ring, 0.50), 1),
                "p95": round(_percentile(ring, 0.95), 1),
            },
        })
    payload = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tools": tools,
        "recentErrors": list(_RECENT_ERRORS)[-10:],
    }
    return mcp_json(payload)


def _record_tool_error(tool_name: str, error: str, arguments: Dict, kind: str = "execution") -> None:
    """Append a tool error to the bounded recent-errors ring (F3)."""
    _TOOL_ERROR_COUNTS[tool_name] = _TOOL_ERROR_COUNTS.get(tool_name, 0) + 1
    _RECENT_ERRORS.append({
        "tool": tool_name,
        "error": error,
        "kind": kind,
        "timestamp": time.time(),
        "arguments": arguments,
    })

LOG_LEVEL_SEVERITY: Dict[str, int] = {
    "debug": 10,
    "info": 20,
    "notice": 25,
    "warning": 30,
    "error": 40,
    "critical": 50,
    "alert": 60,
    "emergency": 70,
}

# ── Token Economy & Terse Mode ───────────────────────────────────────────────

def mcp_json(obj: Any) -> str:
    """Serialize an MCP payload without whitespace — JSON is machine-read, indent is pure token waste."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, default=str)


MCP_MAX_RESULT_CHARS = int(os.getenv("JEBAT_MCP_MAX_RESULT_CHARS", "12000"))
_ARTIFACTS: Dict[str, str] = {}


def _cap_result(text: str, tool_name: str) -> tuple[str, bool]:
    """Cap large tool results using head + tail folding and store the full result in _ARTIFACTS."""
    if len(text) <= MCP_MAX_RESULT_CHARS:
        return (text, False)

    head_chars = int(MCP_MAX_RESULT_CHARS * 0.6)
    tail_chars = int(MCP_MAX_RESULT_CHARS * 0.3)
    head = text[:head_chars]
    tail = text[len(text) - tail_chars:] if tail_chars > 0 else ""
    omitted = len(text) - (len(head) + len(tail))

    artifact_id = uuid.uuid4().hex[:8]
    _ARTIFACTS[artifact_id] = text
    while len(_ARTIFACTS) > 20:
        oldest_key = next(iter(_ARTIFACTS))
        _ARTIFACTS.pop(oldest_key, None)

    folded = (
        f"{head}\n\n"
        f"…[TRUNCATED: {omitted} of {len(text)} chars. Full result: jebat://artifact/{artifact_id}]\n\n"
        f"{tail}"
    )
    return (folded, True)


MCP_TOOLS_PAGE_SIZE = int(os.getenv("JEBAT_MCP_TOOLS_PAGE", "0"))
_TOOLS_CACHE: Dict[tuple, Dict[str, Any]] = {}


_TOOLS_ALLOW_MEMO: Dict[str, Optional[set]] = {}


# ── Skills / wiki resource indexes (extracted to mcp_resources.py) ─────────
# Index builders + TTL caches live in mcp_resources.py; the JSON-RPC handlers
# below consume them. Names re-exported here keep existing import paths stable.
from jebat.features.mcp.mcp_resources import (  # noqa: E402,F401
    _skill_index,
    _skill_meta,
    _skill_roots,
    _wiki_index,
    _wiki_meta,
    _wiki_roots,
)


def _allowed_tools() -> Optional[set]:
    """Return the JEBAT_MCP_TOOLS_ALLOW allowlist, or None when unrestricted.

    The env var is a comma-separated list of tool names (set it from a
    client's mcp.json ``env`` block to trim tools/list). Whitespace around
    names is ignored; empty or unset exposes the full registry so existing
    IDE configs keep every tool unless they opt in. Memoized per raw env
    value — this sits on the tools/call hot path and os.getenv + split
    per request is wasted work when the value never changes.
    """
    raw = os.getenv("JEBAT_MCP_TOOLS_ALLOW", "")
    if raw in _TOOLS_ALLOW_MEMO:
        return _TOOLS_ALLOW_MEMO[raw]
    names = {name.strip() for name in raw.split(",") if name.strip()}
    result: Optional[set] = names or None
    _TOOLS_ALLOW_MEMO[raw] = result
    return result


_TERSE_CLIENT_NAME: str = ""


def mcp_terse_mode() -> bool:
    """Terse mode strips optional MCP fields — the IDE context window is the budget."""
    if os.getenv("JEBAT_MCP_TERSE", "").lower() in ("1", "true", "yes"):
        return True
    if "terse" in _TERSE_CLIENT_NAME.lower():
        return True
    info = getattr(MCPServer, "_client_info_name", "") or ""
    return "terse" in str(info).lower()

# ── Data Structures ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MCPCapabilities:
    """Server capabilities announced during initialization."""
    tools: bool = True
    resources: bool = True
    prompts: bool = True
    logging: bool = True
    roots: bool = True
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

def build_tool_schema(tool_def: ToolDef, terse: bool = False) -> Dict[str, Any]:
    """Convert a JEBAT ToolDef into an MCP tool definition with JSON Schema."""
    schema = tool_def.schema or {"type": "object", "properties": {}}
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    input_schema = {
        "type": "object",
        "properties": properties,
    }
    if required:
        input_schema["required"] = required

    desc = tool_def.description or f"JEBAT tool: {tool_def.name}"
    if terse:
        parts = desc.split(". ")
        first_sentence = parts[0]
        if len(parts) > 1 and not first_sentence.endswith("."):
            first_sentence += "."
        if len(first_sentence) > 160:
            first_sentence = first_sentence[:157] + "..."
        desc = first_sentence

    name_lower = tool_def.name.lower()
    readonly_kws = ("read", "list", "search", "get", "schema", "status", "recall", "dream", "info", "stats")
    destructive_kws = ("delete", "drop", "forget", "clear", "write", "execute_code", "terminal")
    idempotent_kws = ("read", "list", "get", "search", "schema", "info", "stats")
    openworld_kws = ("search_web", "web_extract", "pentest", "browser")

    if terse:
        annotations = {
            "readOnlyHint": any(k in name_lower for k in readonly_kws),
            "destructiveHint": any(k in name_lower for k in destructive_kws) or (tool_def.safety_tier == "dangerous"),
        }
    else:
        annotations = {
            "readOnlyHint": any(k in name_lower for k in readonly_kws),
            "destructiveHint": any(k in name_lower for k in destructive_kws) or (tool_def.safety_tier == "dangerous"),
            "idempotentHint": any(k in name_lower for k in idempotent_kws),
            "openWorldHint": any(k in name_lower for k in openworld_kws),
        }

    res = {
        "name": tool_def.name,
        "description": desc,
        "inputSchema": input_schema,
        "annotations": annotations,
    }
    if tool_def.safety_tier and tool_def.safety_tier != "auto":
        res["_meta"] = {"jebat/safetyTier": tool_def.safety_tier}
    return res


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

    _client_info_name: str = ""

    def __init__(self, transport: TransportMode = TransportMode.STDIO,
                 http_port: int = 8099, host: str = "127.0.0.1"):
        self.transport = transport
        self.http_port = http_port
        self.host = host
        self.capabilities = MCPCapabilities()
        self.client_info: Dict[str, Any] = {}
        self._client_info_name: str = ""
        self._initialized = False
        self._tools_loaded = False
        self._tools_cache: Dict[tuple, Dict[str, Any]] = {}
        self._last_terse_mode: Optional[bool] = None
        self._log_level: str = "info"
        self._pending_notifications: List[Dict[str, Any]] = []
        self._request_handlers: Dict[str, Any] = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_tools_list,
            "tools/describe": self._handle_tools_describe,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
            "roots/list": self._handle_roots_list,
            "ping": self._handle_ping,
            "logging/setLevel": self._handle_logging_set_level,
            "completion/complete": self._handle_completion,
        }

    def _send_notification(self, payload: Dict[str, Any]) -> None:
        """Send a JSON-RPC notification via stdout (stdio) or queue (http)."""
        if payload.get("method") == "notifications/message":
            params = payload.get("params") or {}
            msg_level = str(params.get("level", "info")).lower()
            client_sev = LOG_LEVEL_SEVERITY.get(self._log_level.lower(), 20)
            msg_sev = LOG_LEVEL_SEVERITY.get(msg_level, 20)
            if msg_sev < client_sev:
                return

        pm = getattr(self, "_progress_manager", None)
        if self.transport == TransportMode.STDIO:
            sys.stdout.write(json.dumps(payload) + "\n")
            sys.stdout.flush()
        elif pm and getattr(pm, "_queue", None):
            pm._queue.put_nowait(payload)

    def _flush_pending_notifications(self) -> None:
        """Send all queued server-initiated notifications."""
        while self._pending_notifications:
            notif = self._pending_notifications.pop(0)
            self._send_notification(notif)

    def _log(self, level: str, data: Any, logger_name: Optional[str] = None) -> None:
        """Send a notifications/message notification with level and data fields."""
        params: Dict[str, Any] = {
            "level": level,
            "data": data,
        }
        if logger_name:
            params["logger"] = logger_name

        payload = {
            "jsonrpc": JSONRPC_VERSION,
            "method": "notifications/message",
            "params": params,
        }
        self._send_notification(payload)
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
        # Stateless: v2026-07-28 removes the initialization requirement.
        # For older protocols, we still enforce the init-first handshake.
        # Auto-initialize on first non-init request for stateless clients.
        if method != "initialize" and not self._initialized:
            # Auto-init for stateless protocol — treat server as always ready
            self._initialized = True
            logger.info("MCP server auto-initialized (stateless mode)")

        # Flush any pending notifications on message dispatch
        self._flush_pending_notifications()

        # Dispatch to handler
        handler = self._request_handlers.get(method)
        if handler is None:
            return make_error(request_id, MCPError.METHOD_NOT_FOUND,
                              f"Method not found: {method}")

        try:
            result = await handler(params)
            return make_response(request_id, result)
        except PromptInputError as e:
            return make_error(request_id, MCPError.INVALID_PARAMS, str(e))
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

        self._client_info_name = client_name
        MCPServer._client_info_name = client_name
        global _TERSE_CLIENT_NAME
        _TERSE_CLIENT_NAME = client_name

        logger.info(f"MCP client connecting: {client_name} v{client_version}")
        self._initialized = True

        requested_version = params.get("protocolVersion")
        protocol_version = (
            requested_version
            if requested_version in SUPPORTED_PROTOCOL_VERSIONS
            else MCP_PROTOCOL_VERSION
        )

        capabilities = {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True},
            "prompts": {"listChanged": True},
            "logging": {},
            "roots": {"listChanged": True},
            "experimental": self.capabilities.experimental,
        }

        # Queue advisorReady notification to be sent after initialize response
        try:
            await self._send_advisor_notification()
        except Exception as e:
            logger.warning(f"Failed to prepare advisor notification: {e}")

        return {
            "protocolVersion": protocol_version,
            "capabilities": capabilities,
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        }

    async def _send_advisor_notification(self) -> None:
        """Send project-scoped evidence and persistent advice without model inference."""
        try:
            from jebat.tools.automimpi_tools import _get_automimpi, _get_selflearn, _get_learning_advisor

            root = str(Path.cwd().resolve())
            analysis = _get_selflearn().analyze(Path.cwd().name, root)
            advisor = _get_learning_advisor()
            advice = await asyncio.to_thread(advisor.advise, "", 3, analysis)
            engine = _get_automimpi()
            self._pending_notifications.append({
                "jsonrpc": JSONRPC_VERSION, "method": "notifications/advisorReady",
                "params": {"project_root": root, "healthScore": analysis["retention_health"]["avg_strength"],
                           "metricBasis": analysis["metric_basis"], "suggestions": advice["recommendations"],
                           "staleMemories": analysis["evidence"]["stale"]["count"],
                           "lastDream": engine.last_dream_at.isoformat() if engine.last_dream_at else None,
                           "kb": advice["kb"]},
            })
        except Exception as exc:
            logger.warning("Learning advisor unavailable: %s", exc)

    def _ensure_tools_loaded(self) -> None:
        """Import all JEBAT tool modules to populate TOOL_REGISTRY.

        Each import is wrapped individually so one missing dependency
        doesn't block the rest — the server stays up with a partial
        tool set and logs which modules couldn't load.
        """
        if self._tools_loaded:
            return

        _tool_modules = [
            ("fileops", "jebat.features.fileops"),
            ("terminal", "jebat.features.terminal"),
            ("browser", "jebat.features.browser"),
            ("vision", "jebat.features.vision"),
            ("web_search", "jebat.features.search"),
            ("auth", "jebat.features.auth"),
            ("cron", "jebat.features.cron"),
            ("wiki", "jebat.features.wiki"),
            ("image_gen", "jebat.features.image_gen"),
            ("pentest", "jebat.features.pentest.pentest_tools"),
            # Memory + learning (project memory, dream cycle, self-learning)
            ("memory", "jebat.tools.memory_tools"),
            ("automimpi", "jebat.tools.automimpi_tools"),
            ("skills", "jebat.tools.skill_tools"),
            ("todo", "jebat.tools.todo_tools"),
            ("session", "jebat.tools.session_search_tools"),
            ("execute_code", "jebat.tools.execute_code"),
            # Ghost DB & ephemeral database branching
            ("ghost", "jebat.features.ghost.ghost_tools"),
            # Autonomous multi-turn ReAct agent harness
            ("agent_exec", "jebat.tools.agent_tools"),
            # Design & UI/UX (Pawang Estetika)
            ("design_tools", "jebat.tools.design_tools"),
            ("design_reference", "jebat.tools.design_reference_tools"),
            # Copywriting & Conversion (Pawang Jualan)
            ("copywriting_tools", "jebat.tools.copywriting_tools"),
            # Voyager-style Dynamic Tool Synthesis
            ("dynamic_synthesis", "jebat.tools.dynamic_synthesis"),
            # Advisor — Jev-style System One typed decisions (classify, verify, score)
            ("advisor_tools", "jebat.tools.advisor_tools"),
            # Marketing & SEO (Pawang Pemasaran — strategy + on-page/search visibility)
            ("seo", "jebat.tools.seo_tools"),
            ("marketing", "jebat.tools.marketing_tools"),
        ]
        _loaded = 0
        _failed = []
        for name, mod_path in _tool_modules:
            try:
                __import__(mod_path)
                _loaded += 1
            except Exception as e:
                _failed.append((name, str(e)))

        self._tools_loaded = True
        self._tools_cache.clear()
        _TOOLS_CACHE.clear()
        failed = ", ".join(f"{n}({e})" for n, e in _failed)
        if failed:
            logger.info(f"MCP loaded {_loaded}/{len(_tool_modules)} tool modules; skipped: {failed}")
        else:
            logger.info(f"MCP server loaded {_loaded} tool modules, {len(TOOL_REGISTRY)} tools")

    async def _handle_tools_list(self, params: Dict) -> Dict:
        """Return registered JEBAT tools as MCP tool definitions with pagination and caching."""
        self._ensure_tools_loaded()
        is_terse = mcp_terse_mode()

        # Invalidate cache if terse mode changed
        if getattr(self, "_last_terse_mode", None) != is_terse:
            self._tools_cache.clear()
            _TOOLS_CACHE.clear()
            self._last_terse_mode = is_terse

        cursor = params.get("cursor")
        offset = int(cursor) if cursor is not None and str(cursor).isdigit() else 0
        allowed = _allowed_tools()

        # Check page size from env or instance/constant
        page_size_env = os.getenv("JEBAT_MCP_TOOLS_PAGE")
        if page_size_env is not None:
            try:
                page_size = int(page_size_env)
            except ValueError:
                page_size = 0
        else:
            page_size = MCP_TOOLS_PAGE_SIZE

        # Allowlist participates in the cache key so toggling the env var
        # (or per-client configs sharing a process) never serves stale lists.
        cache_key = (offset, page_size, is_terse, frozenset(allowed) if allowed else None)
        if cache_key in self._tools_cache:
            return self._tools_cache[cache_key]

        tool_items = [
            (name, tool) for name, tool in TOOL_REGISTRY.items()
            if allowed is None or name in allowed
        ]
        total_tools = len(tool_items)

        if page_size > 0:
            paged_items = tool_items[offset : offset + page_size]
        else:
            paged_items = tool_items[offset:]

        tools = [build_tool_schema(tool_def, terse=is_terse) for _, tool_def in paged_items]

        res: Dict[str, Any] = {"tools": tools}
        if page_size > 0 and (offset + len(paged_items) < total_tools):
            res["nextCursor"] = str(offset + len(paged_items))

        self._tools_cache[cache_key] = res
        _TOOLS_CACHE[cache_key] = res
        return res

    async def _handle_tools_describe(self, params: Dict) -> Dict:
        """Return the full schema and description for a single tool (lazy-detail escape hatch)."""
        self._ensure_tools_loaded()
        tool_name = params.get("name", "")
        allowed = _allowed_tools()
        if tool_name not in TOOL_REGISTRY or (allowed is not None and tool_name not in allowed):
            return {
                "error": f"Tool not found: {tool_name}",
            }
        tool_def = TOOL_REGISTRY[tool_name]
        schema = build_tool_schema(tool_def, terse=False)
        return {
            "name": tool_name,
            "description": tool_def.description or f"JEBAT tool: {tool_def.name}",
            "tool": schema,
            "schema": schema,
        }

    async def _handle_tools_call(self, params: Dict) -> Dict:
        """Execute a tool call requested by the IDE."""
        self._ensure_tools_loaded()
        tool_name = params.get("name", "")
        arguments = params.get("arguments") or {}

        if tool_name:
            _TOOL_CALL_COUNTS[tool_name] = _TOOL_CALL_COUNTS.get(tool_name, 0) + 1
        allowed = _allowed_tools()
        if tool_name not in TOOL_REGISTRY or (allowed is not None and tool_name not in allowed):
            _record_tool_error(tool_name, f"Tool not found: {tool_name}", arguments, kind="not_found")
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Tool not found: {tool_name}"}],
            }

        # Safety metadata is returned instead of silently executing a write.
        safety_tier = classify_tool_call(tool_name, arguments)
        if safety_tier in ("confirm", "dangerous"):
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"Tool '{tool_name}' requires {safety_tier} approval. See structuredContent.",
                }],
                "structuredContent": {
                    "status": "approval_required",
                    "tool": tool_name,
                    "safetyTier": safety_tier,
                    "arguments": arguments,
                    "next": "Approve this exact call in JEBAT CLI, then retry it.",
                },
            }

        # Wire ProgressManager for long-running tools (MQ-4). A ContextVar
        # reporter lets inner loops (agent ReAct iterations, SQL batches)
        # push fractional progress without importing JSON-RPC details.
        progress_tools = ('agent_execute', 'ghost_sql', 'pentest_scan', 'advisor_decide')
        progress_token = None
        pm = None
        _reporter_token = None
        if tool_name in progress_tools:
            from jebat.features.mcp.mcp_transport import ProgressManager
            from jebat_cli_new.progress import PROGRESS_REPORTER
            if not hasattr(self, "_progress_manager") or self._progress_manager is None:
                self._progress_manager = ProgressManager()
            pm = self._progress_manager
            progress_token = pm.start(tool_name, total=1.0)
            start_payload = {
                "jsonrpc": JSONRPC_VERSION,
                "method": "notifications/progress",
                "params": {
                    "progressToken": progress_token,
                    "progress": 0.0,
                    "total": 1,
                },
            }
            self._send_notification(start_payload)

            def _on_inner_progress(frac: float, message: str = "") -> None:
                # ProgressManager.notify is queue-backed and thread-safe; the
                # 0.5 cap leaves room for the final completion pulse.
                pm.notify(progress_token, 0.05 + min(max(frac, 0.0), 1.0) * 0.9, message)

            _reporter_token = PROGRESS_REPORTER.set(_on_inner_progress)

        try:
            # Hard deadline per call: a hung tool (dead DB, stalled provider)
            # must not wedge the JSON-RPC request indefinitely. Uses the
            # tool's declared timeout (seconds) with a floor for slow tools.
            tool_def = TOOL_REGISTRY.get(tool_name)
            declared = getattr(tool_def, "timeout", None) if tool_def else None
            call_timeout = max(float(declared or 30), 5.0)
            if tool_name in ("agent_execute", "agi_execute", "ghost_sql", "pentest_scan"):
                call_timeout = max(call_timeout, 600.0)
            try:
                _t0 = time.perf_counter()
                result = await asyncio.wait_for(call_tool(tool_name, **arguments), timeout=call_timeout)
                _record_tool_latency(tool_name, (time.perf_counter() - _t0) * 1000.0)
            except asyncio.TimeoutError:
                _record_tool_latency(tool_name, (time.perf_counter() - _t0) * 1000.0)
                raise TimeoutError(
                    f"tool '{tool_name}' exceeded its {call_timeout:.0f}s execution deadline"
                )

            # Convert result to MCP content format
            if isinstance(result, str):
                text_out, _ = _cap_result(result, tool_name)
                content = [{"type": "text", "text": text_out}]
            elif isinstance(result, dict):
                # Try to serialize; if it has 'content' key in MCP format, use it
                if "content" in result and isinstance(result["content"], list):
                    content = []
                    for item in result["content"]:
                        if isinstance(item, dict) and item.get("type") == "text" and "text" in item:
                            capped_text, _ = _cap_result(str(item["text"]), tool_name)
                            content.append({**item, "text": capped_text})
                        else:
                            content.append(item)
                else:
                    text_out, _ = _cap_result(mcp_json(result), tool_name)
                    content = [{"type": "text", "text": text_out}]
            elif isinstance(result, list):
                text_out, _ = _cap_result(mcp_json(result), tool_name)
                content = [{"type": "text", "text": text_out}]
            else:
                text_out, _ = _cap_result(str(result), tool_name)
                content = [{"type": "text", "text": text_out}]

            return {"content": content}

        except TimeoutError as e:
            logger.error(f"Tool execution deadline exceeded for {tool_name}: {e}")
            _record_tool_error(tool_name, f"TimeoutError: {e}", arguments)
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"Tool execution error: {e}",
                }],
            }
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            _record_tool_error(tool_name, f"{type(e).__name__}: {e}", arguments)
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"Tool execution error: {type(e).__name__}: {e}"
                }],
            }
        finally:
            if _reporter_token is not None:
                from jebat_cli_new.progress import PROGRESS_REPORTER
                PROGRESS_REPORTER.reset(_reporter_token)
            if progress_token and pm:
                end_payload = {
                    "jsonrpc": JSONRPC_VERSION,
                    "method": "notifications/progress",
                    "params": {
                        "progressToken": progress_token,
                        "progress": 1,
                        "total": 1,
                    },
                }
                self._send_notification(end_payload)
                pm.complete(progress_token)

    async def _handle_resources_list(self, params: Dict) -> Dict:
        """Return stable workflow, live tool-registry, and dynamic context resources."""
        raw_resources = [
            {
                "uri": "jebat://workflow",
                "name": "JEBAT execution workflow",
                "description": "Plan, approve, execute, verify, and remember every change.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "jebat://metrics/tools",
                "name": "Tool call metrics and health",
                "description": "Per-tool call counts, error counts, latency p50/p95, and recent errors.",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://tools",
                "name": "JEBAT tool registry",
                "description": "Current tools, safety tiers, and execution limits.",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://memory/project",
                "name": "JEBAT active project memory (SelfLearn)",
                "description": "Durable learned facts about the current project (stack, conventions, environment, gotchas).",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://memory/dream",
                "name": "JEBAT autoMimpi dream summary",
                "description": "Consolidated heuristics, learning profile, and suggestions from latest dream cycle.",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://learning/profile",
                "name": "JEBAT SelfLearn profile",
                "description": "Adaptive learning analysis: skill assessment, knowledge map, velocity, retention health, and recommendations.",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://kb/summary",
                "name": "JEBAT knowledge base summary",
                "description": "Summary of memory count by type, strongest/weakest memories, patterns, and knowledge gaps.",
                "mimeType": "application/json",
            },
            {"uri": "jebat://learning/advisor", "name": "Project learning advisor",
             "description": "Evidence-cited recommendations and explicit reviewer feedback; no model calls.", "mimeType": "application/json"},
            {"uri": "jebat://kb/learning", "name": "Project learning KB",
             "description": "Recent project-scoped dream and advice records from SQLite FTS5.", "mimeType": "application/json"},
            {
                "uri": "jebat://errors/recent",
                "name": "Recent tool execution errors",
                "description": "Last 10 tool execution errors recorded by the MCP server.",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://analytics/tools",
                "name": "JEBAT tool usage analytics",
                "description": "Tool execution frequency and call counts, sorted by frequency.",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://database/schema",
                "name": "JEBAT database schema",
                "description": "Active database schema layout, tables, and definitions.",
                "mimeType": "text/sql",
            },
            {
                "uri": "jebat://design/tokens",
                "name": "JEBAT project design tokens",
                "description": "Detected design tokens, typography scale, and color rules for active project.",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://design/reference",
                "name": "Curated UI/UX pattern corpus",
                "description": "Real-world screen and component patterns with concrete structure, anti-patterns, and standards-backed metrics.",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://design/trends",
                "name": "Current UI/UX conventions",
                "description": "Dated 2025-2026 design conventions with what to do, what to avoid, and how to verify.",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://copy/rules",
                "name": "JEBAT sales copywriting guidelines",
                "description": "Mandatory copywriting conversion rules: CTA formulas, buzzword blacklists, and frameworks.",
                "mimeType": "application/json",
            },
            {
                "uri": "jebat://git/status",
                "name": "Git working tree status",
                "description": "Git working tree status.",
                "mimeType": "text/plain",
            },
            {
                "uri": "jebat://git/diff",
                "name": "Git unstaged diff",
                "description": "Git unstaged diff.",
                "mimeType": "text/x-diff",
            },
        ]
        for uri, entry in sorted(_skill_index().items()):
            raw_resources.append({
                "uri": uri,
                "name": f"Skill: {entry['name']}",
                "description": entry["description"] or f"JEBAT skill ({entry['store']}/{entry['name']})",
                "mimeType": "text/markdown",
            })
        for uri, entry in sorted(_wiki_index().items()):
            raw_resources.append({
                "uri": uri,
                "name": f"Wiki: {entry['title']}",
                "description": entry["description"],
                "mimeType": "text/markdown",
            })
        raw_templates = [
            {"uriTemplate": "jebat://file/{path}", "name": "Project file content", "description": "Read any file from the project workspace", "mimeType": "text/plain"},
            {"uriTemplate": "jebat://git/diff/{ref}", "name": "Git diff against ref", "description": "Show diff against a git ref (branch, commit, HEAD~N)", "mimeType": "text/x-diff"},
            {"uriTemplate": "jebat://artifact/{id}", "name": "Truncated tool result", "description": "Full text of a tool result that exceeded the inline size cap", "mimeType": "text/plain"},
            {"uriTemplate": "skill://{path}", "name": "JEBAT skill (SKILL.md)", "description": "Read any JEBAT skill's SKILL.md by store and name (e.g. skill://tokguru/page-mascot)", "mimeType": "text/markdown"},
            {"uriTemplate": "wiki://{slug}", "name": "JEBAT wiki page", "description": "Read any JEBAT wiki page as markdown by slug (e.g. wiki://erawan-qpos-operational-invariants)", "mimeType": "text/markdown"},
        ]
        if mcp_terse_mode():
            resources = [{"uri": r["uri"], "name": r["name"], "mimeType": r.get("mimeType", "text/plain")} for r in raw_resources]
            templates = [{"uriTemplate": t["uriTemplate"], "name": t["name"], "mimeType": t.get("mimeType", "text/plain")} for t in raw_templates]
            return {
                "resources": resources,
                "resourceTemplates": templates,
            }
        return {
            "resources": raw_resources,
            "resourceTemplates": raw_templates,
        }

    async def _handle_resources_read(self, params: Dict) -> Dict:
        """Read a JEBAT workflow, memory, design, or database resource for context-aware IDE clients."""
        uri = params.get("uri", "")
        if uri.startswith("jebat://artifact/"):
            artifact_id = uri[len("jebat://artifact/"):]
            if artifact_id in _ARTIFACTS:
                return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": _ARTIFACTS[artifact_id]}]}
            return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": f"Error: Artifact not found or expired: {artifact_id}"}]}

        if uri == "jebat://workflow":
            from jebat.workflows import workflow_resource

            text = workflow_resource()
            return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}

        if uri == "jebat://tools":
            self._ensure_tools_loaded()
            allowed = _allowed_tools()
            tools = [
                {"name": name, "safetyTier": tool.safety_tier, "timeout": tool.timeout}
                for name, tool in sorted(TOOL_REGISTRY.items())
                if allowed is None or name in allowed
            ]
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(tools)}]}

        if uri == "jebat://memory/project":
            try:
                from jebat.tools.automimpi_tools import _get_memory, _recall_project_facts
                memory = _get_memory()
                facts = _recall_project_facts(memory)
                payload = {"project": Path(os.getcwd()).name, "project_root": str(Path.cwd().resolve()), "total": len(facts), "facts": facts}
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(payload)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri in {"jebat://learning/advisor", "jebat://kb/learning"}:
            from jebat.tools.automimpi_tools import learning_advisor, learning_kb_search

            payload = await learning_advisor() if uri.endswith("advisor") else await learning_kb_search()
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(payload)}]}

        if uri == "jebat://memory/dream":
            try:
                from jebat.tools.automimpi_tools import _get_automimpi, _get_selflearn, learning_kb_search
                from jebat.features.memory.automimpi import DREAM_QUOTES
                engine = _get_automimpi()
                status = engine.get_status()
                analysis = _get_selflearn().analyze(Path.cwd().name, str(Path.cwd().resolve()))
                profile = engine._build_learning_profile(analysis)
                suggestions = engine._generate_suggestions(profile, analysis)

                quote_idx = (engine.dream_count + len(getattr(engine.memory, "traces", {}))) % len(DREAM_QUOTES)
                laksamana_quote = DREAM_QUOTES[quote_idx]

                suggestions_list = []
                for s in suggestions:
                    suggestions_list.append({
                        "type": s.suggestion_type.value if hasattr(s.suggestion_type, "value") else str(s.suggestion_type),
                        "title": s.title,
                        "reason": s.reason,
                        "urgency": s.urgency.value if hasattr(s.urgency, "value") else str(s.urgency),
                        "action": s.action,
                        "context": getattr(s, "context", {}),
                    })

                profile_dict = {
                    "skill_level": profile.skill_level,
                    "weak_areas": profile.weak_areas,
                    "strong_areas": profile.strong_areas,
                    "knowledge_gaps": profile.knowledge_gaps,
                    "recommended_focus": profile.recommended_focus,
                    "learning_velocity": profile.learning_velocity,
                    "consolidation_health": profile.consolidation_health,
                    "pattern_count": profile.pattern_count,
                    "strategy_success_rates": profile.strategy_success_rates,
                }

                # `get_status()` keys stay at the TOP LEVEL: that was this
                # resource's published shape before the dream report was
                # enriched, and IDE clients plus tests read dream_count and
                # last_dream_at directly. New fields are additive only.
                report_data = {
                    **status,
                    "status": status,
                    "profile": profile_dict,
                    "suggestions": suggestions_list,
                    "laksamana_quote": laksamana_quote,
                    "analysis": analysis,
                    "persisted_reports": await learning_kb_search(kind="dream", limit=1),
                }
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(report_data)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri == "jebat://learning/profile":
            try:
                from jebat.tools.automimpi_tools import _get_selflearn
                selflearn = _get_selflearn()
                analysis = selflearn.analyze(Path.cwd().name, str(Path.cwd().resolve()))
                if "velocity" not in analysis and "learning_velocity" in analysis:
                    analysis["velocity"] = analysis["learning_velocity"]
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(analysis)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri == "jebat://kb/summary":
            try:
                from jebat.tools.automimpi_tools import _get_memory, _get_automimpi, _get_selflearn, learning_kb_status
                from jebat.features.memory.automimpi import project_traces
                memory = _get_memory()
                automimpi = _get_automimpi()

                root = str(Path.cwd().resolve())
                traces = project_traces(memory, Path.cwd().name, root)
                analysis = _get_selflearn().analyze(Path.cwd().name, root)

                by_type: Dict[str, int] = {}
                for t in traces:
                    k = t.memory_type.value if hasattr(t.memory_type, "value") else str(t.memory_type)
                    by_type[k] = by_type.get(k, 0) + 1

                def get_strength(t):
                    try:
                        return t.calculate_current_strength()
                    except Exception:
                        return 0.0

                sorted_by_strength = sorted(traces, key=get_strength, reverse=True)

                top_10_strongest = [
                    {
                        "id": t.trace_id,
                        "content": t.content[:200] if len(t.content) > 200 else t.content,
                        "type": t.memory_type.value if hasattr(t.memory_type, "value") else str(t.memory_type),
                        "strength": round(get_strength(t), 3),
                        "tags": list(t.tags),
                    }
                    for t in sorted_by_strength[:10]
                ]

                top_5_weakest = [
                    {
                        "id": t.trace_id,
                        "content": t.content[:200] if len(t.content) > 200 else t.content,
                        "type": t.memory_type.value if hasattr(t.memory_type, "value") else str(t.memory_type),
                        "strength": round(get_strength(t), 3),
                        "tags": list(t.tags),
                    }
                    for t in sorted_by_strength[-5:]
                ] if traces else []

                pattern_count = analysis["pattern_count"]

                profile = automimpi._build_learning_profile(analysis)
                knowledge_gaps = getattr(profile, "knowledge_gaps", [])

                summary = {
                    "total_memories": len(traces),
                    "by_type": by_type,
                    "top_10_strongest": top_10_strongest,
                    "top_5_weakest": top_5_weakest,
                    "pattern_count": pattern_count,
                    "knowledge_gaps": list(knowledge_gaps),
                    "project_root": root,
                    "learning_database": await learning_kb_status(),
                }
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(summary)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri == "jebat://errors/recent":
            recent = list(_RECENT_ERRORS)[-10:]
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(recent)}]}

        if uri == "jebat://analytics/tools":
            sorted_counts = dict(sorted(_TOOL_CALL_COUNTS.items(), key=lambda item: item[1], reverse=True))
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(sorted_counts)}]}

        if uri == "jebat://database/schema":
            try:
                schema_file = Path(__file__).resolve().parents[3] / "database" / "schema.sql"
                if schema_file.exists():
                    text = schema_file.read_text(encoding="utf-8")
                else:
                    text = "-- Schema file not found at database/schema.sql"
                return {"contents": [{"uri": uri, "mimeType": "text/sql", "text": text}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "text/sql", "text": f"-- Error reading schema: {e}"}]}

        if uri == "jebat://design/tokens":
            try:
                from jebat.tools.design_tools import design_preflight
                tokens = await design_preflight(".")
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(tokens)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri == "jebat://design/reference":
            try:
                from jebat.features.design import PATTERNS
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(PATTERNS)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json({"error": str(e)})}]}

        if uri == "jebat://design/trends":
            try:
                from jebat.features.design import TRENDS
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(TRENDS)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json({"error": str(e)})}]}

        if uri == "jebat://copy/rules":
            try:
                from jebat.tools.copywriting_tools import AI_BUZZWORDS, GENERIC_CTAS
                rules = {
                    "mandatory_cta_formula": "[Action Verb] + [What They Get]",
                    "banned_generic_ctas": GENERIC_CTAS,
                    "prohibited_ai_filler": AI_BUZZWORDS,
                    "principles": [
                        "Benefits over features, customer language over company jargon",
                        "No fabricated metrics, logos, or testimonials",
                        "Single primary CTA per surface with subtle secondary option",
                    ],
                }
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(rules)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri == "jebat://metrics/tools":
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": _build_metrics_json()}]}

        if uri == "jebat://git/status":
            try:
                res = await asyncio.to_thread(
                    subprocess.run, ["git", "status", "--porcelain"],
                    capture_output=True, text=True, cwd=os.getcwd(), timeout=15,
                )
                text = res.stdout if res.returncode == 0 else f"git status error: {res.stderr}"
            except subprocess.TimeoutExpired:
                text = "git status timed out after 15s"
            except Exception as e:
                text = f"Error running git status: {e}"
            return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": text}]}

        if uri == "jebat://git/diff":
            try:
                res = await asyncio.to_thread(
                    subprocess.run, ["git", "diff"],
                    capture_output=True, text=True, cwd=os.getcwd(), timeout=15,
                )
                text = res.stdout if res.returncode == 0 else f"git diff error: {res.stderr}"
            except subprocess.TimeoutExpired:
                text = "git diff timed out after 15s"
            except Exception as e:
                text = f"Error running git diff: {e}"
            return {"contents": [{"uri": uri, "mimeType": "text/x-diff", "text": text}]}

        if uri.startswith("jebat://file/"):
            rel_path = uri[len("jebat://file/"):]
            try:
                base_dir = Path(os.getcwd()).resolve()
                file_path = (base_dir / rel_path).resolve()
                if not file_path.is_relative_to(base_dir) or any(part.startswith(".") for part in file_path.relative_to(base_dir).parts):
                    return {"error": {"code": -32602, "message": "Access denied: path traversal or hidden path detected"}}
                if file_path.is_file():
                    text = file_path.read_text(encoding="utf-8", errors="replace")
                else:
                    text = f"File not found: {rel_path}"
                return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": text}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": f"Error reading file: {e}"}]}
        if uri.startswith("jebat://git/diff/"):
            ref = uri[len("jebat://git/diff/"):]
            try:
                res = await asyncio.to_thread(
                    subprocess.run, ["git", "diff", ref],
                    capture_output=True, text=True, cwd=os.getcwd(), timeout=15,
                )
                text = res.stdout if res.returncode == 0 else f"git diff error: {res.stderr}"
            except subprocess.TimeoutExpired:
                text = f"git diff {ref} timed out after 15s"
            except Exception as e:
                text = f"Error running git diff against {ref}: {e}"
            return {"contents": [{"uri": uri, "mimeType": "text/x-diff", "text": text}]}

        if uri.startswith("skill://"):
            entry = _skill_index().get(uri)
            if entry is None:
                # TTL may be stale right after skill_manage wrote a new skill.
                entry = _skill_index(refresh=True).get(uri)
            if entry is None:
                return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": f"Error: Skill not found: {uri}"}]}
            try:
                text = Path(entry["path"]).read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                text = f"Error reading skill: {e}"
            return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}

        if uri.startswith("wiki://"):
            entry = _wiki_index().get(uri)
            if entry is None:
                # TTL may be stale right after a wiki_* tool wrote a new page.
                entry = _wiki_index(refresh=True).get(uri)
            if entry is None:
                # Accept a title or slug-ish title, not just the exact slug.
                wanted = uri[len("wiki://"):].strip().lower()
                wanted_slug = "-".join(wanted.replace("_", " ").split())
                for candidate in _wiki_index(refresh=True).values():
                    if wanted in (candidate["slug"].lower(), candidate["title"].lower()) or wanted_slug == candidate["slug"].lower():
                        entry = candidate
                        break
            if entry is None:
                return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": f"Error: Wiki page not found: {uri}"}]}
            try:
                text = Path(entry["path"]).read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                text = f"Error reading wiki page: {e}"
            return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}
        return {"contents": []}

    async def _handle_prompts_list(self, params: Dict) -> Dict:
        """Return reusable prompts for governed agent workflows."""
        from jebat.features.mcp.mcp_prompts import prompts_list

        return prompts_list(terse=mcp_terse_mode())

    async def _handle_prompts_get(self, params: Dict) -> Dict:
        """Return the requested guided workflow prompt."""
        from jebat.features.mcp.mcp_prompts import prompts_get

        return prompts_get(params)

    async def _handle_ping(self, params: Dict) -> Dict:
        """Health check ping."""
        return {"status": "ok", "timestamp": str(asyncio.get_event_loop().time())}

    async def _handle_roots_list(self, params: Dict) -> Dict:
        """Return root URIs exposed by the workspace."""
        cwd = os.getcwd().replace("\\", "/")
        uri = f"file:///{cwd.lstrip('/')}"
        project_name = Path(os.getcwd()).name or "workspace"
        return {
            "roots": [
                {
                    "uri": uri,
                    "name": project_name,
                }
            ]
        }

    async def _handle_logging_set_level(self, params: Dict) -> None:
        """Set server log level (logging/setLevel)."""
        level = str(params.get("level", "info")).lower()
        self._log_level = level
        level_map = {
            "debug": logging.DEBUG, "info": logging.INFO,
            "notice": logging.INFO, "warning": logging.WARNING,
            "error": logging.ERROR, "critical": logging.CRITICAL,
        }
        if level in level_map:
            logger.setLevel(level_map[level])
        self._log(level, f"Log level set to {level}")

    _handle_set_log_level = _handle_logging_set_level

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
        logger.info("Starting MCP server on stdio transport")
        sys.stderr.write(f"[JEBAT MCP Server] Starting on stdio, "
                         f"protocol v{MCP_PROTOCOL_VERSION}\n")
        sys.stderr.flush()

        # Read/write on the raw file descriptors. connect_read_pipe() and
        # sys.stdin.buffer.detach().read(1) both treat a subprocess pipe as an
        # immediate EOF and kill the server, so we use os.read/os.write which
        # block correctly until the IDE sends data or closes the pipe.
        infd = sys.stdin.fileno()
        outfd = sys.stdout.fileno()

        # Dedicated reader thread feeding a queue: one blocked OS read parked
        # on its own thread instead of one run_in_executor ticket PER LINE,
        # which churned executor threads and added scheduler latency under
        # bursty IDE traffic.
        line_queue: "asyncio.Queue[Optional[bytes]]" = asyncio.Queue(maxsize=256)
        loop = asyncio.get_event_loop()

        def reader_thread() -> None:
            data = b""
            try:
                while True:
                    chunk = os.read(infd, 1)
                    if chunk == b"":
                        if data:
                            loop.call_soon_threadsafe(line_queue.put_nowait, data)
                        loop.call_soon_threadsafe(line_queue.put_nowait, b"")
                        return
                    data += chunk
                    if chunk == b"\n":
                        loop.call_soon_threadsafe(line_queue.put_nowait, data)
                        data = b""
            except OSError:
                if data:
                    loop.call_soon_threadsafe(line_queue.put_nowait, data)
                loop.call_soon_threadsafe(line_queue.put_nowait, b"")

        async def read_line() -> Optional[bytes]:
            raw = await line_queue.get()
            if raw == b"":
                return None  # EOF sentinel
            return raw

        threading.Thread(target=reader_thread, daemon=True, name="mcp-stdio-reader").start()

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
                self._flush_pending_notifications()

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
        import uvicorn  # type: ignore
        from starlette.applications import Starlette  # type: ignore
        from starlette.routing import Route  # type: ignore
        from starlette.responses import JSONResponse, Response  # type: ignore
        import sse_starlette  # type: ignore

        logger.info(f"Starting MCP server on HTTP transport: {self.host}:{self.http_port}")
        sys.stderr.write(f"[JEBAT MCP Server] Starting on HTTP "
                         f"{self.host}:{self.http_port}\n")

        server_instance = self
        from .mcp_transport import ProgressManager

        notifications: asyncio.Queue = asyncio.Queue()
        self._progress_manager = ProgressManager(notification_queue=notifications)

        def check_auth(request) -> Optional[Response]:
            expected_key = os.getenv("JEBAT_API_KEY", "")
            if not expected_key:
                return None
            provided_key = (
                request.headers.get("x-api-key")
                or request.query_params.get("api_key")
                or ""
            )
            if not provided_key:
                auth_header = request.headers.get("authorization", "")
                if auth_header.lower().startswith("bearer "):
                    provided_key = auth_header[7:].strip()
            if not provided_key or not hmac.compare_digest(provided_key.encode(), expected_key.encode()):
                return JSONResponse(
                    {"error": "unauthorized", "message": "API key required or invalid"},
                    status_code=401,
                )
            return None

        async def handle_message(request):
            """Handle POST /message — client sends JSON-RPC request."""
            auth_err = check_auth(request)
            if auth_err:
                return auth_err
            try:
                body = await request.json()
            except json.JSONDecodeError:
                return JSONResponse({"jsonrpc": JSONRPC_VERSION, "id": None,
                                     "error": {"code": MCPError.PARSE_ERROR,
                                               "message": "Invalid JSON"}},
                                    status_code=400)

            response = await server_instance.handle_request(body)
            server_instance._flush_pending_notifications()
            if response is None:
                # Notification — no response
                return Response(status_code=204)
            return JSONResponse(json.loads(response))

        async def handle_sse(request):
            """Handle GET /sse — establish SSE connection for notifications."""
            auth_err = check_auth(request)
            if auth_err:
                return auth_err
            async def events():
                yield {"event": "endpoint", "data": "/message"}
                while True:
                    try:
                        notification = await asyncio.wait_for(notifications.get(), timeout=30)
                        yield {"event": "message", "data": json.dumps(notification)}
                    except asyncio.TimeoutError:
                        yield {"event": "ping", "data": ""}

            return sse_starlette.EventSourceResponse(events())

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
    # secrets.env (TYPESAFE_API_KEY etc.) is normally loaded by the CLI init
    # path — stdio entrypoints never pass through it, so load it here before
    # the advisor or provider code checks os.environ. Idempotent.
    try:
        from jebat.llm.auth import _ensure_secrets_loaded
        _ensure_secrets_loaded()
    except Exception as e:
        logger.warning("secrets.env load skipped: %s", e)

    # Warm a configured local advisor model (Laya/transformers) in the
    # background: first load can take minutes (the 421M Laya checkpoint
    # downloads + loads slowly), which would blow the per-call tier deadline.
    if os.getenv("JEBAT_ADVISOR_MODEL", "").strip() or os.getenv(
        "JEBAT_ADVISOR_BACKEND", "auto"
    ).lower() in ("laya", "transformers"):
        import threading

        def _warm() -> None:
            try:
                from routers.advisor import warm_advisor
                warm_advisor()
            except Exception as e:
                logger.info("advisor warm-up skipped: %s", e)

        threading.Thread(target=_warm, name="advisor-warm", daemon=True).start()

    if transport == "streamable-http":
        from jebat.features.mcp.mcp_transport import run_streamable_http

        run_streamable_http(MCPServer(), port=port, host=host)
        return

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
        print(mcp_json(ide_config["config"]))

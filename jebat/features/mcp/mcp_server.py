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
import json
import logging
import os
import sys
import traceback
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from jebat.tools import TOOL_REGISTRY, ToolDef, call_tool, classify_tool_call

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

MCP_PROTOCOL_VERSION = "2026-07-28"
SUPPORTED_PROTOCOL_VERSIONS = ("2024-11-05", "2025-03-26", "2025-06-18", "2026-07-28")
JSONRPC_VERSION = "2.0"
SERVER_NAME = "jebat-mcp-server"
SERVER_VERSION = "0.1.0"


# ── Tracking & Severity ──────────────────────────────────────────────────────

_RECENT_ERRORS: List[Dict[str, Any]] = []
_TOOL_CALL_COUNTS: Dict[str, int] = {}


def _record_tool_error(tool_name: str, error: str, arguments: Dict, kind: str = "execution") -> None:
    """Append a tool error to the bounded recent-errors ring (F3)."""
    _RECENT_ERRORS.append({
        "tool": tool_name,
        "error": error,
        "kind": kind,
        "timestamp": time.time(),
        "arguments": arguments,
    })
    if len(_RECENT_ERRORS) > 50:
        _RECENT_ERRORS.pop(0)

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
        """Lazily create AutoMimpi + SelfLearn, build profile, generate suggestions, send notifications/advisorReady."""
        try:
            from jebat.features.memory import EnhancedMemorySystem
            from jebat.features.memory.automimpi import AutoMimpi, SelfLearn, create_automimpi, create_selflearn

            try:
                from jebat.tools.automimpi_tools import _get_automimpi, _get_selflearn, _get_memory
                automimpi = _get_automimpi()
                selflearn = _get_selflearn()
                memory = _get_memory()
            except Exception:
                memory = EnhancedMemorySystem()
                memory._load()
                automimpi = create_automimpi(memory)
                selflearn = create_selflearn(memory)

            profile = automimpi._build_learning_profile()
            suggestions = automimpi._generate_suggestions(profile)

            top_3 = []
            for s in suggestions[:3]:
                top_3.append({
                    "type": s.suggestion_type.value if hasattr(s.suggestion_type, "value") else str(s.suggestion_type),
                    "title": s.title,
                    "reason": s.reason,
                    "urgency": s.urgency.value if hasattr(s.urgency, "value") else str(s.urgency),
                    "action": s.action,
                })

            stale_count = 0
            traces = list(memory.traces.values()) if hasattr(memory, "traces") else []
            for t in traces:
                try:
                    if t.calculate_current_strength() < 0.3:
                        stale_count += 1
                except Exception:
                    pass

            last_dream = automimpi.last_dream_at.isoformat() if automimpi.last_dream_at else None
            health_score = getattr(profile, "consolidation_health", 0.5)

            payload = {
                "jsonrpc": JSONRPC_VERSION,
                "method": "notifications/advisorReady",
                "params": {
                    "healthScore": health_score,
                    "suggestions": top_3,
                    "staleMemories": stale_count,
                    "lastDream": last_dream,
                },
            }
            self._pending_notifications.append(payload)
        except Exception as e:
            logger.warning(f"Error in _send_advisor_notification: {e}")

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

        # Check page size from env or instance/constant
        page_size_env = os.getenv("JEBAT_MCP_TOOLS_PAGE")
        if page_size_env is not None:
            try:
                page_size = int(page_size_env)
            except ValueError:
                page_size = 0
        else:
            page_size = MCP_TOOLS_PAGE_SIZE

        cache_key = (offset, page_size, is_terse)
        if cache_key in self._tools_cache:
            return self._tools_cache[cache_key]

        tool_items = list(TOOL_REGISTRY.items())
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
        if tool_name not in TOOL_REGISTRY:
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
        if tool_name not in TOOL_REGISTRY:
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

        # Wire ProgressManager for long-running tools (MQ-4)
        progress_tools = ('agent_execute', 'ghost_sql', 'pentest_scan', 'advisor_decide')
        progress_token = None
        pm = None
        if tool_name in progress_tools:
            from jebat.features.mcp.mcp_transport import ProgressManager
            if not hasattr(self, "_progress_manager") or self._progress_manager is None:
                self._progress_manager = ProgressManager()
            pm = self._progress_manager
            progress_token = pm.start(tool_name, total=1.0)
            start_payload = {
                "jsonrpc": JSONRPC_VERSION,
                "method": "notifications/progress",
                "params": {
                    "progressToken": progress_token,
                    "progress": 0.5,
                    "total": 1,
                },
            }
            self._send_notification(start_payload)

        try:
            # Dispatch to JEBAT tool registry
            result = await call_tool(tool_name, **arguments)

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

        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            _RECENT_ERRORS.append({
                "tool": tool_name,
                "error": f"{type(e).__name__}: {e}",
                "timestamp": time.time(),
                "arguments": arguments,
            })
            if len(_RECENT_ERRORS) > 50:
                _RECENT_ERRORS.pop(0)
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"Tool execution error: {type(e).__name__}: {e}"
                }],
            }
        finally:
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
        raw_templates = [
            {"uriTemplate": "jebat://file/{path}", "name": "Project file content", "description": "Read any file from the project workspace", "mimeType": "text/plain"},
            {"uriTemplate": "jebat://git/diff/{ref}", "name": "Git diff against ref", "description": "Show diff against a git ref (branch, commit, HEAD~N)", "mimeType": "text/x-diff"},
            {"uriTemplate": "jebat://artifact/{id}", "name": "Truncated tool result", "description": "Full text of a tool result that exceeded the inline size cap", "mimeType": "text/plain"},
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
            text = """# JEBAT workflow

1. Plan: state intent, scope, constraints, and risk.
2. Approve: classify each action as AUTO, CONFIRM, or DANGEROUS.
3. Execute: call the smallest tool set needed.
4. Verify: check the observable result, not internal assumptions.
5. Remember: store durable project facts without secrets.
"""
            return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}

        if uri == "jebat://tools":
            self._ensure_tools_loaded()
            tools = [
                {"name": name, "safetyTier": tool.safety_tier, "timeout": tool.timeout}
                for name, tool in sorted(TOOL_REGISTRY.items())
            ]
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(tools)}]}

        if uri == "jebat://memory/project":
            try:
                from jebat.tools.automimpi_tools import _get_memory, _recall_project_facts
                memory = _get_memory()
                facts = _recall_project_facts(memory)
                payload = {"project": Path(os.getcwd()).name, "total": len(facts), "facts": facts}
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(payload)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri == "jebat://memory/dream":
            try:
                from jebat.tools.automimpi_tools import _get_automimpi
                from jebat.features.memory.automimpi import DREAM_QUOTES
                engine = _get_automimpi()
                status = engine.get_status()
                profile = engine._build_learning_profile()
                suggestions = engine._generate_suggestions(profile)

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
                }
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(report_data)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri == "jebat://learning/profile":
            try:
                from jebat.tools.automimpi_tools import _get_selflearn
                selflearn = _get_selflearn()
                analysis = selflearn.analyze()
                if "velocity" not in analysis and "learning_velocity" in analysis:
                    analysis["velocity"] = analysis["learning_velocity"]
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(analysis)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri == "jebat://kb/summary":
            try:
                from jebat.tools.automimpi_tools import _get_memory, _get_automimpi
                memory = _get_memory()
                automimpi = _get_automimpi()

                traces = list(memory.traces.values()) if hasattr(memory, "traces") else []

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

                pattern_count = len(getattr(memory, "extracted_patterns", []))

                profile = automimpi._build_learning_profile()
                knowledge_gaps = getattr(profile, "knowledge_gaps", [])

                summary = {
                    "total_memories": len(traces),
                    "by_type": by_type,
                    "top_10_strongest": top_10_strongest,
                    "top_5_weakest": top_5_weakest,
                    "pattern_count": pattern_count,
                    "knowledge_gaps": list(knowledge_gaps),
                }
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": mcp_json(summary)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri == "jebat://errors/recent":
            recent = _RECENT_ERRORS[-10:]
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

        if uri == "jebat://git/status":
            try:
                res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=os.getcwd())
                text = res.stdout if res.returncode == 0 else f"git status error: {res.stderr}"
            except Exception as e:
                text = f"Error running git status: {e}"
            return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": text}]}

        if uri == "jebat://git/diff":
            try:
                res = subprocess.run(["git", "diff"], capture_output=True, text=True, cwd=os.getcwd())
                text = res.stdout if res.returncode == 0 else f"git diff error: {res.stderr}"
            except Exception as e:
                text = f"Error running git diff: {e}"
            return {"contents": [{"uri": uri, "mimeType": "text/x-diff", "text": text}]}

        if uri.startswith("jebat://file/"):
            rel_path = uri[len("jebat://file/"):]
            try:
                file_path = (Path(os.getcwd()) / rel_path).resolve()
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
                res = subprocess.run(["git", "diff", ref], capture_output=True, text=True, cwd=os.getcwd())
                text = res.stdout if res.returncode == 0 else f"git diff error: {res.stderr}"
            except Exception as e:
                text = f"Error running git diff against {ref}: {e}"
            return {"contents": [{"uri": uri, "mimeType": "text/x-diff", "text": text}]}
        return {"contents": []}

    async def _handle_prompts_list(self, params: Dict) -> Dict:
        """Return reusable prompts for governed agent workflows."""
        raw_prompts = [
            {
                "name": "plan-act-verify-remember",
                "description": "Run a governed JEBAT task from intent through durable memory.",
                "arguments": [
                    {"name": "task", "description": "The task to perform", "required": True},
                    {"name": "scope", "description": "Files, services, or systems in scope", "required": False},
                ],
            },
            {
                "name": "hallmark-design-audit",
                "description": "Audit UI markup against Hallmark 6-axis anti-slop gates and 8-state interaction rules.",
                "arguments": [
                    {"name": "markup", "description": "UI component markup or code", "required": True},
                    {"name": "component_type", "description": "Type of component (button, card, hero, pricing)", "required": False},
                ],
            },
            {
                "name": "sales-copy-review",
                "description": "Mandatory copywriting conversion review: strip AI buzzwords and transform generic CTAs.",
                "arguments": [
                    {"name": "copy", "description": "Sales or marketing text to audit", "required": True},
                    {"name": "benefit", "description": "Specific tangible benefit the customer achieves", "required": False},
                ],
            },
            {
                "name": "project-onboard",
                "description": "Auto-scan project files and SelfLearn memory to produce a comprehensive project context snapshot.",
                "arguments": [
                    {"name": "root", "description": "Project root directory", "required": False},
                ],
            },
            {
                "name": "kb-review",
                "description": "Review JEBAT knowledge base: analyze strong areas, stale memories, knowledge gaps, and suggested consolidation actions.",
                "arguments": [
                    {"name": "focus_area", "description": "Optional focus area or topic to evaluate", "required": False},
                ],
            },
            {
                "name": "debug-this",
                "description": "Structured 5-step debugging workflow for diagnosing and fixing errors.",
                "arguments": [
                    {"name": "error_message", "description": "The error message or traceback to debug", "required": True},
                    {"name": "file", "description": "File or module where the error occurred", "required": False},
                    {"name": "context", "description": "Additional context, reproducer, or logs", "required": False},
                ],
            },
        ]
        if mcp_terse_mode():
            terse_prompts = []
            for p in raw_prompts:
                tp: Dict[str, Any] = {"name": p["name"]}
                req_args = [a for a in p.get("arguments", []) if a.get("required")]
                if req_args:
                    tp["arguments"] = req_args
                terse_prompts.append(tp)
            return {"prompts": terse_prompts}
        return {"prompts": raw_prompts}

    async def _handle_prompts_get(self, params: Dict) -> Dict:
        """Return the requested guided workflow prompt."""
        name = params.get("name", "")
        arguments = params.get("arguments", {})

        if name == "plan-act-verify-remember":
            task = arguments.get("task", "the requested task")
            scope = arguments.get("scope", "the current workspace")
            text = (
                f"Perform this task: {task}\nScope: {scope}\n\n"
                "First plan the smallest reversible change. Before each CONFIRM or "
                "DANGEROUS action, return the exact operation and wait for approval. "
                "After execution, verify the user-visible result and remember only "
                "durable non-secret project facts."
            )
            return {
                "description": "Governed JEBAT task workflow",
                "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
            }

        if name == "hallmark-design-audit":
            markup = arguments.get("markup", "")
            c_type = arguments.get("component_type", "generic")
            text = (
                f"Audit this {c_type} markup against Hallmark standards:\n\n{markup}\n\n"
                "Evaluate against:\n"
                "1. 6-Axis Scoring (Philosophy, Hierarchy, Execution, Specificity, Restraint, Variety)\n"
                "2. 8-State Interactive Discipline (default, hover, focus-visible, active, disabled, loading, error, success)\n"
                "3. Hard Rules: No italic headers, no re-drawn browser chrome, responsive at 320/375/768px.\n"
                "Provide the Hallmark score stamp: /* Hallmark · pre-emit critique: P# H# E# S# R# V# */ and concrete fixes."
            )
            return {
                "description": "Hallmark anti-slop design audit prompt",
                "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
            }

        if name == "sales-copy-review":
            copy = arguments.get("copy", "")
            benefit = arguments.get("benefit", "clear value proposition")
            text = (
                f"Perform a sales copywriting review on this text:\n\n{copy}\n\n"
                f"Target Benefit: {benefit}\n\n"
                "Requirements:\n"
                "1. Transform any generic CTA into [Action Verb] + [What They Get].\n"
                "2. Strip banned AI buzzwords (delve, testament, tapestry, seamless, game-changer).\n"
                "3. Ensure benefits over features, customer language, and active voice.\n"
                "4. Enforce: No fabricated statistics, testimonials, or claims."
            )
            return {
                "description": "Sales copywriting conversion review prompt",
                "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
            }
        if name == "project-onboard":
            root_arg = arguments.get("root")
            root_dir = Path(root_arg).resolve() if root_arg else Path(os.getcwd()).resolve()

            snippets = []
            common_files = ["package.json", "pyproject.toml", "tsconfig.json", ".jebat/memory.json", "README.md"]
            for rel_name in common_files:
                target_file = root_dir / rel_name
                try:
                    if target_file.is_file():
                        content = target_file.read_text(encoding="utf-8", errors="replace")
                        snippet = content[:4000] + ("\n... [truncated]" if len(content) > 4000 else "")
                        snippets.append(f"--- {rel_name} ---\n{snippet}")
                except Exception as e:
                    logger.debug(f"Could not read {target_file} for project-onboard prompt: {e}")

            files_context = "\n\n".join(snippets) if snippets else "No common project configuration files found."

            prompt_text = (
                f"You are onboarding to the project located at '{root_dir}'.\n\n"
                f"Project configuration and context files detected:\n\n{files_context}\n\n"
                "Please analyze this project:\n"
                "1. Identify the tech stack, languages, frameworks, and architecture.\n"
                "2. Note key conventions, build/test commands, and entry points.\n"
                "3. Check for any prior project memory or gotchas.\n"
                "4. Produce a comprehensive project context snapshot summarizing your findings."
            )
            return {
                "description": "Auto-scan project files and SelfLearn memory to produce a comprehensive project context snapshot.",
                "messages": [{"role": "user", "content": {"type": "text", "text": prompt_text}}],
            }



        if name == "kb-review":
            focus_area = arguments.get("focus_area", "all domains")
            stats_text = "Memory stats unavailable."
            try:
                from jebat.tools.automimpi_tools import _get_memory, _get_automimpi
                memory = _get_memory()
                automimpi = _get_automimpi()
                total = len(memory.traces)
                profile = automimpi._build_learning_profile()
                strong = ", ".join(profile.strong_areas) if profile.strong_areas else "none"
                weak = ", ".join(profile.weak_areas) if profile.weak_areas else "none"
                gaps = ", ".join(profile.knowledge_gaps) if profile.knowledge_gaps else "none"
                patterns = len(getattr(memory, "extracted_patterns", []))
                stats_text = (
                    f"Total memories: {total}\n"
                    f"Strong areas: {strong}\n"
                    f"Weak areas: {weak}\n"
                    f"Knowledge gaps: {gaps}\n"
                    f"Consolidated patterns: {patterns}\n"
                    f"Consolidation health: {profile.consolidation_health:.2f}"
                )
            except Exception as e:
                stats_text = f"Could not load memory stats: {e}"

            text = (
                f"Perform a comprehensive review of the JEBAT knowledge base for focus area: {focus_area}.\n\n"
                f"Current Knowledge Base Statistics:\n{stats_text}\n\n"
                "Please review the knowledge base and address:\n"
                "1. What is strong: Identify domains with solid, high-strength memory coverage.\n"
                "2. What is stale: Identify weak or decaying memories that need refreshing or pruning.\n"
                "3. What is missing: Highlight critical knowledge gaps or unrepresented skills.\n"
                "4. Suggested actions: Recommend concrete consolidation steps, practice areas, or facts to remember."
            )
            return {
                "description": "JEBAT knowledge base review prompt",
                "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
            }

        if name == "debug-this":
            error_message = arguments.get("error_message", "")
            file_path = arguments.get("file", "unknown")
            context = arguments.get("context", "")

            text = (
                f"Debug the following error:\n\n"
                f"Error: {error_message}\n"
                f"File: {file_path}\n"
                + (f"Context: {context}\n\n" if context else "\n")
                + "Follow this structured 5-step debugging workflow:\n"
                "1. Reproduce the error: State the minimal conditions or command that reproduce the issue.\n"
                "2. Identify the root cause: Trace execution to find the underlying bug, not just the crash point.\n"
                "3. Fix the source, not the symptom: Implement a clean fix addressing the actual cause.\n"
                "4. Verify the fix: Test and prove that the error is resolved and no regressions are introduced.\n"
                "5. Store the pattern as a memory: Record the bug pattern and solution in JEBAT memory to avoid recurrence."
            )
            return {
                "description": "Structured 5-step debugging workflow",
                "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
            }
        return {"description": "Unknown prompt", "messages": []}
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

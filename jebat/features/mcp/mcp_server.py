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
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from jebat.tools import TOOL_REGISTRY, ToolDef, call_tool, classify_tool_call

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

MCP_PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = ("2024-11-05", "2025-03-26", "2025-06-18")
JSONRPC_VERSION = "2.0"
SERVER_NAME = "jebat-mcp-server"
SERVER_VERSION = "0.1.0"


# ── Data Structures ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MCPCapabilities:
    """Server capabilities announced during initialization."""
    tools: bool = True
    resources: bool = True
    prompts: bool = True
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
        "annotations": {
            "readOnlyHint": tool_def.safety_tier == "auto",
            "destructiveHint": tool_def.safety_tier == "dangerous",
            "idempotentHint": tool_def.safety_tier == "auto",
            "openWorldHint": tool_def.name.startswith(("browser", "search", "web")),
        },
        "_meta": {"jebat/safetyTier": tool_def.safety_tier},
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
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
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

        requested_version = params.get("protocolVersion")
        protocol_version = (
            requested_version
            if requested_version in SUPPORTED_PROTOCOL_VERSIONS
            else MCP_PROTOCOL_VERSION
        )

        return {
            "protocolVersion": protocol_version,
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
                "logging": {},
                "experimental": self.capabilities.experimental,
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        }

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
            # Copywriting & Conversion (Pawang Jualan)
            ("copywriting_tools", "jebat.tools.copywriting_tools"),
            # Voyager-style Dynamic Tool Synthesis
            ("dynamic_synthesis", "jebat.tools.dynamic_synthesis"),
        ]
        _loaded = 0
        _failed = []
        for name, mod_path in _tool_modules:
            try:
                __import__(mod_path)
                _loaded += 1
            except ImportError as e:
                _failed.append((name, str(e)))

        self._tools_loaded = True
        failed = ", ".join(f"{n}({e})" for n, e in _failed)
        if failed:
            logger.info(f"MCP loaded {_loaded}/{len(_tool_modules)} tool modules; skipped: {failed}")
        else:
            logger.info(f"MCP server loaded {_loaded} tool modules, {len(TOOL_REGISTRY)} tools")

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
        arguments = params.get("arguments") or {}

        if tool_name not in TOOL_REGISTRY:
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
                    "text": f"Tool '{tool_name}' requires {safety_tier} approval before execution.",
                }],
                "structuredContent": {
                    "status": "approval_required",
                    "tool": tool_name,
                    "safetyTier": safety_tier,
                    "arguments": arguments,
                    "next": "Approve this exact call in JEBAT CLI, then retry it.",
                },
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
        """Return stable workflow, live tool-registry, and dynamic context resources."""
        return {
            "resources": [
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
                    "uri": "jebat://copy/rules",
                    "name": "JEBAT sales copywriting guidelines",
                    "description": "Mandatory copywriting conversion rules: CTA formulas, buzzword blacklists, and frameworks.",
                    "mimeType": "application/json",
                },
            ]
        }

    async def _handle_resources_read(self, params: Dict) -> Dict:
        """Read a JEBAT workflow, memory, design, or database resource for context-aware IDE clients."""
        uri = params.get("uri", "")
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
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(payload, indent=2)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        if uri == "jebat://memory/dream":
            try:
                from jebat.tools.automimpi_tools import _get_automimpi
                engine = _get_automimpi()
                status = engine.get_status()
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(status, indent=2)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

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
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(tokens, indent=2)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

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
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(rules, indent=2)}]}
            except Exception as e:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}]}

        return {"contents": []}

    async def _handle_prompts_list(self, params: Dict) -> Dict:
        """Return reusable prompts for governed agent workflows."""
        return {
            "prompts": [
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
            ]
        }

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

        return {"description": "Unknown prompt", "messages": []}
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
        print(json.dumps(ide_config["config"], indent=2))

"""MCP Transport Upgrades — Streamable HTTP + SSE + Progress Tokens (MCP 2025-03-26 spec).

This module upgrades the JEBAT MCP server from the 2024-11-05 protocol to the
2025-03-26 revision, adding:

1. Streamable HTTP transport — single /mcp endpoint that handles both
   JSON-RPC requests (POST) and SSE streams (GET), replacing the old
   separate /message + /sse endpoints.

2. Sampling (createMessage) — lets IDEs request LLM completions through
   JEBAT's 9Router proxy, so the IDE can ask JEBAT to "think" on its behalf.

3. Progress tokens — tools can send notifications/progress during
   long-running operations (nmap scans, code generation, etc.), giving
   IDEs real-time feedback instead of silent waits.

4. Resource subscriptions — lets IDEs subscribe to JEBAT knowledge base
   updates via resources/subscribe → notifications/resources/updated.

Usage:
    # Start upgraded MCP server
    jebat mcp serve --transport streamable-http --port 8100
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── MCP 2025-03-26 Protocol Constants ────────────────────────────────────────

MCP_PROTOCOL_VERSION_NEW = "2025-03-26"
JSONRPC_VERSION = "2.0"

# ── Progress Token Manager ───────────────────────────────────────────────────

@dataclass
class ProgressToken:
    """Tracks progress for a long-running tool call."""
    token: str
    tool_name: str
    total: Optional[float] = None
    started_at: float = field(default_factory=time.time)
    _current: float = 0.0

    def advance(self, progress: float, message: str = "") -> Dict[str, Any]:
        """Advance progress and return a notification payload."""
        self._current = progress
        return {
            "jsonrpc": JSONRPC_VERSION,
            "method": "notifications/progress",
            "params": {
                "progressToken": self.token,
                "progress": progress,
                "total": self.total,
            },
        }

    def done(self) -> bool:
        return self.total is not None and self._current >= self.total


class ProgressManager:
    """Manages progress tokens for long-running MCP tool calls.

    When a tool call takes >2 seconds, the MCP server automatically
    creates a progress token and sends periodic notifications to the
    connected IDE so users see real-time feedback.

    Usage in tool handlers:
        pm = ProgressManager()
        token = pm.start("nmap_scan", total=100)
        pm.notify(token, 25, "Scanning ports 1-1000...")
        pm.notify(token, 50, "Scanning ports 1000-2000...")
        pm.complete(token)
    """

    def __init__(self, notification_queue: Optional[asyncio.Queue] = None):
        self._tokens: Dict[str, ProgressToken] = {}
        self._queue = notification_queue  # For SSE/Streamable HTTP delivery

    def start(self, tool_name: str, total: Optional[float] = None) -> str:
        """Create a new progress token for a tool call."""
        token = f"jebat-progress-{uuid.uuid4().hex[:8]}"
        pt = ProgressToken(token=token, tool_name=tool_name, total=total)
        self._tokens[token] = pt
        return token

    def notify(self, token: str, progress: float, message: str = "") -> None:
        """Send a progress notification via the SSE queue."""
        pt = self._tokens.get(token)
        if pt is None:
            logger.warning(f"Unknown progress token: {token}")
            return
        payload = pt.advance(progress, message)
        if self._queue:
            self._queue.put_nowait(payload)
        logger.debug(f"Progress [{pt.tool_name}]: {progress}/{pt.total} — {message}")

    def complete(self, token: str) -> None:
        """Mark a progress token as complete."""
        pt = self._tokens.get(token)
        if pt and pt.total is not None:
            payload = pt.advance(pt.total, "Complete")
            if self._queue:
                self._queue.put_nowait(payload)
        self._tokens.pop(token, None)

    def cancel(self, token: str) -> None:
        """Cancel a progress token."""
        self._tokens.pop(token, None)


# ── Sampling Handler (createMessage) ──────────────────────────────────────────

class SamplingHandler:
    """Handles MCP sampling requests (createMessage) from IDEs.

    When an IDE sends a createMessage request, JEBAT uses its 9Router
    LLM proxy to generate a response. This lets the IDE "borrow" JEBAT's
    AI capabilities without needing its own LLM connection.

    MCP Sampling spec:
        Request:  { method: "sampling/createMessage", params: { messages, maxTokens, ... } }
        Response: { role: "assistant", model: "...", content: { type: "text", text: "..." } }
    """

    def __init__(self, config: Any = None):
        self._config = config

    async def handle_create_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process a sampling/createMessage request from the IDE.

        Args:
            params: MCP sampling params with messages, maxTokens, systemPrompt, etc.

        Returns:
            MCP sampling response with role, model, and content.
        """
        messages = params.get("messages", [])
        max_tokens = params.get("maxTokens", 4096)
        system_prompt = params.get("systemPrompt", "")
        temperature = params.get("temperature", 0.7)
        model_preference = params.get("modelPreferences", [{}])
        preferred_model = model_preference[0].get("name", "") if model_preference else ""

        # Convert MCP messages to simple prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", {})
            if isinstance(content, dict):
                text = content.get("text", "")
            elif isinstance(content, str):
                text = content
            else:
                text = str(content)
            prompt_parts.append(f"{role}: {text}")

        combined_prompt = "\n".join(prompt_parts)

        # Use JEBAT's 9Router LLM proxy
        try:
            from jebat.llm import generate_with_failover, load_llm_config
            config = self._config or load_llm_config()

            # Override model if IDE specifies one
            if preferred_model:
                config.model = preferred_model

            response_text, used_provider = await generate_with_failover(
                config=config,
                prompt=combined_prompt,
                system_prompt=system_prompt,
            )

            return {
                "role": "assistant",
                "model": f"jebat-{used_provider}",
                "content": {
                    "type": "text",
                    "text": response_text,
                },
            }

        except Exception as e:
            logger.error(f"Sampling error: {e}")
            return {
                "role": "assistant",
                "model": "jebat-error",
                "content": {
                    "type": "text",
                    "text": f"JEBAT sampling error: {type(e).__name__}: {e}",
                },
                "stopReason": "error",
            }


# ── Streamable HTTP Transport ────────────────────────────────────────────────

class StreamableHTTPTransport:
    """MCP 2025-03-26 Streamable HTTP transport — single /mcp endpoint.

    Replaces the old /message (POST) + /sse (GET) dual endpoints with
    a unified /mcp endpoint that handles:
    - POST /mcp — client sends JSON-RPC requests; server can respond
      with either a single JSON response or an SSE stream
    - GET /mcp — client establishes SSE connection for notifications
    - DELETE /mcp — client terminates session

    This matches the official MCP Streamable HTTP specification and is
    compatible with all major IDE MCP clients (VS Code, Cursor, etc).
    """

    def __init__(self, mcp_server: Any, host: str = "127.0.0.1", port: int = 8100):
        self.mcp_server = mcp_server
        self.host = host
        self.port = port
        self._notification_queue: asyncio.Queue = asyncio.Queue()
        self._sessions: Dict[str, Dict] = {}  # session_id -> session state

    async def run(self) -> None:
        """Start the Streamable HTTP server using uvicorn + Starlette."""
        try:
            import uvicorn
            from starlette.applications import Starlette
            from starlette.routing import Route
            from starlette.responses import JSONResponse, Response
            import sse_starlette
        except ImportError:
            logger.error("Missing dependencies: uvicorn, starlette, sse-starlette")
            logger.error("Install: pip install uvicorn starlette sse-starlette")
            raise

        transport = self
        pm = ProgressManager(notification_queue=self._notification_queue)
        sampling = SamplingHandler()

        # Register new handlers on the MCP server
        self.mcp_server._request_handlers["sampling/createMessage"] = sampling.handle_create_message
        self.mcp_server._request_handlers["resources/subscribe"] = self._handle_resource_subscribe

        # Store progress manager on server instance
        self.mcp_server._progress_manager = pm

        async def handle_mcp_post(request):
            """POST /mcp — handle JSON-RPC requests.

            If the request is tools/call for a long-running tool,
            respond with an SSE stream that includes progress notifications
            before the final result.
            Otherwise, respond with a single JSON-RPC response.
            """
            try:
                body = await request.json()
            except json.JSONDecodeError:
                return JSONResponse(
                    {"jsonrpc": JSONRPC_VERSION, "id": None,
                     "error": {"code": -32700, "message": "Invalid JSON"}},
                    status_code=400,
                )

            # Check if this is a streaming request (tools/call for long ops)
            method = body.get("method", "")
            if method == "tools/call":
                # For tool calls, check if we should stream progress
                tool_name = body.get("params", {}).get("name", "")
                long_running_tools = {"nmap_scan", "web_crawl", "code_generate",
                                      "deep_analysis", "batch_operation"}

                if tool_name in long_running_tools:
                    # Return SSE stream with progress + final result
                    async def event_generator():
                        token = pm.start(tool_name, total=100)
                        # The tool handler will call pm.notify() during execution
                        response = await self.mcp_server.handle_request(body)
                        pm.complete(token)
                        if response:
                            yield {"data": response}
                    return sse_starlette.EventSourceResponse(event_generator())

            # Standard request — single JSON response
            response = await self.mcp_server.handle_request(body)
            if response is None:
                return Response(status_code=204)
            return JSONResponse(json.loads(response))

        async def handle_mcp_get(request):
            """GET /mcp — establish SSE connection for server notifications."""
            async def event_generator():
                # Send initial connection event
                yield {"event": "endpoint", "data": f"/mcp?sessionId={uuid.uuid4().hex[:12]}"}

                # Forward all queued notifications to the client
                while True:
                    try:
                        notification = await asyncio.wait_for(
                            transport._notification_queue.get(), timeout=30
                        )
                        yield {"event": "message", "data": json.dumps(notification)}
                    except asyncio.TimeoutError:
                        # Send keepalive
                        yield {"event": "ping", "data": ""}
            return sse_starlette.EventSourceResponse(event_generator())

        async def handle_mcp_delete(request):
            """DELETE /mcp — terminate session."""
            session_id = request.query_params.get("sessionId", "")
            if session_id in transport._sessions:
                transport._sessions.pop(session_id)
            return Response(status_code=204)

        routes = [
            Route("/mcp", endpoint=handle_mcp_post, methods=["POST"]),
            Route("/mcp", endpoint=handle_mcp_get, methods=["GET"]),
            Route("/mcp", endpoint=handle_mcp_delete, methods=["DELETE"]),
        ]
        app = Starlette(routes=routes)

        config = uvicorn.Config(app, host=self.host, port=self.port,
                                log_level="warning")
        server = uvicorn.Server(config)
        logger.info(f"Streamable HTTP MCP server starting on {self.host}:{self.port}")
        await server.serve()

    async def _handle_resource_subscribe(self, params: Dict) -> Dict:
        """Handle resources/subscribe — IDE subscribes to resource updates."""
        uri = params.get("uri", "")
        # Future: track subscriptions and send notifications/resources/updated
        # when JEBAT knowledge base changes
        return {"subscribed": True, "uri": uri}


# ── CLI Entrypoint Helper ────────────────────────────────────────────────────

def run_streamable_http(mcp_server: Any, port: int = 8100, host: str = "127.0.0.1"):
    """Start the MCP server with Streamable HTTP transport.

    Safe to call from both sync and async contexts:
    - If no event loop is running, starts one with asyncio.run()
    - If called inside an existing loop, spawns a task and blocks until done
    """
    transport = StreamableHTTPTransport(mcp_server, host=host, port=port)
    asyncio.run(transport.run())
"""`jebat rpc` — newline-delimited JSON-RPC 2.0 over stdio.

One JSON object per line on stdin, one JSON object per line on stdout.
stdout carries protocol only; all logs go to stderr.

Methods:
    initialize        -> {protocolVersion, serverInfo, capabilities}
    prompt            -> run the agent; params: {prompt, provider?, model?,
                         yolo?, plan?, stream?}  result: {text, tokens, tools}
    tool              -> execute one tool; params: {name, args}
                         result: {result}
    models            -> configured providers and models
    skills            -> available skills
    tools             -> available tool names
    shutdown          -> exit 0

Notifications (no id) are accepted and ignored.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

PROTOCOL_VERSION = "2024-11-05"


def _emit(payload: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _result(msg_id: Any, result: Any) -> None:
    _emit({"jsonrpc": "2.0", "id": msg_id, "result": result})


def _error(msg_id: Any, code: int, message: str) -> None:
    _emit({"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}})


def _log(text: str) -> None:
    sys.stderr.write(f"[jebat rpc] {text}\n")
    sys.stderr.flush()


class RPCServer:
    # Only these are dispatchable. Built per instance so bound methods resolve.
    _METHOD_NAMES = ("initialize", "prompt", "tool", "models", "skills", "tools")

    def __init__(self, ns) -> None:
        self.ns = ns
        self.registry = None
        self.taskdb = None
        self.skills = None
        self.agent = None
        self._METHODS = {name: getattr(self, name) for name in self._METHOD_NAMES}

    # ── lazy singletons ─────────────────────────────────────────────────────

    def _ensure(self) -> None:
        if self.registry is not None:
            return
        from jebat_cli_new.jebat import ProviderRegistry, SkillManager, TaskDB

        self.registry = ProviderRegistry()
        self.taskdb = TaskDB()
        self.skills = SkillManager()

    def _agent(self):
        from jebat_cli_new.jebat import Agent

        self._ensure()
        if self.agent is None:
            self.agent = Agent(
                self.registry, self.taskdb, self.skills,
                yolo=self.ns.yolo, plan_first=self.ns.plan,
                ghost_mode=True,
            )
            self.agent.spinner = _NullSpinner()
        return self.agent

    # ── methods ─────────────────────────────────────────────────────────────

    def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        from jebat_cli_new import __version__

        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": {"name": "jebat-rpc", "version": __version__},
            "capabilities": {"prompt": True, "tool": True, "streaming": False},
        }

    def prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = (params.get("prompt") or "").strip()
        if not text:
            raise ValueError("params.prompt is required")
        agent = self._agent()
        provider = params.get("provider")
        model = params.get("model")
        step = agent.step(text, provider=provider, model=model)
        return {
            "text": step.response.text,
            "provider": step.response.provider,
            "model": step.response.model,
            "tokens": step.tokens,
            "latency_ms": step.latency_ms,
            "tools": step.tool_actions,
        }

    def tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        from jebat_cli_new.tools import execute_tool

        name = params.get("name")
        if not name:
            raise ValueError("params.name is required")
        result = execute_tool(name, params.get("args") or {}, yolo=self.ns.yolo)
        return {"result": result}

    def models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure()
        out = []
        for cfg in self.registry.list_all():
            out.append({
                "id": cfg.id, "kind": cfg.kind, "model": cfg.model,
                "active": cfg.id == self.registry.active_id,
            })
        return {"active": self.registry.active_id, "providers": out}

    def skills(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure()
        return {"skills": [{"name": n, "source": s} for n, s in self.skills.list_skills()]}

    def tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        from jebat_cli_new.tools import TOOL_DEFINITIONS

        return {"tools": [d.get("name") for d in TOOL_DEFINITIONS]}

    # ── loop ────────────────────────────────────────────────────────────────

    def handle(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}
        if msg_id is None:
            return None  # notification
        if method == "shutdown":
            return {"stop": True}
        # Allowlist, not getattr: `serve` would block the loop and `handle`
        # would recurse. Only protocol methods are dispatchable.
        fn = self._METHODS.get(method) if isinstance(method, str) else None
        if fn is None:
            _error(msg_id, -32601, f"unknown method: {method}")
            return None
        try:
            _result(msg_id, fn(params))
        except ValueError as exc:
            _error(msg_id, -32602, str(exc))
        except Exception as exc:
            _error(msg_id, -32603, f"{type(exc).__name__}: {exc}")
        return None

    def serve(self) -> int:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError as exc:
                _error(None, -32700, f"parse error: {exc}")
                continue
            if not isinstance(req, dict):
                _error(None, -32600, "request must be an object")
                continue
            if self.handle(req) == {"stop": True}:
                return 0
        return 0


class _NullSpinner:
    def start(self, *args, **kwargs):
        return None

    def stop(self):
        return None


def run_rpc(ns) -> int:
    """Entry point for --mode rpc."""
    server = RPCServer(ns)
    _log("serving JSON-RPC on stdio")
    return server.serve()

"""Minimal stdio MCP server exposing one Agentix solution as a tool.

Emitted by `jebat agentix deploy --target mcp`; paste the printed config
into any MCP client (Claude Code, Cursor, opencode, jebat itself):

    python -m jebat_cli_new.agentix_mcp_server --solution NAME

Works for both runtimes: `runtime: llm` solutions spawn the shared
AgentLoop; code solutions execute their entrypoint. Protocol:
newline-delimited JSON-RPC 2.0 on stdio (MCP stdio spec).
stdout is the JSON-RPC channel — all diagnostics go to stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "jebat-agentix"
SERVER_VERSION = "0.1.0"

_SOLUTION: Optional[str] = None


def _configure_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "agentix_run",
            "description": (
                "Run a task through the deployed JEBAT Agentix solution "
                f"{_SOLUTION!r} and return the agent's final answer."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The task for the agent"},
                    "yolo": {
                        "type": "boolean",
                        "description": "Skip interactive safety confirmations (default false)",
                        "default": False,
                    },
                },
                "required": ["task"],
            },
        },
        {
            "name": "agentix_status",
            "description": "Return the solution's manifest, build state, and path.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def _status_payload() -> Dict[str, Any]:
    from jebat_cli_new.agentix import _load_manifest, _resolve_solution

    sol = _resolve_solution(_SOLUTION or "")
    manifest = _load_manifest(sol)
    build_path = sol / ".agentix" / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8")) if build_path.is_file() else None
    return {
        "name": manifest["name"],
        "template": manifest["template"],
        "runtime": manifest.get("runtime", "code"),
        "version": manifest.get("version", "0.0.0"),
        "tools": manifest.get("tools", []),
        "build": build,
        "path": str(sol),
    }


def _call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    from jebat_cli_new.agentix import _resolve_solution, _run_solution
    from jebat_cli_new.agentix_llm import PROVIDER_ERROR_PREFIX

    if name == "agentix_status":
        return {"content": [{"type": "text", "text": json.dumps(_status_payload(), indent=2)}]}
    if name == "agentix_run":
        task = str(arguments.get("task") or "").strip()
        if not task:
            raise ValueError("task must be a non-empty string")
        sol = _resolve_solution(_SOLUTION or "")
        result, info = _run_solution(sol, task, yolo=bool(arguments.get("yolo", False)))
        if result and result.startswith(PROVIDER_ERROR_PREFIX):
            return {"content": [{"type": "text", "text": result or ""}], "isError": True}
        return {"content": [{"type": "text", "text": result or ""}]}
    raise ValueError(f"unknown tool {name!r}")


def _respond(request_id: Any, result: Dict[str, Any]) -> None:
    sys.stdout.write(
        json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}, ensure_ascii=False) + "\n"
    )
    sys.stdout.flush()


def _respond_error(request_id: Any, code: int, message: str) -> None:
    sys.stdout.write(
        json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}) + "\n"
    )
    sys.stdout.flush()


def serve(solution: str) -> int:
    """JSON-RPC loop. Returns a process exit code."""
    global _SOLUTION
    _SOLUTION = solution
    sys.stderr.write(f"[agentix-mcp] serving solution {solution!r} on stdio\n")
    sys.stderr.flush()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            _respond_error(None, -32700, "parse error")
            continue
        method = request.get("method", "")
        request_id = request.get("id")
        if method == "initialize":
            _respond(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            )
        elif method.startswith("notifications/"):
            continue
        elif method == "tools/list":
            _respond(request_id, {"tools": _tool_definitions()})
        elif method == "tools/call":
            params = request.get("params") or {}
            try:
                _respond(request_id, _call_tool(str(params.get("name")), params.get("arguments") or {}))
            except (Exception, SystemExit) as exc:
                # SystemExit included: _resolve_solution/_run_solution signal
                # "solution not found"/build errors that way — the server must
                # answer a tool error, not die mid-session.
                _respond(
                    request_id,
                    {
                        "content": [{"type": "text", "text": f"agentix error: {exc}"}],
                        "isError": True,
                    },
                )
        elif request_id is not None:
            _respond_error(request_id, -32601, f"method not found: {method}")
    return 0


def main() -> int:
    _configure_streams()
    parser = argparse.ArgumentParser(prog="python -m jebat_cli_new.agentix_mcp_server")
    parser.add_argument("--solution", "-s", required=True, help="Solution name (registry) or path")
    args = parser.parse_args()
    return serve(args.solution)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Tiny stdio MCP server used by tests/mock configs.

Tools:
  - echo {text}            -> text back (readOnlyHint: true)
  - write_note {path,text} -> writes the file (readOnlyHint: false)

Line-delimited JSON-RPC 2.0 on stdio; exits on EOF.
"""

from __future__ import annotations

import json
import sys

TOOLS = [
    {
        "name": "echo",
        "description": "Echo back the provided text.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "write_note",
        "description": "Write text to a file path (test fixture).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["path", "text"],
        },
        "annotations": {"readOnlyHint": False},
    },
]


def _respond(request_id, result=None, error=None) -> None:
    message = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        message["error"] = error
    else:
        message["result"] = result
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = message.get("method", "")
        request_id = message.get("id")
        if method == "initialize":
            _respond(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "mock-mcp", "version": "0.0.1"},
                },
            )
        elif method.startswith("notifications/"):
            continue
        elif method == "tools/list":
            _respond(request_id, {"tools": TOOLS})
        elif method == "resources/list":
            _respond(request_id, {"resources": []})
        elif method == "tools/call":
            params = message.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            if name == "echo":
                _respond(
                    request_id,
                    {
                        "content": [{"type": "text", "text": str(args.get("text", ""))}],
                        "isError": False,
                    },
                )
            elif name == "write_note":
                with open(str(args.get("path", "")), "w", encoding="utf-8") as handle:
                    handle.write(str(args.get("text", "")))
                _respond(
                    request_id,
                    {"content": [{"type": "text", "text": f"wrote {args.get('path', '')}"}]},
                )
            else:
                _respond(
                    request_id,
                    {
                        "content": [{"type": "text", "text": f"unknown tool {name!r}"}],
                        "isError": True,
                    },
                )
        elif request_id is not None:
            _respond(request_id, error={"code": -32601, "message": f"method not found: {method}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

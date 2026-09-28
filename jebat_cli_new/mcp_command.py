"""`jebat mcp` subcommand — MCP server management for IDE integration.

The canonical `jebat` entrypoint (jebat_cli_new) historically had no `mcp`
branch, so `.cursor/mcp.json` / `.vscode/mcp.json` / `.windsurf/mcp.json`
calling `jebat mcp serve --transport stdio` fell through to the one-shot
prompt path, printed the banner on stdout, and broke the JSON-RPC stream.
This module gives that path a real implementation.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence


def _configure_streams() -> None:
    """Force UTF-8 on stdio pipes (Windows defaults to cp1252)."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def run_mcp_command(tokens: Sequence[str]) -> int:
    """Dispatch `jebat mcp ...`. Returns a process exit code."""
    parser = argparse.ArgumentParser(
        prog="jebat mcp",
        description="MCP server management (IDE integration).",
    )
    sub = parser.add_subparsers(dest="command")

    serve = sub.add_parser("serve", help="Start JEBAT as MCP server (for IDE integration)")
    serve.add_argument(
        "--transport", "-t",
        default="stdio",
        choices=["stdio", "http", "streamable-http"],
        help="Transport mode (stdio for IDEs, http for remote, streamable-http for MCP 2025-03-26)",
    )
    serve.add_argument("--port", "-p", type=int, default=8099, help="HTTP port (for http transport)")
    serve.add_argument("--host", default="127.0.0.1", help="HTTP host (for http transport)")

    sub.add_parser("ide-config", help="Print IDE MCP configuration templates")

    args = parser.parse_args(list(tokens))

    if args.command == "serve":
        _configure_streams()
        # Status goes to stderr — stdout is the JSON-RPC channel for stdio.
        if args.transport == "stdio":
            sys.stderr.write(
                "[JEBAT MCP] serving on stdio "
                "(tools trimmed by JEBAT_MCP_TOOLS_ALLOW if set)\n"
            )
        else:
            sys.stderr.write(
                f"[JEBAT MCP] serving on {args.transport} "
                f"{args.host}:{args.port}\n"
            )
        sys.stderr.flush()

        from jebat.features.mcp.mcp_server import run_server

        run_server(transport=args.transport, port=args.port, host=args.host)
        return 0

    if args.command == "ide-config":
        from jebat.features.mcp.mcp_server import print_ide_configs

        _configure_streams()
        print_ide_configs()
        return 0

    parser.print_help(sys.stderr)
    return 2

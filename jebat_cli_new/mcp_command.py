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
from pathlib import Path
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

    pair = sub.add_parser("pair", help="Detect installed IDEs and merge JEBAT MCP configuration")
    pair.add_argument("--ide", choices=["auto", "kiro", "cursor", "vscode", "windsurf"], default="auto")
    pair.add_argument("--list", action="store_true", help="List detected IDEs without changing files")

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

    if args.command == "pair":
        from jebat_cli_new.ide_integration import installed_ides, merge_server, IDE_PATHS

        selected = installed_ides() if args.ide == "auto" else [args.ide]
        if args.list:
            print("\n".join(selected) if selected else "No supported IDE configuration directories detected.")
            return 0
        if not selected:
            print("No supported IDE configuration directories detected; no files changed.")
            return 0
        failures = 0
        for ide in selected:
            path = Path.home() / IDE_PATHS[ide][0]
            try:
                status = merge_server(path, "jebat", ["mcp", "serve", "--transport", "stdio"])
                print(f"{ide}: {status} {path}")
            except (OSError, ValueError) as exc:
                failures += 1
                print(f"{ide}: ERROR: {exc}", file=sys.stderr)
        if not failures:
            print("Restart or reconnect the IDE. In Kiro Chat, use # → plan-act-verify-remember.")
        return 1 if failures else 0

    if args.command == "ide-config":
        from jebat.features.mcp.mcp_server import print_ide_configs

        _configure_streams()
        print_ide_configs()
        return 0

    parser.print_help(sys.stderr)
    return 2

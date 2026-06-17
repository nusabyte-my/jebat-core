"""Catalyst CLI — command handlers for tracing and observability.

Usage:
    jebat catalyst init --gateway   # Initialize with Gateway
    jebat catalyst instrument       # Auto-instrument JEBAT
    jebat catalyst trace "agent.search" # Start a trace
    jebat catalyst halo t1 t2 --type full # HALO analysis
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Optional

from jebat.features.catalyst.catalyst_integration import CatalystClient, create_catalyst_client


class CatalystCommand:
    """CLI command handler for Catalyst tracing operations."""

    def __init__(self):
        self.client: Optional[CatalystClient] = None

    async def _ensure_client(self) -> CatalystClient:
        if self.client is None:
            self.client = await create_catalyst_client()
        return self.client

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        """Register catalyst subcommands on an argparse subparsers group."""
        cat_parser = subparsers.add_parser("catalyst", help="Catalyst tracing and observability")
        cat_sub = cat_parser.add_subparsers(dest="catalyst_cmd")

        # init
        init_p = cat_sub.add_parser("init", help="Initialize Catalyst")
        init_p.add_argument("--gateway", action="store_true", help="Initialize with Gateway")

        # instrument
        cat_sub.add_parser("instrument", help="Auto-instrument JEBAT components")

        # trace
        trace_p = cat_sub.add_parser("trace", help="Start a named trace")
        trace_p.add_argument("name", help="Trace name")

        # status
        cat_sub.add_parser("status", help="Check instrumentation status")

        # list
        list_p = cat_sub.add_parser("list", help="List recent traces")
        list_p.add_argument("--limit", type=int, default=10, help="Max traces to show")

        # halo
        halo_p = cat_sub.add_parser("halo", help="HALO analysis between two traces")
        halo_p.add_argument("trace_a", help="Start trace ID")
        halo_p.add_argument("trace_b", help="End trace ID")
        halo_p.add_argument("--type", default="full", help="Analysis type: full, performance, correctness")

    async def handle(self, args: argparse.Namespace) -> str:
        """Route to the appropriate handler."""
        cmd = getattr(args, "catalyst_cmd", None)
        if not cmd:
            return "Usage: jebat catalyst <command>"

        client = await self._ensure_client()
        handlers = {
            "init": self._init,
            "instrument": self._instrument,
            "trace": self._trace,
            "status": self._status,
            "list": self._list,
            "halo": self._halo,
        }
        handler = handlers.get(cmd)
        if not handler:
            return f"Unknown catalyst command: {cmd}"
        return await handler(client, args)

    async def _init(self, client: CatalystClient, args: argparse.Namespace) -> str:
        result = await client.instrument()
        mode = "Gateway-integrated" if args.gateway else "Standalone"
        components = ", ".join(result.get("components", []))
        return f"Catalyst initialized ({mode})\nInstrumented: {components}"

    async def _instrument(self, client: CatalystClient, args: argparse.Namespace) -> str:
        result = await client.instrument()
        components = ", ".join(result.get("components", []))
        return f"Catalyst instrumentation active: {components}"

    async def _trace(self, client: CatalystClient, args: argparse.Namespace) -> str:
        span = await client.start_span(name=args.name)
        return f"Trace started: {span.trace_id}\nSpan: {span.id}"

    async def _status(self, client: CatalystClient, args: argparse.Namespace) -> str:
        stats = client.get_stats()
        lines = [
            "Catalyst — Status",
            f"  Instrumented:    {stats['instrumented']}",
            f"  Total traces:    {stats['total_traces']}",
            f"  Total spans:     {stats['total_spans']}",
            f"  Active spans:    {stats['active_spans']}",
            f"  Completed:       {stats['completed_traces']}",
        ]
        return "\n".join(lines)

    async def _list(self, client: CatalystClient, args: argparse.Namespace) -> str:
        traces = await client.list_traces(limit=args.limit)
        if not traces:
            return "No traces recorded yet."
        lines = [f"Recent Traces ({len(traces)}):"]
        for t in traces:
            lines.append(f"  {t.id}  {t.name:<25s}  spans={len(t.spans)}")
        return "\n".join(lines)

    async def _halo(self, client: CatalystClient, args: argparse.Namespace) -> str:
        result = await client.halo_analysis(
            trace_id_start=args.trace_a,
            trace_id_end=args.trace_b,
            analysis_type=args.type,
        )
        if "error" in result:
            return f"HALO error: {result['error']}"

        lines = [f"HALO Analysis ({result['analysis_type']}):"]
        a = result["trace_a"]
        b = result["trace_b"]
        lines.append(f"  Trace A: {a['id']}  spans={a['spans']}  duration={a['total_duration_ms']}ms")
        lines.append(f"  Trace B: {b['id']}  spans={b['spans']}  duration={b['total_duration_ms']}ms")
        cmp = result["comparison"]
        lines.append(f"  Duration change: {cmp['duration_change_pct']}%")
        for rec in result.get("recommendations", []):
            lines.append(f"  → {rec}")
        return "\n".join(lines)


def run_catalyst_command(args: argparse.Namespace) -> None:
    """Entry point for catalyst CLI commands."""
    cmd = CatalystCommand()
    result = asyncio.run(cmd.handle(args))
    print(result)

"""Project-scoped AutoMimpi, SelfLearn, advisor, and KB commands."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Sequence


def run_learning_command(tokens: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="jebat learning", description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("analyze", help="Analyze active project evidence")
    dream = sub.add_parser("dream", help="Consolidate active project evidence and persist a KB report")
    dream.add_argument("--force", action="store_true")
    advice = sub.add_parser("advise", help="Generate cited, deterministic advice; no model calls")
    advice.add_argument("--focus", default="")
    advice.add_argument("--limit", type=int, default=5)
    sub.add_parser("status", help="Show dream and project KB status")
    search = sub.add_parser("search", help="Search project learning records")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--kind", choices=["dream", "advice"], default="")
    search.add_argument("--limit", type=int, default=10)
    feedback = sub.add_parser("feedback", help="Record an explicit reviewer decision")
    feedback.add_argument("record_id")
    feedback.add_argument("outcome", choices=["helpful", "unhelpful", "dismissed"])
    feedback.add_argument("--evidence", required=True)
    args = parser.parse_args(list(tokens))
    from jebat.tools import automimpi_tools as tools

    async def invoke():
        if args.action == "analyze":
            return await tools.selflearn_analyze()
        if args.action == "dream":
            return await tools.mimpi_dream(force=args.force)
        if args.action == "advise":
            return await tools.learning_advisor(args.focus, args.limit)
        if args.action == "search":
            return await tools.learning_kb_search(args.query, args.kind, args.limit)
        if args.action == "feedback":
            return await tools.learning_feedback(args.record_id, args.outcome, args.evidence)
        return {"dream": await tools.mimpi_status(), "kb": await tools.learning_kb_status()}

    try:
        result = asyncio.run(invoke())
    except (ValueError, TypeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 2
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 1 if result.get("status") in {"error", "partial"} else 0

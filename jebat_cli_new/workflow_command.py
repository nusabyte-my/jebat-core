"""Inspect shared operator playbooks without starting agents or tools."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from jebat.workflows import WORKFLOWS, render_workflow


def run_workflow_command(tokens: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="jebat workflow", description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    listing = sub.add_parser("list", help="List available playbooks")
    listing.add_argument("--json", action="store_true")
    showing = sub.add_parser("show", help="Render a playbook; does not execute it")
    showing.add_argument("name", choices=WORKFLOWS)
    showing.add_argument("--task", required=True, help="Objective, or - to read stdin")
    showing.add_argument("--scope", default="the current workspace")
    showing.add_argument("--json", action="store_true")
    args = parser.parse_args(list(tokens) or ["list"])
    if args.action == "list":
        items = [{"name": name, "description": value[0]} for name, value in WORKFLOWS.items()]
        print(json.dumps(items, ensure_ascii=False) if args.json else "\n".join(
            f"{item['name']}: {item['description']}" for item in items
        ))
        return 0
    task = sys.stdin.read() if args.task == "-" else args.task
    try:
        text = render_workflow(args.name, task, args.scope)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"name": args.name, "text": text}, ensure_ascii=False) if args.json else text)
    return 0

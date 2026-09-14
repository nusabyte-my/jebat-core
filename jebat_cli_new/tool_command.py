"""Direct shared-tool command for automation and agent interoperability."""

from __future__ import annotations

import json
import sys
from typing import Sequence

from jebat_cli_new.tool_bridge import execute_shared_tool, shared_tool_definitions


def _option_value(tokens: Sequence[str], option: str) -> str | None:
    """Return one option value from a command token sequence."""
    try:
        index = tokens.index(option)
    except ValueError:
        return None
    if index + 1 >= len(tokens):
        raise ValueError(f"{option} requires a value")
    return tokens[index + 1]


def run_tool_command(tokens: Sequence[str]) -> int:
    """List or invoke shared JEBAT tools with an optional JSON envelope."""
    action = tokens[0] if tokens else "list"
    machine_output = "--json" in tokens
    if action == "list":
        definitions = shared_tool_definitions()
        if machine_output:
            print(json.dumps(definitions, ensure_ascii=False))
        else:
            for definition in definitions:
                print(f"{definition['name']}\t{definition['description']}")
        return 0
    if action != "call" or len(tokens) < 2:
        print("Usage: jebat tool [list|call <name> --args '{...}' [--json] [--yolo]]", file=sys.stderr)
        return 2

    name = tokens[1]
    try:
        raw_arguments = _option_value(tokens[2:], "--args") or "{}"
        arguments = json.loads(raw_arguments)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Tool arguments error: {exc}", file=sys.stderr)
        return 2
    if not isinstance(arguments, dict):
        print("Tool arguments error: --args must contain a JSON object", file=sys.stderr)
        return 2

    result = execute_shared_tool(name, arguments, yolo="--yolo" in tokens)
    if machine_output:
        print(json.dumps({"tool": name, "result": result}, ensure_ascii=False))
    else:
        print(result)
    return 0

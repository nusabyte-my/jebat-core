"""Tool handler for the REPL — dispatches tool invocations through the registry."""

from typing import Any

from ..tools import get_tool


def handle_tool_call(tool_name: str, args: dict[str, Any]) -> str:
    """Look up tool in registry, execute, return result string."""
    tool = get_tool(tool_name)
    if tool is None:
        return f"Unknown tool: {tool_name}"

    try:
        result = tool["handler"](**args)
    except TypeError as e:
        return f"Tool argument error for '{tool_name}': {e}"
    except Exception as e:
        return f"Tool error for '{tool_name}': {e}"

    if isinstance(result, dict):
        if result.get("error"):
            return f"[{tool_name}] error: {result['error']}"
        # Compact dict representation
        return f"[{tool_name}] {_format_result(result)}"

    return f"[{tool_name}] {result}"


def _format_result(d: dict[str, Any]) -> str:
    """Pretty-print a dict result, skipping large content fields."""
    parts = []
    for k, v in sorted(d.items()):
        if k in ("content", "matches", "backup"):
            if isinstance(v, str) and len(v) > 60:
                v = v[:57] + "..."
            elif isinstance(v, list):
                v = f"[{len(v)} items]"
        parts.append(f"{k}={v}")
    return ", ".join(parts)
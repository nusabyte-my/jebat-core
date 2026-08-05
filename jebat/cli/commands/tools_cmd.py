"""
Tools command — List and inspect registered tools.
"""

from __future__ import annotations

from typing import Any

from jebat.tools import TOOL_REGISTRY, list_tools
try:
    from jebat.core.agent_runtime import ToolDispatcher
except ImportError:
    ToolDispatcher = None


def _ensure_tools_loaded():
    """Ensure all tools are loaded."""
    dispatcher = ToolDispatcher(None, None)
    dispatcher.ensure_tools_loaded()


def tools_command(args: Any) -> int:
    """List and inspect registered tools."""
    _ensure_tools_loaded()

    if args.tools_command == "list":
        tools = list_tools(args.tier)
        if not tools:
            print("No tools found.")
        else:
            for tool in tools:
                print(f"  {tool.name:<30} {tool.safety_tier:<10} {tool.description[:60]}")
        return 0

    elif args.tools_command == "inspect":
        _ensure_tools_loaded()
        tool = TOOL_REGISTRY.get(args.name)
        if not tool:
            print(f"Tool not found: {args.name}")
            return 1
        print(f"Name: {tool.name}")
        print(f"Description: {tool.description}")
        print(f"Safety tier: {tool.safety_tier}")
        print("Parameters:")
        import json
        print(json.dumps(tool.schema, indent=2))
        return 0

    else:
        print("Usage: jebat tools {list|inspect} [...]")
        return 1

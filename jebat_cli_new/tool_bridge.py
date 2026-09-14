"""Bridge the canonical CLI agent to JEBAT's shared async tool registry."""

from __future__ import annotations

import json
from functools import partial
from typing import Any

import anyio


def _load_registry() -> dict[str, Any]:
    """Load feature modules so the shared registry contains every available tool."""
    from jebat.core.agent_loop import AgentLoop
    from jebat.tools import TOOL_REGISTRY

    loader = AgentLoop.__new__(AgentLoop)
    loader._tools_imported = False
    loader._ensure_tools_imported()
    return TOOL_REGISTRY


def shared_tool_definitions() -> list[dict[str, Any]]:
    """Return shared registry tools in the CLI agent's definition format."""
    definitions: list[dict[str, Any]] = []
    for name, tool in sorted(_load_registry().items()):
        if tool.handler is None:
            continue
        definitions.append(
            {
                "name": name,
                "description": tool.description.strip().splitlines()[0]
                if tool.description.strip()
                else f"Execute the {name} tool.",
                "parameters": tool.schema,
            }
        )
    return definitions


def shared_tool_prompt() -> str:
    """Build a compact, model-readable inventory of shared tools."""
    lines = [
        "",
        "Additional JEBAT tools are available by registered name:",
    ]
    for definition in shared_tool_definitions():
        lines.append(f"- {definition['name']}: {definition['description']}")
    return "\n".join(lines)


def execute_shared_tool(name: str, arguments: dict[str, Any], *, yolo: bool) -> str:
    """Execute one shared tool from the synchronous CLI agent boundary."""
    from jebat.tools import call_tool, classify_tool_call

    registry = _load_registry()
    tool = registry.get(name)
    if tool is None or tool.handler is None:
        return f"Unknown shared tool: {name}"

    if not yolo and classify_tool_call(name, arguments) != "auto":
        from jebat_cli_new.safety import confirm_action

        if not confirm_action(f"Run tool '{name}'", json.dumps(arguments, ensure_ascii=False)):
            return "Tool call cancelled by user."

    async def invoke() -> Any:
        return await call_tool(name, **arguments)

    try:
        result = anyio.run(invoke)
    except (KeyError, RuntimeError, TypeError, ValueError, OSError) as exc:
        return f"Tool error ({name}): {exc}"
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False, default=str)

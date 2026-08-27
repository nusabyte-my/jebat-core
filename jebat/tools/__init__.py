"""JEBAT Tool Registry — foundation for all CLI tools.

Every tool in JEBAT registers itself here with a name, handler, JSON Schema,
safety tier, timeout, and output limit. The CLI dispatches through this registry.
Plugins add tools by appending to TOOL_REGISTRY.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine


@dataclass
class ToolDef:
    """Definition of a single tool in the JEBAT tool system.

    Attributes:
        name: Unique tool name (snake_case).
        handler: Async callable that accepts **kwargs matching the schema.
        schema: JSON Schema dict describing parameters.
        safety_tier: 'auto' (no prompt), 'confirm' (Y/n), 'dangerous' (--dangerous flag).
        timeout: Default timeout in seconds.
        max_output: Max output size in bytes (0 = unlimited).
        description: Human-readable one-liner.
    """
    name: str
    handler: Callable[..., Coroutine[Any, Any, Any]] | None = None
    schema: dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})
    safety_tier: str = "auto"
    timeout: int = 30
    max_output: int = 100_000
    description: str = ""


# ── Global Registry ──────────────────────────────────────────────────────

TOOL_REGISTRY: dict[str, ToolDef] = {}


def register_tool(
    name: str,
    handler: Callable[..., Coroutine[Any, Any, Any]] | None = None,
    *,
    schema: dict[str, Any] | None = None,
    safety_tier: str = "auto",
    timeout: int = 30,
    max_output: int = 100_000,
    description: str = "",
) -> Callable:
    """Decorator or direct-call to register a tool.

    Usage as decorator:
        @register_tool("file_read", schema={...})
        async def read_file_handler(path: str, ...): ...

    Usage as function:
        register_tool("my_tool", handler=my_fn, schema=my_schema)
    """
    def _register(fn: Callable) -> Callable:
        TOOL_REGISTRY[name] = ToolDef(
            name=name,
            handler=fn,
            schema=schema or {"type": "object", "properties": {}},
            safety_tier=safety_tier,
            timeout=timeout,
            max_output=max_output,
            description=description or fn.__doc__ or "",
        )
        return fn

    if handler is not None:
        return _register(handler)
    return _register


def get_tool(name: str) -> ToolDef | None:
    """Look up a tool by name. Returns None if not found."""
    return TOOL_REGISTRY.get(name)


def list_tools(category: str | None = None) -> list[ToolDef]:
    """List all registered tools, optionally filtered by safety tier or prefix."""
    tools = list(TOOL_REGISTRY.values())
    if category:
        tools = [t for t in tools if t.name.startswith(category) or t.safety_tier == category]
    return sorted(tools, key=lambda t: t.name)


async def call_tool(name: str, **params: Any) -> Any:
    """Find and execute a tool by name with the given parameters.

    Returns the raw result from the handler. Raises KeyError if tool not found.
    """
    tool = get_tool(name)
    if tool is None:
        raise KeyError(f"Tool '{name}' not found in registry")
    return await tool.handler(**params)


# ── Safety Classification ────────────────────────────────────────────────

import re

DANGEROUS_PATTERNS: list[re.Pattern] = [
    re.compile(r'rm\s+-rf\s+/'),
    re.compile(r'dd\s+if=/dev/zero'),
    re.compile(r':\(\)\s*\{'),
    re.compile(r'chmod\s+-R\s+777\s+/'),
    re.compile(r'>\s*/dev/sd[a-z]'),
    re.compile(r'mkfs\.'),
    re.compile(r'wget.*\|\s*(sh|bash)'),
    re.compile(r'curl.*\|\s*(sh|bash)'),
    re.compile(r'sudo\s+rm'),
]

DANGEROUS_KEYWORDS = ["rm", "dd", "chmod", "sudo", "mkfs", ":(){", "> /dev/"]


def classify_command(command: str) -> str:
    """Classify a shell command into a safety tier.

    Returns 'auto', 'confirm', or 'dangerous'.
    """
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return "dangerous"
    for kw in DANGEROUS_KEYWORDS:
        if kw in command:
            return "confirm"
    return "auto"


def classify_tool_call(tool_name: str, params: dict[str, Any]) -> str:
    """Determine the effective safety tier for a tool call.

    Returns 'auto', 'confirm', or 'dangerous'.
    """
    tool = get_tool(tool_name)
    if tool is None:
        return "auto"
    base_tier = tool.safety_tier
    if base_tier != "auto":
        return base_tier
    # For terminal commands, check the actual command string
    if tool_name in ("terminal", "exec") and "command" in params:
        return classify_command(params["command"])
    return "auto"
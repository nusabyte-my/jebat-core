"""JEBAT Dynamic Tool Synthesis — Voyager-style Self-Extending Agent Harness.

Enables JEBAT to autonomously synthesize, test, and register new tools
at runtime when encountering missing capabilities.
"""

from __future__ import annotations

import ast
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from jebat.tools import register_tool, TOOL_REGISTRY

logger = logging.getLogger(__name__)

SYNTHESIZED_DIR = Path.home() / ".jebat" / "synthesized_tools"
SYNTHESIZED_DIR.mkdir(parents=True, exist_ok=True)


class SynthesizeToolInput(BaseModel):
    name: str = Field(..., description="Unique snake_case tool name (e.g. 'calculate_growth_rate')")
    code: str = Field(..., description="Complete Python code containing the tool function. Must define async def or def with matching name.")
    description: str = Field(..., description="Clear one-sentence description of what the tool accomplishes")
    parameters: Dict[str, str] = Field(default_factory=dict, description="Map of parameter names to their type/description")


@register_tool(
    "tool_synthesize",
    schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Unique tool name (snake_case)"},
            "code": {"type": "string", "description": "Python source code defining the function"},
            "description": {"type": "string", "description": "One-sentence description"},
            "parameters": {"type": "object", "description": "Parameter name to description mapping"},
        },
        "required": ["name", "code", "description"],
    },
    safety_tier="confirm",
    timeout=30,
    description="Synthesize, validate, and dynamically register a new Python tool into JEBAT's runtime.",
)
async def tool_synthesize(
    name: str,
    code: str,
    description: str,
    parameters: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Validate Python code, execute it in a clean scope, and register as a live tool."""
    params = parameters or {}

    # 1. AST syntax validation
    try:
        tree = ast.parse(code, filename=f"<synthesized_{name}>")
    except SyntaxError as e:
        return {
            "status": "error",
            "error_type": "SyntaxError",
            "message": f"Syntax error at line {e.lineno}: {e.msg}",
            "guidance": "Fix the syntax error in your Python code and retry.",
        }

    # 2. Extract function definition
    fn_name = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_name = node.name
            break

    if not fn_name:
        return {
            "status": "error",
            "error_type": "NoFunctionFound",
            "message": "The code must define at least one top-level function.",
        }

    # 3. Execute in isolated scope
    scope: Dict[str, Any] = {}
    try:
        exec(code, scope)
    except Exception as e:
        return {
            "status": "error",
            "error_type": "ExecutionError",
            "message": f"Failed to execute code: {e}",
        }

    target_fn = scope.get(fn_name)
    if not callable(target_fn):
        return {
            "status": "error",
            "error_type": "NotCallable",
            "message": f"Extracted symbol '{fn_name}' is not callable.",
        }

    # Wrap in async if sync
    if not inspect.iscoroutinefunction(target_fn):
        orig_fn = target_fn
        async def async_wrapper(**kwargs):
            return orig_fn(**kwargs)
        handler = async_wrapper
    else:
        handler = target_fn

    # 4. Build JSON Schema
    props = {p: {"type": "string", "description": desc} for p, desc in params.items()}
    schema = {"type": "object", "properties": props}

    # 5. Register in live runtime
    register_tool(
        name=name,
        handler=handler,
        schema=schema,
        description=description,
        safety_tier="auto",
        timeout=30,
    )

    # 6. Persist to disk for cross-session longevity
    tool_file = SYNTHESIZED_DIR / f"{name}.py"
    try:
        tool_file.write_text(code, encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to persist synthesized tool {name} to disk: {e}")

    return {
        "status": "registered",
        "name": name,
        "description": description,
        "total_active_tools": len(TOOL_REGISTRY),
        "persisted_path": str(tool_file),
        "guidance": f"Tool '{name}' is now active and immediately callable in subsequent ReAct steps or via MCP.",
    }

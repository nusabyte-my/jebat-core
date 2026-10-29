"""ComfyUI bridge health for CLI and MCP."""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx

from jebat.tools import register_tool


@register_tool(
    "comfyui_health",
    schema={"type": "object", "properties": {}},
    safety_tier="auto",
    timeout=15,
    description="Check the configured workstation ComfyUI or authenticated asynchronous bridge. Does not generate an image.",
)
async def comfyui_health() -> Dict[str, Any]:
    host = os.environ.get("JEBAT_COMFYUI_HOST")
    if not host:
        return {"status": "unconfigured", "error": "JEBAT_COMFYUI_HOST is not set"}
    bridge = os.environ.get("JEBAT_COMFYUI_BRIDGE", "").lower() in {"1", "true", "yes"}
    try:
        if bridge:
            response = await httpx.AsyncClient(timeout=8).get(f"{host.rstrip('/')}/health")
        else:
            response = await httpx.AsyncClient(timeout=8).get(f"{host.rstrip('/')}/system_stats")
        response.raise_for_status()
        return {"status": "ok", "mode": "bridge" if bridge else "direct", "host": host, "response": response.json()}
    except Exception as exc:
        return {"status": "unreachable", "mode": "bridge" if bridge else "direct", "host": host, "error": str(exc)}

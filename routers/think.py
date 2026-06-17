"""UltraThink deep reasoning engine endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from jebat.features.ultra_think.core import ThinkingMode, UltraThink

router = APIRouter(prefix="/api/think", tags=["ultra-think"])

_engine = UltraThink()


class ThinkRequest(BaseModel):
    problem: str = Field(..., min_length=1, description="Problem or question to reason about")
    mode: str = Field(default="deliberate", description="Thinking mode: fast, deliberate, deep, strategic, creative, critical, custom")
    user_id: str = Field(default="default", description="User ID for memory context")
    timeout: float = Field(default=30.0, ge=0.001, le=300.0, description="Timeout in seconds")


@router.post("")
async def think(req: ThinkRequest) -> Dict[str, Any]:
    """Run deep reasoning on a problem using the specified thinking mode."""
    mode_map = {m.value: m for m in ThinkingMode}
    mode = mode_map.get(req.mode, ThinkingMode.DELIBERATE)

    result = await _engine.think(
        problem=req.problem,
        mode=mode,
        user_id=req.user_id,
        timeout=req.timeout,
    )
    return {
        "success": result.success,
        "conclusion": result.conclusion,
        "confidence": result.confidence,
        "reasoning_steps": result.reasoning_steps,
        "execution_time": result.execution_time,
        "trace_id": result.trace.trace_id,
        "mode": result.trace.mode.value,
    }


@router.get("/modes")
async def thinking_modes() -> Dict[str, Any]:
    """List available thinking modes."""
    return {
        "modes": [
            {"value": m.value, "description": m.value.replace("_", " ").title()}
            for m in ThinkingMode
        ]
    }


@router.get("/stats")
async def think_stats() -> Dict[str, Any]:
    """UltraThink engine statistics."""
    return _engine.get_stats()


@router.get("/history")
async def think_history(limit: int = 10) -> Dict[str, Any]:
    """Recent thinking session history."""
    history = await _engine.get_session_history(limit=limit)
    return {"sessions": history, "total": len(history)}

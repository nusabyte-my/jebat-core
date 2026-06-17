"""UltraLoop continuous processing engine endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from jebat.features.ultra_loop.core import UltraLoop

router = APIRouter(prefix="/api/loop", tags=["ultra-loop"])

_loop = UltraLoop(config={"cycle_interval": 5.0, "max_cycles": 0})


@router.post("/start")
async def start_loop() -> Dict[str, Any]:
    """Start the continuous processing loop."""
    if _loop._running:
        return {"status": "already_running", **_loop.get_metrics()}
    await _loop.start()
    return {"status": "started", **_loop.get_metrics()}


@router.post("/stop")
async def stop_loop() -> Dict[str, Any]:
    """Stop the continuous processing loop."""
    if not _loop._running:
        return {"status": "already_stopped", **_loop.get_metrics()}
    await _loop.stop()
    return {"status": "stopped", **_loop.get_metrics()}


@router.get("/status")
async def loop_status() -> Dict[str, Any]:
    """Current loop status and metrics."""
    return _loop.get_metrics()


@router.get("/history")
async def loop_history(limit: int = 10) -> Dict[str, Any]:
    """Recent cycle history."""
    history = await _loop.get_cycle_history(limit=limit)
    return {"cycles": history, "total": len(history)}


@router.get("/stats")
async def loop_stats() -> Dict[str, Any]:
    """Loop performance statistics."""
    return await _loop.get_statistics()

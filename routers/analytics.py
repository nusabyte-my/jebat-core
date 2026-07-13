"""Q4 analytics dashboard backend — DB-backed /analytics/* JSON endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import func, select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def _jsonify(value: Any) -> Any:
    """Make a value JSON-serializable (UUID, datetime -> str)."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


async def _session_scope() -> Any:
    """Open an async DB session + RepositoryManager, mirroring jebat_api."""
    from jebat.database.models import AsyncSessionLocal
    from jebat.database.repositories import RepositoryManager

    session = AsyncSessionLocal()
    repos = RepositoryManager(session)
    return session, repos


@router.get("/overview")
async def overview() -> Dict[str, Any]:
    """Aggregate totals across agents, memory, models, errors, and events."""
    try:
        session, repos = await _session_scope()
        try:
            from jebat.database.models import (
                AgentPerformance,
                ErrorTracking,
                ModelUsage,
                SecurityEvent,
                Task,
            )

            total_memories = (
                await repos.memory_m0.count()
                + await repos.memory_m1.count()
                + await repos.memory_m2.count()
                + await repos.memory_m3.count()
                + await repos.memory_m4.count()
            )

            task_count = await session.execute(select(func.count(Task.id)))
            agent_executions = task_count.scalar() or 0

            sr = await session.execute(
                select(func.avg(AgentPerformance.metric_value)).where(
                    AgentPerformance.metric_type == "success_rate"
                )
            )
            success_rate = sr.scalar() or 0.0

            tok = await session.execute(
                select(
                    func.coalesce(func.sum(ModelUsage.input_tokens), 0),
                    func.coalesce(func.sum(ModelUsage.output_tokens), 0),
                    func.coalesce(func.sum(ModelUsage.cost), 0),
                )
            )
            input_tokens, output_tokens, total_cost = tok.first()

            err = await session.execute(select(func.count(ErrorTracking.id)))
            error_count = err.scalar() or 0

            ev = await session.execute(select(func.count(SecurityEvent.id)))
            security_event_count = ev.scalar() or 0

            return {
                "agent_executions": agent_executions,
                "success_rate": float(success_rate),
                "total_memories": total_memories,
                "model_tokens": int(input_tokens or 0) + int(output_tokens or 0),
                "model_input_tokens": int(input_tokens or 0),
                "model_output_tokens": int(output_tokens or 0),
                "model_cost": float(total_cost or 0),
                "error_count": error_count,
                "security_event_count": security_event_count,
            }
        finally:
            await session.close()
    except Exception as e:  # noqa: BLE001
        logger.exception("analytics /overview failed")
        return {
            "agent_executions": 0,
            "success_rate": 0.0,
            "total_memories": 0,
            "model_tokens": 0,
            "model_input_tokens": 0,
            "model_output_tokens": 0,
            "model_cost": 0.0,
            "error_count": 0,
            "security_event_count": 0,
            "error": str(e),
        }


@router.get("/agents")
async def agents() -> Dict[str, Any]:
    """Per-agent performance rows (executions, success_rate, avg latency)."""
    try:
        session, repos = await _session_scope()
        try:
            from jebat.database.models import AgentPerformance

            rows = await repos.agent_performance.get_all()
            by_agent: Dict[str, Dict[str, Any]] = {}
            for r in rows:
                aid = str(r.agent_id)
                agg = by_agent.setdefault(
                    aid, {"executions": 0, "success_rates": [], "latencies": []}
                )
                if r.metric_type == "execution_time":
                    agg["executions"] += 1
                    if r.metric_value is not None:
                        agg["latencies"].append(r.metric_value)
                elif r.metric_type == "success_rate":
                    if r.metric_value is not None:
                        agg["success_rates"].append(r.metric_value)

            result = []
            for aid, agg in by_agent.items():
                sr = agg["success_rates"]
                lat = agg["latencies"]
                result.append(
                    {
                        "agent_id": aid,
                        "executions": agg["executions"],
                        "success_rate": (sum(sr) / len(sr)) if sr else None,
                        "avg_latency_ms": (sum(lat) / len(lat)) if lat else None,
                    }
                )
            return {"agents": result, "total": len(result)}
        finally:
            await session.close()
    except Exception as e:  # noqa: BLE001
        logger.exception("analytics /agents failed")
        return {"agents": [], "total": 0, "error": str(e)}


@router.get("/memory")
async def memory() -> Dict[str, Any]:
    """Counts per memory layer M0-M4."""
    try:
        session, repos = await _session_scope()
        try:
            counts = {
                "M0": await repos.memory_m0.count(),
                "M1": await repos.memory_m1.count(),
                "M2": await repos.memory_m2.count(),
                "M3": await repos.memory_m3.count(),
                "M4": await repos.memory_m4.count(),
            }
            counts["total"] = sum(counts.values())
            return counts
        finally:
            await session.close()
    except Exception as e:  # noqa: BLE001
        logger.exception("analytics /memory failed")
        return {"M0": 0, "M1": 0, "M2": 0, "M3": 0, "M4": 0, "total": 0, "error": str(e)}


@router.get("/models")
async def models() -> Dict[str, Any]:
    """Token usage + cost per model."""
    try:
        session, repos = await _session_scope()
        try:
            from jebat.database.models import Model, ModelUsage

            rows = await session.execute(
                select(
                    ModelUsage.model_id,
                    func.coalesce(func.sum(ModelUsage.input_tokens), 0),
                    func.coalesce(func.sum(ModelUsage.output_tokens), 0),
                    func.coalesce(func.sum(ModelUsage.cost), 0),
                    func.count(ModelUsage.id),
                ).group_by(ModelUsage.model_id)
            )
            result = []
            for model_id, in_tok, out_tok, cost, n in rows.all():
                name = str(model_id)
                provider = None
                try:
                    m = await repos.models.get_by_id(model_id)
                    if m is not None:
                        name = getattr(m, "model_name", name)
                        provider = getattr(m, "provider", None)
                except Exception:  # noqa: BLE001
                    pass
                result.append(
                    {
                        "model_id": str(model_id),
                        "model_name": name,
                        "provider": provider,
                        "input_tokens": int(in_tok or 0),
                        "output_tokens": int(out_tok or 0),
                        "total_tokens": int(in_tok or 0) + int(out_tok or 0),
                        "cost": float(cost or 0),
                        "usage_count": int(n or 0),
                    }
                )
            return {"models": result, "total": len(result)}
        finally:
            await session.close()
    except Exception as e:  # noqa: BLE001
        logger.exception("analytics /models failed")
        return {"models": [], "total": 0, "error": str(e)}


@router.get("/errors")
async def errors(limit: int = 50) -> Dict[str, Any]:
    """Recent ErrorTracking rows."""
    try:
        session, repos = await _session_scope()
        try:
            from jebat.database.models import ErrorTracking

            rows = await session.execute(
                select(ErrorTracking)
                .order_by(ErrorTracking.created_at.desc())
                .limit(min(limit, 200))
            )
            items = [
                {
                    "id": _jsonify(r.id),
                    "error_type": r.error_type,
                    "error_message": r.error_message,
                    "severity": str(r.severity) if r.severity is not None else None,
                    "is_resolved": r.is_resolved,
                    "created_at": _jsonify(r.created_at),
                }
                for r in rows.scalars().all()
            ]
            return {"errors": items, "total": len(items)}
        finally:
            await session.close()
    except Exception as e:  # noqa: BLE001
        logger.exception("analytics /errors failed")
        return {"errors": [], "total": 0, "error": str(e)}


@router.get("/events")
async def events(limit: int = 50) -> Dict[str, Any]:
    """Recent SecurityEvent rows."""
    try:
        session, repos = await _session_scope()
        try:
            from jebat.database.models import SecurityEvent

            rows = await session.execute(
                select(SecurityEvent)
                .order_by(SecurityEvent.created_at.desc())
                .limit(min(limit, 200))
            )
            items = [
                {
                    "id": _jsonify(r.id),
                    "event_type": r.event_type,
                    "severity": r.severity,
                    "description": r.description,
                    "is_resolved": r.is_resolved,
                    "created_at": _jsonify(r.created_at),
                }
                for r in rows.scalars().all()
            ]
            return {"events": items, "total": len(items)}
        finally:
            await session.close()
    except Exception as e:  # noqa: BLE001
        logger.exception("analytics /events failed")
        return {"events": [], "total": 0, "error": str(e)}

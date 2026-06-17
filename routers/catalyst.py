"""Catalyst Observability API router — REST endpoints for distributed tracing.

Endpoints:
    GET  /api/catalyst/status         — Catalyst system status
    POST /api/catalyst/instrument     — Auto-instrument JEBAT
    POST /api/catalyst/spans          — Start a new span
    POST /api/catalyst/spans/{id}/end — End a span
    POST /api/catalyst/spans/{id}/event — Record an event on a span
    GET  /api/catalyst/traces         — List traces
    GET  /api/catalyst/traces/{id}    — Get trace with spans
    POST /api/catalyst/halo           — Run HALO analysis between two traces
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jebat.features.catalyst.catalyst_integration import (
    CatalystClient,
    SpanKind,
    SpanStatus,
    create_catalyst_client,
)

router = APIRouter(prefix="/api/catalyst", tags=["catalyst"])

# Singleton client — initialized lazily
_client: Optional[CatalystClient] = None


async def _get_client() -> CatalystClient:
    global _client
    if _client is None:
        _client = await create_catalyst_client()
    return _client


# ─── Request models ─────────────────────────────────────────────────

class StartSpanRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Span name")
    trace_id: Optional[str] = Field(default=None, description="Parent trace ID")
    parent_id: Optional[str] = Field(default=None, description="Parent span ID")
    kind: str = Field(default="internal", description="Span kind (internal/llm/tool/agent/database/http)")
    attributes: Dict[str, Any] = Field(default_factory=dict)


class EndSpanRequest(BaseModel):
    status: str = Field(default="ok", description="Span status (ok/error/timeout)")
    attributes: Optional[Dict[str, Any]] = Field(default=None)


class RecordEventRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Event name")
    attributes: Dict[str, Any] = Field(default_factory=dict)


class HaloRequest(BaseModel):
    trace_id_start: str = Field(..., description="First trace ID for comparison")
    trace_id_end: str = Field(..., description="Second trace ID for comparison")
    analysis_type: str = Field(default="full", description="Analysis type")


# ─── Endpoints ──────────────────────────────────────────────────────

@router.get("/status", summary="Catalyst system status")
async def catalyst_status() -> Dict[str, Any]:
    """Get Catalyst system status.

    Returns the current state of the tracing subsystem including total traces,
    active spans, and overall health.
    """
    client = await _get_client()
    return client.get_stats()


@router.post("/instrument", summary="Auto-instrument JEBAT")
async def instrument() -> Dict[str, Any]:
    """Auto-instrument JEBAT for tracing.

    Patches JEBAT internals to emit spans for LLM calls, tool invocations,
    and agent workflows. Call once at startup.
    """
    client = await _get_client()
    return await client.instrument()


@router.post("/spans", summary="Start a new span")
async def start_span(req: StartSpanRequest) -> Dict[str, Any]:
    """Start a new span.

    Create a tracing span within a trace. Set `trace_id` to attach to an
    existing trace, or omit to start a new one. Use `parent_id` for nested
    spans.
    """
    client = await _get_client()
    try:
        kind = SpanKind(req.kind)
    except ValueError:
        kind = SpanKind.INTERNAL
    span = await client.start_span(
        name=req.name,
        trace_id=req.trace_id,
        parent_id=req.parent_id,
        kind=kind,
        attributes=req.attributes,
    )
    return _span_to_dict(span)


@router.post("/spans/{span_id}/end", summary="End a span")
async def end_span(span_id: str, req: EndSpanRequest) -> Dict[str, Any]:
    """End an active span and record its duration.

    Closes the span, calculates its wall-clock duration, and sets the final
    status (ok/error/timeout). Returns 404 if the span is not active.
    """
    client = await _get_client()
    try:
        status = SpanStatus(req.status)
    except ValueError:
        status = SpanStatus.OK
    span = await client.end_span(span_id=span_id, status=status, attributes=req.attributes)
    if not span:
        raise HTTPException(status_code=404, detail=f"Active span '{span_id}' not found")
    return _span_to_dict(span)


@router.post("/spans/{span_id}/event", summary="Record span event")
async def record_event(span_id: str, req: RecordEventRequest) -> Dict[str, Any]:
    """Record an event on an active span.

    Attach a timestamped event (e.g. "retry", "fallback") to a span for
    detailed debugging. Returns 404 if the span is not active.
    """
    client = await _get_client()
    recorded = await client.record_event(span_id=span_id, name=req.name, attributes=req.attributes)
    if not recorded:
        raise HTTPException(status_code=404, detail=f"Active span '{span_id}' not found")
    return {"recorded": True, "span_id": span_id, "event_name": req.name}


@router.get("/traces", summary="List traces")
async def list_traces(limit: int = 50) -> Dict[str, Any]:
    """List all traces, newest first.

    Returns a summary of each trace including name, duration, span count,
    and status.
    """
    client = await _get_client()
    traces = await client.list_traces(limit=limit)
    return {"traces": [_trace_summary(t) for t in traces], "total": len(traces)}


@router.get("/traces/{trace_id}", summary="Get trace with spans")
async def get_trace(trace_id: str) -> Dict[str, Any]:
    """Get a trace with its spans.

    Returns the full trace metadata plus every span in the trace tree,
    including timing, status, events, and attributes.
    """
    client = await _get_client()
    trace = await client.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found")
    spans = await client.get_trace_spans(trace_id)
    return {
        "trace": _trace_summary(trace),
        "spans": [_span_to_dict(s) for s in spans],
    }


@router.post("/halo", summary="HALO analysis")
async def halo_analysis(req: HaloRequest) -> Dict[str, Any]:
    """Run HALO analysis between two traces.

    Compares two traces side-by-side and generates optimization
    recommendations covering latency, token usage, and call patterns.
    """
    client = await _get_client()
    result = await client.halo_analysis(
        trace_id_start=req.trace_id_start,
        trace_id_end=req.trace_id_end,
        analysis_type=req.analysis_type,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ─── Serialization helpers ──────────────────────────────────────────

def _span_to_dict(span) -> Dict[str, Any]:
    return {
        "id": span.id,
        "trace_id": span.trace_id,
        "name": span.name,
        "kind": span.kind.value,
        "status": span.status.value,
        "start_time": span.start_time,
        "end_time": span.end_time,
        "duration_ms": span.duration_ms,
        "parent_id": span.parent_id,
        "attributes": span.attributes,
        "events": span.events,
    }


def _trace_summary(trace) -> Dict[str, Any]:
    total_duration = trace.duration_ms or sum(s.duration_ms for s in trace.spans)
    return {
        "id": trace.id,
        "name": trace.name,
        "start_time": trace.start_time,
        "end_time": trace.end_time,
        "duration_ms": round(total_duration, 2),
        "span_count": len(trace.spans),
        "status": trace.status.value,
        "metadata": trace.metadata,
    }

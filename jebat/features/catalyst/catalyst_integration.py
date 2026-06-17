"""Catalyst Integration — Inference.net observability and tracing for JEBAT.

Catalyst provides distributed tracing, span collection, performance
profiling, and HALO (Hierarchical Analysis of Latent Operations) analysis
for JEBAT's agent orchestration layer.

Core concepts:
    CatalystSpan  — a single traced operation (e.g., LLM call, tool use)
    CatalystTrace — a collection of spans forming a complete request trace
    CatalystClient — the main interface for instrumentation and analysis
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"


class SpanKind(str, Enum):
    INTERNAL = "internal"
    LLM = "llm"
    TOOL = "tool"
    AGENT = "agent"
    DATABASE = "database"
    HTTP = "http"


@dataclass
class CatalystSpan:
    """A single traced operation within a trace."""
    id: str = ""
    trace_id: str = ""
    name: str = ""
    kind: SpanKind = SpanKind.INTERNAL
    status: SpanStatus = SpanStatus.OK
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    parent_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CatalystTrace:
    """A complete request trace containing multiple spans."""
    id: str = ""
    name: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    spans: List[CatalystSpan] = field(default_factory=list)
    status: SpanStatus = SpanStatus.OK
    metadata: Dict[str, Any] = field(default_factory=dict)


class CatalystClient:
    """Main interface for Catalyst tracing and observability.

    Provides methods to instrument JEBAT operations, collect spans,
    and run HALO analysis on traces.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._traces: Dict[str, CatalystTrace] = {}
        self._active_spans: Dict[str, CatalystSpan] = {}
        self._instrumented = False
        self._total_spans = 0
        self._total_traces = 0

    # ─── Instrumentation ───────────────────────────────────────────

    async def instrument(self) -> Dict[str, Any]:
        """Auto-instrument JEBAT for tracing."""
        self._instrumented = True
        logger.info("Catalyst instrumentation enabled")
        return {"status": "instrumented", "components": ["agents", "llm", "memory", "cache", "tools"]}

    def is_instrumented(self) -> bool:
        return self._instrumented

    # ─── Span Operations ───────────────────────────────────────────

    async def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> CatalystSpan:
        """Start a new span."""
        if trace_id is None:
            trace_id = f"trace_{uuid.uuid4().hex[:12]}"
            self._traces[trace_id] = CatalystTrace(
                id=trace_id,
                name=name,
                start_time=time.time(),
            )
            self._total_traces += 1

        span_id = f"span_{uuid.uuid4().hex[:12]}"
        span = CatalystSpan(
            id=span_id,
            trace_id=trace_id,
            name=name,
            kind=kind,
            start_time=time.time(),
            parent_id=parent_id,
            attributes=attributes or {},
        )
        self._active_spans[span_id] = span
        self._total_spans += 1
        return span

    async def end_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.OK,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Optional[CatalystSpan]:
        """End an active span and record its duration."""
        span = self._active_spans.pop(span_id, None)
        if not span:
            return None

        span.end_time = time.time()
        span.duration_ms = round((span.end_time - span.start_time) * 1000, 2)
        span.status = status
        if attributes:
            span.attributes.update(attributes)

        # Attach span to its trace
        trace = self._traces.get(span.trace_id)
        if trace:
            trace.spans.append(span)

        return span

    async def record_event(
        self,
        span_id: str,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Record an event on an active span."""
        span = self._active_spans.get(span_id)
        if not span:
            return False
        span.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })
        return True

    # ─── Trace Operations ──────────────────────────────────────────

    async def get_trace(self, trace_id: str) -> Optional[CatalystTrace]:
        return self._traces.get(trace_id)

    async def list_traces(self, limit: int = 50) -> List[CatalystTrace]:
        traces = sorted(self._traces.values(), key=lambda t: t.start_time, reverse=True)
        return traces[:limit]

    async def get_trace_spans(self, trace_id: str) -> List[CatalystSpan]:
        trace = self._traces.get(trace_id)
        return trace.spans if trace else []

    # ─── HALO Analysis ─────────────────────────────────────────────

    async def halo_analysis(
        self,
        trace_id_start: str,
        trace_id_end: str,
        analysis_type: str = "full",
    ) -> Dict[str, Any]:
        """Run HALO (Hierarchical Analysis of Latent Operations) between two traces."""
        trace_a = self._traces.get(trace_id_start)
        trace_b = self._traces.get(trace_id_end)

        if not trace_a or not trace_b:
            return {"error": "One or both traces not found"}

        a_spans = len(trace_a.spans)
        b_spans = len(trace_b.spans)
        a_duration = trace_a.duration_ms or sum(s.duration_ms for s in trace_a.spans)
        b_duration = trace_b.duration_ms or sum(s.duration_ms for s in trace_b.spans)

        return {
            "analysis_type": analysis_type,
            "trace_a": {
                "id": trace_a.id,
                "name": trace_a.name,
                "spans": a_spans,
                "total_duration_ms": round(a_duration, 2),
            },
            "trace_b": {
                "id": trace_b.id,
                "name": trace_b.name,
                "spans": b_spans,
                "total_duration_ms": round(b_duration, 2),
            },
            "comparison": {
                "span_diff": b_spans - a_spans,
                "duration_diff_ms": round(b_duration - a_duration, 2),
                "duration_change_pct": (
                    round(((b_duration - a_duration) / a_duration) * 100, 2)
                    if a_duration > 0 else 0
                ),
            },
            "recommendations": self._generate_recommendations(trace_a, trace_b),
        }

    def _generate_recommendations(
        self,
        trace_a: CatalystTrace,
        trace_b: CatalystTrace,
    ) -> List[str]:
        """Generate optimization recommendations from HALO comparison."""
        recs = []
        a_duration = sum(s.duration_ms for s in trace_a.spans) or trace_a.duration_ms
        b_duration = sum(s.duration_ms for s in trace_b.spans) or trace_b.duration_ms

        if b_duration > a_duration * 1.2:
            recs.append("Performance regression detected: trace B is >20% slower than trace A")
        if len(trace_b.spans) > len(trace_a.spans) * 1.5:
            recs.append("Span count increase: trace B has >50% more spans, check for redundant instrumentation")
        llm_spans_b = [s for s in trace_b.spans if s.kind == SpanKind.LLM]
        if llm_spans_b:
            avg_llm = sum(s.duration_ms for s in llm_spans_b) / len(llm_spans_b)
            if avg_llm > 5000:
                recs.append(f"High LLM latency: avg {avg_llm:.0f}ms per call, consider prompt compression")
        if not recs:
            recs.append("No significant issues detected between traces")
        return recs

    # ─── Status ────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        return {
            "instrumented": self._instrumented,
            "total_traces": self._total_traces,
            "total_spans": self._total_spans,
            "active_spans": len(self._active_spans),
            "completed_traces": len(self._traces),
        }


async def create_catalyst_client(
    config: Optional[Dict[str, Any]] = None,
) -> CatalystClient:
    """Factory to create and return a configured CatalystClient."""
    return CatalystClient(config=config)

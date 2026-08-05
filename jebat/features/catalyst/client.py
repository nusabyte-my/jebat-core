"""Catalyst O11y — Core Client for Distributed Tracing."""

from __future__ import annotations

import contextvars
import logging
import threading
import time
import uuid
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .models import (
    CatalystSpan,
    CatalystTrace,
    SpanKind,
    SpanStatus,
    SamplingConfig,
    SamplingDecision,
    SpanEvent,
)
from .exporters.elasticsearch import ElasticsearchConfig

logger = logging.getLogger(__name__)

# Context variables for current span/trace
_current_span: contextvars.ContextVar[Optional[CatalystSpan]] = contextvars.ContextVar("current_span", default=None)
_current_trace: contextvars.ContextVar[Optional[CatalystTrace]] = contextvars.ContextVar("current_trace", default=None)


@dataclass
class CatalystConfig:
    """Catalyst client configuration."""
    service_name: str = "jebat"
    service_version: str = "7.5"
    environment: str = "development"

    # Sampling
    sampling: SamplingConfig = field(default_factory=SamplingConfig)

    # Exporters
    exporters: list[dict[str, Any]] = field(default_factory=list)

    # Elasticsearch (ELK) — off by default (empty url = skip)
    elasticsearch: ElasticsearchConfig = field(
        default_factory=lambda: ElasticsearchConfig(url="")
    )

    # Resource attributes
    resource_attributes: dict[str, Any] = field(default_factory=lambda: {
        "service.name": "jebat",
        "service.version": "7.5",
    })

    # Buffer
    buffer_size: int = 1000
    flush_interval_seconds: float = 5.0

    # Auto-instrumentation
    auto_instrument: bool = True
    instrument_llm: bool = True
    instrument_tools: bool = True
    instrument_agents: bool = True
    instrument_memory: bool = True
    instrument_cache: bool = True
    instrument_mcp: bool = True
    instrument_http: bool = True


class CatalystClient:
    """Main Catalyst observability client."""

    def __init__(self, config: Optional[CatalystConfig] = None):
        self.config = config or CatalystConfig()
        self._traces: dict[str, CatalystTrace] = {}
        self._active_spans: dict[str, CatalystSpan] = {}
        self._lock = threading.RLock()

        # Stats
        self._total_traces = 0
        self._total_spans = 0
        self._completed_traces = 0
        self._start_time = time.time()

        # Exporters
        self._exporters: list[Any] = []
        self._init_exporters()

        # Auto-instrument
        if self.config.auto_instrument:
            self._setup_auto_instrumentation()

    def _init_exporters(self) -> None:
        """Initialize configured exporters."""
        for exp_config in self.config.exporters:
            exp_type = exp_config.get("type", "stdout")
            if exp_type == "otlp_http":
                from .exporters.otlp import OTLPHTTPExporter
                self._exporters.append(OTLPHTTPExporter(exp_config))
            elif exp_type == "otlp_grpc":
                from .exporters.otlp import OTLPGRPCExporter
                self._exporters.append(OTLPGRPCExporter(exp_config))
            elif exp_type == "jaeger":
                from .exporters.jaeger import JaegerExporter
                self._exporters.append(JaegerExporter(exp_config))
            elif exp_type == "prometheus":
                from .exporters.prometheus import PrometheusExporter
                self._exporters.append(PrometheusExporter(exp_config))
            elif exp_type == "stdout":
                from .exporters.stdout import StdoutExporter
                self._exporters.append(StdoutExporter(exp_config))
            elif exp_type == "elasticsearch":
                try:
                    from .exporters.elasticsearch import ElasticsearchExporter
                    self._exporters.append(ElasticsearchExporter(self.config.elasticsearch))
                except ImportError as e:
                    logger.warning(f"Elasticsearch exporter unavailable: {e}")
            else:
                logger.warning(f"Unknown exporter type: {exp_type}")

        configured_types = {e.get("type") for e in self.config.exporters}
        if self.config.elasticsearch.url and "elasticsearch" not in configured_types:
            try:
                from .exporters.elasticsearch import ElasticsearchExporter
                self._exporters.append(ElasticsearchExporter(self.config.elasticsearch))
            except ImportError as e:
                logger.warning(f"Elasticsearch exporter unavailable: {e}")

    def _setup_auto_instrumentation(self) -> None:
        """Set up auto-instrumentation hooks."""
        # This would patch JEBAT internals
        # For now, just log that it's available
        logger.info("Catalyst auto-instrumentation enabled")

    def _should_sample(self) -> SamplingDecision:
        """Decide whether to sample this trace."""
        s = self.config.sampling
        if s.strategy == "always":
            return SamplingDecision.RECORD
        elif s.strategy == "never":
            return SamplingDecision.DROP
        elif s.strategy == "probabilistic":
            import random
            if random.random() < s.rate:
                return SamplingDecision.RECORD
            return SamplingDecision.DROP
        elif s.strategy == "tail":
            # Tail sampling decided at trace end
            return SamplingDecision.RECORD_AND_SAMPLE
        return SamplingDecision.DROP

    def start_trace(
        self,
        name: str,
        metadata: Optional[dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> CatalystTrace:
        """Start a new trace."""
        trace = CatalystTrace(
            id=trace_id or f"trace_{uuid.uuid4().hex[:16]}",
            name=name,
            metadata=metadata or {},
            resource=self.config.resource_attributes,
        )

        decision = self._should_sample()
        if decision == SamplingDecision.DROP:
            trace.metadata["_sampled"] = False
        else:
            trace.metadata["_sampled"] = True

        with self._lock:
            self._traces[trace.id] = trace
            self._total_traces += 1

        # Set as current trace
        _current_trace.set(trace)

        return trace

    def end_trace(self, trace_id: str, status: SpanStatus = SpanStatus.OK) -> Optional[CatalystTrace]:
        """End a trace and export if sampled."""
        with self._lock:
            trace = self._traces.pop(trace_id, None)

        if not trace:
            return None

        trace.end_time = time.time()
        trace.duration_ms = round((trace.end_time - trace.start_time) * 1000, 2)
        trace.status = status
        trace.metadata["_sampled"] = trace.metadata.get("_sampled", False)

        # Tail sampling decision
        if trace.metadata.get("_sampled") is None and self.config.sampling.strategy == "tail":
            should_sample = self._tail_sampling_decision(trace)
            trace.metadata["_sampled"] = should_sample
            if not should_sample:
                return None

        if trace.metadata.get("_sampled", True):
            self._export_trace(trace)
            self._completed_traces += 1

        # Clear current trace if it matches
        current = _current_trace.get()
        if current and current.id == trace_id:
            _current_trace.set(None)

        return trace

    def _tail_sampling_decision(self, trace: CatalystTrace) -> bool:
        """Decide whether to sample based on tail criteria."""
        s = self.config.sampling
        # Sample errors
        if s.tail_error_sampling and trace.status == SpanStatus.ERROR:
            return True
        # Sample high latency
        if trace.duration_ms > s.tail_latency_threshold_ms:
            return True
        return False

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> CatalystSpan:
        """Start a new span."""
        # Get or create trace
        trace_id = trace_id
        current_trace = _current_trace.get()
        if current_trace:
            trace_id = trace_id or current_trace.id

        if not trace_id:
            # Create implicit trace
            trace = self.start_trace(name)
            trace_id = trace.id

        # Determine parent
        if parent_id is None:
            current_span = _current_span.get()
            if current_span:
                parent_id = current_span.id

        span = CatalystSpan(
            trace_id=trace_id,
            name=name,
            kind=kind,
            parent_id=parent_id,
            attributes=attributes or {},
            resource=self.config.resource_attributes,
        )

        with self._lock:
            self._active_spans[span.id] = span
            self._total_spans += 1

            # Add to trace
            trace = self._traces.get(trace_id)
            if trace:
                trace.add_span(span)

        # Set as current span
        _current_span.set(span)

        return span

    def end_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.OK,
        attributes: Optional[dict[str, Any]] = None,
    ) -> Optional[CatalystSpan]:
        """End a span."""
        with self._lock:
            span = self._active_spans.pop(span_id, None)

        if not span:
            return None

        span.end(status, attributes)

        # Clear current span if it matches
        current = _current_span.get()
        if current and current.id == span_id:
            _current_span.set(None)

        return span

    @contextmanager
    def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[dict[str, Any]] = None,
    ):
        """Context manager for spans."""
        span = self.start_span(name, kind, attributes=attributes)
        try:
            yield span
            self.end_span(span.id, SpanStatus.OK)
        except Exception as e:
            self.end_span(span.id, SpanStatus.ERROR, {"error": str(e), "error_type": type(e).__name__})
            raise

    def get_current_span(self) -> Optional[CatalystSpan]:
        """Get the currently active span."""
        return _current_span.get()

    def get_current_trace(self) -> Optional[CatalystTrace]:
        """Get the currently active trace."""
        return _current_trace.get()

    def add_span_event(
        self,
        span_id: str,
        name: str,
        attributes: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Add an event to a span."""
        with self._lock:
            span = self._active_spans.get(span_id)
            if not span:
                # Check completed spans in traces
                for trace in self._traces.values():
                    span = trace.get_span(span_id)
                    if span:
                        break
            if span:
                span.add_event(name, attributes)
                return True
        return False

    def set_span_attribute(self, span_id: str, key: str, value: Any) -> bool:
        """Set an attribute on a span."""
        with self._lock:
            span = self._active_spans.get(span_id)
            if not span:
                for trace in self._traces.values():
                    span = trace.get_span(span_id)
                    if span:
                        break
            if span:
                span.set_attribute(key, value)
                return True
        return False

    def get_trace(self, trace_id: str) -> Optional[CatalystTrace]:
        """Get a trace by ID."""
        with self._lock:
            return self._traces.get(trace_id)

    def list_traces(self, limit: int = 50) -> list[CatalystTrace]:
        """List recent traces."""
        with self._lock:
            traces = sorted(
                self._traces.values(),
                key=lambda t: t.start_time,
                reverse=True,
            )
            return traces[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Get client statistics."""
        with self._lock:
            uptime = time.time() - self._start_time
            return {
                "service_name": self.config.service_name,
                "uptime_seconds": uptime,
                "total_traces": self._total_traces,
                "total_spans": self._total_spans,
                "completed_traces": self._completed_traces,
                "active_traces": len(self._traces),
                "active_spans": len(self._active_spans),
                "traces_per_second": self._total_traces / uptime if uptime > 0 else 0,
                "spans_per_second": self._total_spans / uptime if uptime > 0 else 0,
            }

    def _export_trace(self, trace: CatalystTrace) -> None:
        """Export trace to all exporters."""
        trace_dict = trace.to_dict()
        for exporter in self._exporters:
            try:
                exporter.export(trace_dict)
            except Exception as e:
                logger.error(f"Exporter {type(exporter).__name__} failed: {e}")

    def shutdown(self) -> None:
        """Shutdown client and flush."""
        # Export any remaining traces
        with self._lock:
            for trace in list(self._traces.values()):
                if trace.metadata.get("_sampled", True):
                    self._export_trace(trace)

        # Flush exporters
        for exporter in self._exporters:
            try:
                exporter.flush()
            except Exception as e:
                logger.error(f"Exporter flush failed: {e}")


# Global client instance
_global_client: Optional[CatalystClient] = None


def get_catalyst_client() -> Optional[CatalystClient]:
    """Get the global Catalyst client."""
    return _global_client


def init_catalyst(config: Optional[CatalystConfig] = None) -> CatalystClient:
    """Initialize global Catalyst client."""
    global _global_client
    _global_client = CatalystClient(config)
    return _global_client


def shutdown_catalyst() -> None:
    """Shutdown global Catalyst client."""
    global _global_client
    if _global_client:
        _global_client.shutdown()
        _global_client = None
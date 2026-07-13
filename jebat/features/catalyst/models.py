"""Catalyst O11y — Core Tracing Models."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import numpy as np


class SpanKind(str, Enum):
    """OpenTelemetry-compatible span kinds."""
    INTERNAL = "internal"
    LLM = "llm"
    TOOL = "tool"
    AGENT = "agent"
    DATABASE = "database"
    HTTP = "http"
    CACHE = "cache"
    QUEUE = "queue"
    RERANK = "rerank"
    EMBEDDING = "embedding"


class SpanStatus(str, Enum):
    """Span status."""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SpanEvent:
    """Event within a span (OpenTelemetry compatible)."""
    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanLink:
    """Link to another span (OpenTelemetry compatible)."""
    trace_id: str
    span_id: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class CatalystSpan:
    """A single traced operation (OTel-compatible)."""
    id: str = field(default_factory=lambda: f"span_{uuid.uuid4().hex[:16]}")
    trace_id: str = field(default_factory=lambda: f"trace_{uuid.uuid4().hex[:16]}")
    name: str = ""
    kind: SpanKind = SpanKind.INTERNAL
    status: SpanStatus = SpanStatus.OK
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    parent_id: Optional[str] = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[SpanEvent] = field(default_factory=list)
    links: list[SpanLink] = field(default_factory=list)
    resource: dict[str, Any] = field(default_factory=dict)

    def end(self, status: SpanStatus = SpanStatus.OK, attributes: Optional[dict[str, Any]] = None) -> None:
        """Mark span as ended."""
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status
        if attributes:
            self.attributes.update(attributes)

    def add_event(self, name: str, attributes: Optional[dict[str, Any]] = None) -> None:
        """Add an event to this span."""
        self.events.append(SpanEvent(name=name, attributes=attributes or {}))

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (OTel JSON format)."""
        return {
            "span_id": self.id,
            "trace_id": self.trace_id,
            "name": self.name,
            "kind": self.kind.value,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "parent_id": self.parent_id,
            "attributes": self.attributes,
            "events": [
                {"name": e.name, "timestamp": e.timestamp, "attributes": e.attributes}
                for e in self.events
            ],
            "links": [
                {"trace_id": l.trace_id, "span_id": l.span_id, "attributes": l.attributes}
                for l in self.links
            ],
        }


@dataclass
class CatalystTrace:
    """A complete trace containing multiple spans."""
    id: str = field(default_factory=lambda: f"trace_{uuid.uuid4().hex[:16]}")
    name: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    spans: list[CatalystSpan] = field(default_factory=list)
    status: SpanStatus = SpanStatus.OK
    metadata: dict[str, Any] = field(default_factory=dict)
    resource: dict[str, Any] = field(default_factory=dict)

    def add_span(self, span: CatalystSpan) -> None:
        """Add a span to this trace."""
        self.spans.append(span)
        self.end_time = max(self.end_time or 0, span.end_time or 0)
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2) if self.end_time else 0

        # Update trace status from spans
        if any(s.status == SpanStatus.ERROR for s in self.spans):
            self.status = SpanStatus.ERROR
        elif any(s.status == SpanStatus.TIMEOUT for s in self.spans):
            self.status = SpanStatus.TIMEOUT

    def get_span(self, span_id: str) -> Optional[CatalystSpan]:
        """Get span by ID."""
        for s in self.spans:
            if s.id == span_id:
                return s
        return None

    def get_root_spans(self) -> list[CatalystSpan]:
        """Get root spans (no parent)."""
        return [s for s in self.spans if s.parent_id is None]

    def get_child_spans(self, parent_id: str) -> list[CatalystSpan]:
        """Get child spans of a parent."""
        return [s for s in self.spans if s.parent_id == parent_id]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
            "resource": self.resource,
        }


class SamplingDecision(str, Enum):
    """Sampling decision."""
    RECORD = "record"
    DROP = "drop"
    RECORD_AND_SAMPLE = "record_and_sample"


@dataclass
class SamplingConfig:
    """Trace sampling configuration."""
    strategy: str = "probabilistic"  # probabilistic, tail, always, never
    rate: float = 0.1                # for probabilistic: 0.0-1.0
    max_traces_per_second: int = 1000  # rate limiting
    tail_latency_threshold_ms: int = 5000  # for tail sampling
    tail_error_sampling: bool = True
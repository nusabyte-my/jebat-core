"""Catalyst O11y — OTLP Exporters (HTTP & gRPC)."""

from __future__ import annotations

import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Base class for trace/metric exporters."""

    @abstractmethod
    def export(self, trace: dict[str, Any]) -> None:
        """Export a trace."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered data."""
        pass


@dataclass
class StdoutExporter(BaseExporter):
    """Export traces to stdout (JSON lines)."""

    pretty: bool = False

    def export(self, trace: dict[str, Any]) -> None:
        if self.pretty:
            print(json.dumps(trace, indent=2))
        else:
            print(json.dumps(trace))

    def flush(self) -> None:
        pass


@dataclass
class OTLPHTTPExporter(BaseExporter):
    """Export traces via OTLP/HTTP (protobuf or JSON)."""

    endpoint: str = "http://localhost:4318/v1/traces"
    headers: dict[str, str] = None
    timeout: float = 10.0
    batch_size: int = 100
    use_json: bool = True  # Use JSON instead of protobuf

    def __post_init__(self):
        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}
        self._buffer: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._client = httpx.Client(timeout=self.timeout)

    def export(self, trace: dict[str, Any]) -> None:
        with self._lock:
            self._buffer.append(trace)
            if len(self._buffer) >= self.batch_size:
                self._flush_buffer()

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return

        traces = self._buffer[:]
        self._buffer.clear()

        # Convert to OTLP format
        payload = self._to_otlp(traces)

        try:
            response = self._client.post(self.endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"OTLP HTTP export failed: {e}")
            # Re-buffer on failure
            with self._lock:
                self._buffer.extend(traces)

    def _to_otlp(self, traces: list[dict[str, Any]]) -> dict[str, Any]:
        """Convert Catalyst traces to OTLP JSON format."""
        resource_spans = []

        for trace in traces:
            resource = trace.get("resource", {})
            resource_attrs = [
                {"key": k, "value": {"stringValue": str(v)}}
                for k, v in resource.items()
            ]

            scope_spans = []
            spans_by_id = {s["span_id"]: s for s in trace.get("spans", [])}

            for span in trace.get("spans", []):
                # Convert attributes
                attrs = []
                for k, v in span.get("attributes", {}).items():
                    attrs.append({"key": k, "value": {"stringValue": str(v)}})

                # Convert events
                events = []
                for event in span.get("events", []):
                    event_attrs = []
                    for k, v in event.get("attributes", {}).items():
                        event_attrs.append({"key": k, "value": {"stringValue": str(v)}})
                    events.append({
                        "name": event["name"],
                        "timeUnixNano": str(int(event["timestamp"] * 1e9)),
                        "attributes": event_attrs,
                    })

                # Convert links
                links = []
                for link in span.get("links", []):
                    links.append({
                        "traceId": link["trace_id"],
                        "spanId": link["span_id"],
                        "attributes": [
                            {"key": k, "value": {"stringValue": str(v)}}
                            for k, v in link.get("attributes", {}).items()
                        ],
                    })

                status_code = 1 if span["status"] == "ok" else 2  # 1=OK, 2=ERROR

                scope_spans.append({
                    "spanId": span["span_id"],
                    "traceId": span["trace_id"],
                    "parentSpanId": span.get("parent_id", ""),
                    "name": span["name"],
                    "kind": self._span_kind_to_otel(span["kind"]),
                    "startTimeUnixNano": str(int(span["start_time"] * 1e9)),
                    "endTimeUnixNano": str(int(span["end_time"] * 1e9)) if span.get("end_time") else "",
                    "attributes": attrs,
                    "events": events,
                    "links": links,
                    "status": {"code": status_code},
                })

            resource_spans.append({
                "resource": {"attributes": resource_attrs},
                "scopeSpans": [{
                    "scope": {"name": "catalyst", "version": "0.1.0"},
                    "spans": scope_spans,
                }],
            })

        return {"resourceSpans": resource_spans}

    def _span_kind_to_otel(self, kind: str) -> int:
        """Map Catalyst span kind to OTel span kind."""
        mapping = {
            "internal": 0,  # UNSPECIFIED
            "llm": 3,       # CONSUMER (or custom)
            "tool": 3,
            "agent": 3,
            "database": 3,
            "http": 2,      # SERVER
            "cache": 3,
            "queue": 3,
            "rerank": 3,
            "embedding": 3,
        }
        return mapping.get(kind, 0)

    def flush(self) -> None:
        with self._lock:
            self._flush_buffer()

    def close(self) -> None:
        self.flush()
        self._client.close()


@dataclass
class OTLPGRPCExporter(BaseExporter):
    """Export traces via OTLP/gRPC (requires grpcio)."""

    endpoint: str = "localhost:4317"
    timeout: float = 10.0

    def __post_init__(self):
        try:
            import grpc
            from opentelemetry.proto.collector.trace.v1 import trace_service_pb2_grpc
            from opentelemetry.proto.trace.v1 import trace_pb2
            self._grpc = grpc
            self._trace_pb2 = trace_pb2
            self._trace_service_pb2_grpc = trace_service_pb2_grpc
            self._channel = grpc.insecure_channel(self.endpoint)
            self._stub = trace_service_pb2_grpc.TraceServiceStub(self._channel)
        except ImportError:
            logger.warning("grpcio/opentelemetry-proto not installed, OTLP gRPC disabled")
            self._stub = None

    def export(self, trace: dict[str, Any]) -> None:
        if not self._stub:
            return
        # Implementation would convert to protobuf and send
        pass

    def flush(self) -> None:
        pass


@dataclass
class JaegerExporter(BaseExporter):
    """Export traces to Jaeger (Thrift over HTTP/UDP)."""

    agent_host: str = "localhost"
    agent_port: int = 6831
    collector_endpoint: str = "http://localhost:14268/api/traces"

    def __post_init__(self):
        self._client = httpx.Client(timeout=10.0)

    def export(self, trace: dict[str, Any]) -> None:
        # Convert to Jaeger format
        jaeger_trace = self._to_jaeger(trace)

        try:
            response = self._client.post(
                self.collector_endpoint,
                json=jaeger_trace,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Jaeger export failed: {e}")

    def _to_jaeger(self, trace: dict[str, Any]) -> dict[str, Any]:
        """Convert Catalyst trace to Jaeger format."""
        spans = []
        for span in trace.get("spans", []):
            jaeger_span = {
                "traceID": span["trace_id"],
                "spanID": span["span_id"],
                "operationName": span["name"],
                "references": [],
                "startTime": int(span["start_time"] * 1_000_000),  # microseconds
                "duration": int(span["duration_ms"] * 1000),  # microseconds
                "tags": [
                    {"key": k, "type": "string", "value": str(v)}
                    for k, v in span.get("attributes", {}).items()
                ],
                "logs": [
                    {
                        "timestamp": int(e["timestamp"] * 1_000_000),
                        "fields": [
                            {"key": k, "type": "string", "value": str(v)}
                            for k, v in e.get("attributes", {}).items()
                        ],
                    }
                    for e in span.get("events", [])
                ],
            }

            if span.get("parent_id"):
                jaeger_span["references"].append({
                    "refType": "CHILD_OF",
                    "traceID": span["trace_id"],
                    "spanID": span["parent_id"],
                })

            spans.append(jaeger_span)

        return {"spans": spans}

    def flush(self) -> None:
        pass
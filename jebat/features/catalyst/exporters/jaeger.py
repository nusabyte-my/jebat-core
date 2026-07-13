"""Catalyst O11y — Jaeger Exporter."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

_thrift = None
_thrift_lock = threading.Lock()


def _get_thrift():
    global _thrift
    if _thrift is None:
        with _thrift_lock:
            if _thrift is None:
                try:
                    import jaeger_client
                    _thrift = jaeger_client
                except ImportError:
                    logger.warning("jaeger_client not installed, Jaeger export disabled")
                    return None
    return _thrift


@dataclass
class JaegerExporterConfig:
    """Configuration for Jaeger exporter."""
    agent_host: str = "localhost"
    agent_port: int = 6831
    collector_endpoint: Optional[str] = None
    service_name: str = "jebat"
    tags: dict[str, str] = None
    max_packet_size: int = 65000


class JaegerExporter:
    """Export traces to Jaeger via UDP agent or HTTP collector."""

    def __init__(self, config: JaegerExporterConfig):
        self.config = config
        self._jaeger = _get_thrift()
        self._tracer = None
        self._init_tracer()

    def _init_tracer(self) -> None:
        """Initialize Jaeger tracer."""
        if not self._jaeger:
            return

        try:
            if self.config.collector_endpoint:
                # Use collector
                self._tracer = self._jaeger.Config(
                    config={
                        "sampler": {"type": "const", "param": 1},
                        "local_agent": {
                            "reporting_host": self.config.agent_host,
                            "reporting_port": self.config.agent_port,
                        },
                        "reporter": {
                            "collector_endpoint": self.config.collector_endpoint,
                            "max_packet_size": self.config.max_packet_size,
                        },
                    },
                    service_name=self.config.service_name,
                    validate=True,
                ).initialize_tracer()
            else:
                # Use agent
                self._tracer = self._jaeger.Config(
                    config={
                        "sampler": {"type": "const", "param": 1},
                        "local_agent": {
                            "reporting_host": self.config.agent_host,
                            "reporting_port": self.config.agent_port,
                        },
                    },
                    service_name=self.config.service_name,
                    validate=True,
                ).initialize_tracer()

            logger.info(f"Jaeger tracer initialized for service {self.config.service_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Jaeger tracer: {e}")

    def export(self, trace: dict[str, Any]) -> None:
        """Export trace to Jaeger."""
        if not self._tracer:
            return

        try:
            # Convert to Jaeger span
            jaeger_span = self._tracer.start_span(
                operation_name=trace.get("name", "unknown"),
                trace_id=trace.get("trace_id", ""),
                span_id=trace.get("spans", [{}])[0].get("span_id", ""),
                references=self._build_references(trace),
                tags=self._build_tags(trace),
                start_time=int(trace.get("start_time", time.time()) * 1_000_000),
            )

            # Add logs/events
            for span in trace.get("spans", []):
                for event in span.get("events", []):
                    jaeger_span.log_kv({
                        "event": event.get("name", ""),
                        **event.get("attributes", {}),
                    }, timestamp=int(event.get("timestamp", time.time()) * 1_000_000))

            # Set duration
            end_time = trace.get("end_time")
            if end_time:
                jaeger_span.finish(finish_time=int(end_time * 1_000_000))

        except Exception as e:
            logger.error(f"Jaeger export failed: {e}")

    def _build_references(self, trace: dict) -> list:
        """Build Jaeger span references."""
        refs = []
        for span in trace.get("spans", []):
            parent_id = span.get("parent_id")
            if parent_id:
                refs.append({
                    "ref_type": "CHILD_OF",
                    "trace_id": span.get("trace_id"),
                    "span_id": parent_id,
                })
        return refs

    def _build_tags(self, trace: dict) -> dict:
        """Build Jaeger tags from trace."""
        tags = {}
        for span in trace.get("spans", []):
            for k, v in span.get("attributes", {}).items():
                if isinstance(v, (str, int, float, bool)):
                    tags[k] = v
        return tags

    def flush(self) -> None:
        """Flush any buffered spans."""
        if self._tracer:
            self._tracer.close()

    def close(self) -> None:
        """Close the tracer."""
        if self._tracer:
            self._tracer.close()
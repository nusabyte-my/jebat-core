"""Catalyst O11y — Loki Log Exporter."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx


@dataclass
class LokiConfig:
    """Loki exporter configuration."""
    enabled: bool = True
    endpoint: str = "http://localhost:3100/loki/api/v1/push"
    labels: dict[str, str] = field(default_factory=lambda: {"service": "jebat"})
    batch_size: int = 100
    timeout: float = 5.0


class LokiHandler(logging.Handler):
    """Logging handler that sends logs to Loki."""

    def __init__(self, config: LokiConfig):
        super().__init__()
        self.config = config
        self._buffer: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._client = httpx.Client(timeout=config.timeout)

    def emit(self, record: logging.LogRecord) -> None:
        """Format and buffer log record."""
        try:
            log_entry = {
                "timestamp": int(record.created * 1e9),  # nanoseconds
                "line": self.format(record),
                "level": record.levelname,
                "logger": record.name,
            }

            # Add trace context if available
            if hasattr(record, "trace_id"):
                log_entry["trace_id"] = record.trace_id
            if hasattr(record, "span_id"):
                log_entry["span_id"] = record.span_id

            # Add structured fields
            for key, value in record.__dict__.items():
                if key not in ["name", "msg", "args", "created", "filename", "funcName",
                               "levelname", "levelno", "lineno", "module", "msecs",
                               "message", "msg", "name", "pathname", "process",
                               "processName", "relativeCreated", "thread", "threadName",
                               "exc_info", "exc_text", "stack_info", "trace_id", "span_id"]:
                    log_entry[key] = value

            with self._lock:
                self._buffer.append(log_entry)
                if len(self._buffer) >= self.config.batch_size:
                    self._flush_buffer()

        except Exception:
            self.handleError(record)

    def _flush_buffer(self) -> None:
        """Send buffered logs to Loki."""
        if not self._buffer:
            return

        entries = self._buffer[:]
        self._buffer.clear()

        # Group by labels
        streams = {}
        for entry in entries:
            label_key = json.dumps(self.config.labels, sort_keys=True)
            if label_key not in streams:
                streams[label_key] = {"stream": self.config.labels, "values": []}
            streams[label_key]["values"].append([str(entry["timestamp"]), json.dumps(entry)])

        payload = {"streams": list(streams.values())}

        try:
            response = self._client.post(
                self.config.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except Exception as e:
            logging.getLogger(__name__).error(f"Loki push failed: {e}")

    def flush(self) -> None:
        """Flush any buffered logs."""
        with self._lock:
            self._flush_buffer()

    def close(self) -> None:
        """Close handler."""
        self.flush()
        self._client.close()
        super().close()


class LokiExporter:
    """Loki log exporter for structured logging."""

    def __init__(self, config: LokiConfig):
        self.config = config
        self._handler: Optional[LokiHandler] = None
        if config.enabled:
            self._handler = LokiHandler(config)
            root_logger = logging.getLogger()
            root_logger.addHandler(self._handler)
            root_logger.setLevel(logging.INFO)

    def export(self, trace: dict[str, Any]) -> None:
        """Export trace as structured log entries."""
        if not self._handler:
            return

        for span in trace.get("spans", []):
            extra = {
                "trace_id": span.get("trace_id"),
                "span_id": span.get("span_id"),
                "operation": span.get("name"),
                "kind": span.get("kind"),
                "duration_ms": span.get("duration_ms"),
                "status": span.get("status"),
            }
            extra.update(span.get("attributes", {}))

            logger = logging.getLogger("catalyst.trace")
            logger.info(f"Span: {span.get('name')}", extra=extra)

    def flush(self) -> None:
        """Flush buffered logs."""
        if self._handler:
            self._handler.flush()

    def close(self) -> None:
        """Close exporter."""
        if self._handler:
            self._handler.close()
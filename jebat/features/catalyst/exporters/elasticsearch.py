"""Catalyst O11y — Elasticsearch (ELK) Log Exporter."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

_STANDARD_ATTRS = {
    "name", "msg", "args", "created", "filename", "funcName", "levelname",
    "levelno", "lineno", "module", "msecs", "message", "pathname", "process",
    "processName", "relativeCreated", "stack_info", "exc_info", "exc_text",
    "thread", "threadName",
}


@dataclass
class ElasticsearchConfig:
    """Elasticsearch exporter configuration."""
    url: str = "http://localhost:9200"
    index: str = "jebat-logs"
    api_key: Optional[str] = None
    timeout: float = 5.0
    batch_size: int = 50
    environment: str = "production"


def _service_version() -> str:
    try:
        import jebat
        return getattr(jebat, "__version__", "unknown")
    except Exception:
        return "unknown"


class ElasticsearchHandler(logging.Handler):
    """Logging handler that sends logs to Elasticsearch."""

    def __init__(self, config: ElasticsearchConfig):
        super().__init__()
        self.config = config
        self._buffer: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._version = _service_version()
        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"ApiKey {config.api_key}"
        self._client = httpx.Client(timeout=config.timeout, headers=headers)

    def emit(self, record: logging.LogRecord) -> None:
        """Format and buffer log record."""
        try:
            doc: dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "service.name": "jebat",
                "service.version": self._version,
                "environment": self.config.environment,
            }

            if record.exc_info:
                doc["exception"] = self.formatException(record.exc_info)

            for key, value in record.__dict__.items():
                if key in _STANDARD_ATTRS:
                    continue
                try:
                    json.dumps(value)
                    doc[key] = value
                except (TypeError, ValueError):
                    doc[key] = str(value)

            with self._lock:
                self._buffer.append(doc)
                if len(self._buffer) >= self.config.batch_size:
                    self._flush_buffer()

        except Exception:
            self.handleError(record)

    def _flush_buffer(self) -> None:
        """Send buffered logs to Elasticsearch via the _bulk endpoint."""
        if not self._buffer:
            return

        docs = self._buffer[:]
        self._buffer.clear()

        lines = []
        action = json.dumps({"index": {"_index": self.config.index}})
        for doc in docs:
            lines.append(action)
            lines.append(json.dumps(doc))
        payload = "\n".join(lines) + "\n"

        try:
            response = self._client.post(
                f"{self.config.url.rstrip('/')}/_bulk",
                content=payload,
                headers={"Content-Type": "application/x-ndjson"},
            )
            response.raise_for_status()
        except Exception as e:
            logging.getLogger(__name__).error(f"Elasticsearch push failed: {e}")

    def flush(self) -> None:
        """Flush any buffered logs."""
        with self._lock:
            self._flush_buffer()

    def close(self) -> None:
        """Close handler."""
        self.flush()
        self._client.close()
        super().close()


class ElasticsearchExporter:
    """Elasticsearch log exporter for structured logging."""

    def __init__(self, config: ElasticsearchConfig):
        self.config = config
        self._handler: Optional[ElasticsearchHandler] = None
        if config.url:
            self._handler = ElasticsearchHandler(config)
            logging.getLogger().addHandler(self._handler)

    def export(self, trace: dict[str, Any]) -> None:
        """Export trace as structured log entries."""
        if not self._handler:
            return

        for span in trace.get("spans", []):
            extra = {
                "trace_id": span.get("trace_id"),
                "span_id": span.get("span_id"),
                "action": span.get("name"),
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

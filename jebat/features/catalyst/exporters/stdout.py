"""Catalyst O11y — Stdout Exporter (JSON Lines)."""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class StdoutExporterConfig:
    """Configuration for stdout exporter."""
    pretty: bool = False
    include_spans: bool = True
    output_stream: str = "stdout"  # stdout or stderr


class StdoutExporter:
    """Export traces as JSON lines to stdout/stderr."""

    def __init__(self, config: StdoutExporterConfig):
        self.config = config
        self._stream = sys.stdout if config.output_stream == "stdout" else sys.stderr

    def export(self, trace: dict[str, Any]) -> None:
        """Export trace as JSON line."""
        output = {
            "trace_id": trace.get("trace_id"),
            "name": trace.get("name"),
            "start_time": trace.get("start_time"),
            "end_time": trace.get("end_time"),
            "duration_ms": trace.get("duration_ms"),
            "status": trace.get("status"),
            "metadata": trace.get("metadata", {}),
        }

        if self.config.include_spans:
            output["spans"] = trace.get("spans", [])

        try:
            if self.config.pretty:
                json.dump(output, self._stream, indent=2)
            else:
                json.dump(output, self._stream, separators=(",", ":"))
            self._stream.write("\n")
            self._stream.flush()
        except Exception as e:
            logger.error(f"Stdout export failed: {e}")

    def flush(self) -> None:
        """Flush output."""
        self._stream.flush()

    def close(self) -> None:
        """Close exporter."""
        self.flush()
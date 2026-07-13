"""Catalyst O11y — Prometheus Metrics Exporter."""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Lazy import prometheus_client
_prom = None
_prom_lock = threading.Lock()


def _get_prom():
    global _prom
    if _prom is None:
        with _prom_lock:
            if _prom is None:
                try:
                    import prometheus_client as pc
                    _prom = pc
                except ImportError:
                    logger.warning("prometheus_client not installed, metrics disabled")
                    return None
    return _prom


@dataclass
class PrometheusExporterConfig:
    """Configuration for Prometheus exporter."""
    enabled: bool = True
    port: int = 9090
    path: str = "/metrics"
    pushgateway_url: Optional[str] = None
    job_name: str = "jebat"
    instance: Optional[str] = None
    push_interval_seconds: float = 15.0


class PrometheusExporter:
    """Prometheus metrics exporter with optional Pushgateway support."""

    def __init__(self, config: PrometheusExporterConfig):
        self.config = config
        self._prom = _get_prom()
        self._registry = None
        self._metrics = {}
        self._pushgateway_url = config.pushgateway_url
        self._job_name = config.job_name
        self._instance = config.instance or os.getenv("HOSTNAME", "jebat-1")

        if self._prom:
            self._init_registry()
            self._create_builtin_metrics()
            if config.enabled:
                self._start_http_server(config.port, config.path)

    def _init_registry(self) -> None:
        """Initialize Prometheus registry."""
        self._registry = self._prom["CollectorRegistry"]()

    def _create_builtin_metrics(self) -> None:
        """Create built-in JEBAT metrics."""
        # LLM Metrics
        self._create_metric(
            "counter", "jebat_llm_requests_total",
            "Total LLM requests", ["provider", "model", "status"]
        )
        self._create_metric(
            "histogram", "jebat_llm_duration_seconds",
            "LLM request duration", ["provider", "model"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        self._create_metric(
            "histogram", "jebat_llm_tokens_total",
            "Total tokens used", ["provider", "model", "type"],  # prompt, completion, total
            buckets=[100, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000]
        )
        self._create_metric(
            "gauge", "jebat_llm_cost_usd_total",
            "Total LLM cost in USD", ["provider", "model"]
        )

        # Tool Metrics
        self._create_metric(
            "counter", "jebat_tool_invocations_total",
            "Total tool invocations", ["tool", "status"]
        )
        self._create_metric(
            "histogram", "jebat_tool_duration_seconds",
            "Tool execution duration", ["tool"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0]
        )

        # Agent Metrics
        self._create_metric(
            "counter", "jebat_agent_handoffs_total",
            "Total agent handoffs", ["from_agent", "to_agent", "status"]
        )
        self._create_metric(
            "gauge", "jebat_active_agents",
            "Currently active agents", ["agent_type"]
        )

        # Memory Metrics
        self._create_metric(
            "counter", "jebat_memory_operations_total",
            "Total memory operations", ["layer", "operation", "status"]
        )
        self._create_metric(
            "gauge", "jebat_memory_usage_bytes",
            "Memory layer usage in bytes", ["layer"]
        )
        self._create_metric(
            "histogram", "jebat_memory_consolidation_duration_seconds",
            "Memory consolidation duration", ["layer"],
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0]
        )

        # MCP Metrics
        self._create_metric(
            "counter", "jebat_mcp_requests_total",
            "Total MCP requests", ["method", "transport", "status"]
        )
        self._create_metric(
            "histogram", "jebat_mcp_duration_seconds",
            "MCP request duration", ["method", "transport"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )

        # System Metrics
        self._create_metric(
            "gauge", "jebat_uptime_seconds",
            "Process uptime in seconds", []
        )

    def _create_metric(self, mtype: str, name: str, help_text: str,
                       labels: list[str], **kwargs) -> None:
        """Create a Prometheus metric."""
        if not self._prom:
            return

        if mtype == "counter":
            metric = self._prom["Counter"](name, help_text, labels, registry=self._registry)
        elif mtype == "gauge":
            metric = self._prom["Gauge"](name, help_text, labels, registry=self._registry)
        elif mtype == "histogram":
            metric = self._prom["Histogram"](name, help_text, labels, registry=self._registry, **kwargs)
        elif mtype == "summary":
            metric = self._prom["Summary"](name, help_text, labels, registry=self._registry)
        else:
            raise ValueError(f"Unknown metric type: {mtype}")

        self._metrics[name] = metric

    def _start_http_server(self, port: int, path: str) -> None:
        """Start Prometheus HTTP metrics server."""
        try:
            self._prom["start_http_server"](port, addr="0.0.0.0", registry=self._registry)
            logger.info(f"Prometheus metrics server started on port {port}{path}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus HTTP server: {e}")

    def counter(self, name: str, labels: dict[str, str] = None, value: float = 1.0) -> None:
        """Increment a counter."""
        metric = self._metrics.get(name)
        if metric and self._prom:
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)

    def gauge(self, name: str, value: float, labels: dict[str, str] = None) -> None:
        """Set a gauge value."""
        metric = self._metrics.get(name)
        if metric and self._prom:
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)

    def histogram(self, name: str, value: float, labels: dict[str, str] = None) -> None:
        """Observe a histogram value."""
        metric = self._metrics.get(name)
        if metric and self._prom:
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)

    def summary(self, name: str, value: float, labels: dict[str, str] = None) -> None:
        """Observe a summary value."""
        metric = self._metrics.get(name)
        if metric and self._prom:
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)

    def export(self, trace: dict[str, Any]) -> None:
        """Export trace as metrics (extract metrics from trace)."""
        # Extract span metrics from trace
        for span in trace.get("spans", []):
            kind = span.get("kind", "internal")
            duration_ms = span.get("duration_ms", 0)
            status = span.get("status", "ok")
            attributes = span.get("attributes", {})

            if kind == "llm":
                provider = attributes.get("llm.provider", "unknown")
                model = attributes.get("llm.model", "unknown")
                self.counter("jebat_llm_requests_total", {"provider": provider, "model": model, "status": status})
                self.histogram("jebat_llm_duration_seconds", duration_ms / 1000, {"provider": provider, "model": model})

                prompt_tokens = attributes.get("llm.prompt_tokens", 0)
                completion_tokens = attributes.get("llm.completion_tokens", 0)
                if prompt_tokens:
                    self.histogram("jebat_llm_tokens_total", prompt_tokens, {"provider": provider, "model": model, "type": "prompt"})
                if completion_tokens:
                    self.histogram("jebat_llm_tokens_total", completion_tokens, {"provider": provider, "model": model, "type": "completion"})

            elif kind == "tool":
                tool = attributes.get("tool.name", "unknown")
                self.counter("jebat_tool_invocations_total", {"tool": tool, "status": status})
                self.histogram("jebat_tool_duration_seconds", duration_ms / 1000, {"tool": tool})

            elif kind == "agent":
                from_agent = attributes.get("agent.from", "unknown")
                to_agent = attributes.get("agent.to", "unknown")
                self.counter("jebat_agent_handoffs_total", {"from_agent": from_agent, "to_agent": to_agent, "status": status})

            elif kind == "database":
                layer = attributes.get("memory.layer", "unknown")
                operation = attributes.get("memory.operation", "unknown")
                self.counter("jebat_memory_operations_total", {"layer": layer, "operation": operation, "status": status})

    def flush(self) -> None:
        """Push metrics to Pushgateway if configured."""
        if not self._prom or not self._pushgateway_url:
            return

        try:
            self._prom["push_to_gateway"](
                self._pushgateway_url,
                job=self._job_name,
                registry=self._registry,
                grouping_key={"instance": self._instance},
            )
        except Exception as e:
            logger.error(f"Pushgateway push failed: {e}")

    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format."""
        if not self._prom:
            return ""
        return self._prom["generate_latest"](self._registry).decode("utf-8")

    def get_metric(self, name: str) -> Any:
        """Get a metric by name for direct manipulation."""
        return self._metrics.get(name)
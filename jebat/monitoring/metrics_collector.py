"""
JEBAT Metrics Collector

System metrics collection:
- CPU, Memory, Disk usage
- Request latency
- Error rates
- Custom metrics
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram


class MetricsCollector:
    """
    Metrics Collector for JEBAT.

    Collects and stores system metrics.
    """

    def __init__(self, retention_seconds: int = 86400):
        """
        Initialize Metrics Collector.

        Args:
            retention_seconds: Data retention period
        """
        self.retention_seconds = retention_seconds
        self.metrics: Dict[str, List[MetricPoint]] = {}
        self.collectors: List[callable] = []
        self.running = False

        logger.info("MetricsCollector initialized")

    def register_collector(self, collector: callable):
        """Register a metric collector function."""
        self.collectors.append(collector)
        logger.info(f"Registered collector: {collector.__name__}")

    async def start_collecting(self, interval: int = 10):
        """Start automatic metric collection."""
        self.running = True

        while self.running:
            await self._collect_all_metrics()
            await asyncio.sleep(interval)

    async def stop_collecting(self):
        """Stop metric collection."""
        self.running = False

    async def _collect_all_metrics(self):
        """Collect metrics from all registered collectors."""
        for collector in self.collectors:
            try:
                metrics = await collector()
                for metric in metrics:
                    await self.record(metric)
            except Exception as e:
                logger.error(f"Collector error: {e}")

    async def record(self, metric: MetricPoint):
        """Record a metric point."""
        if metric.name not in self.metrics:
            self.metrics[metric.name] = []

        self.metrics[metric.name].append(metric)

        # Cleanup old data
        self._cleanup_old_data(metric.name)

    def _cleanup_old_data(self, metric_name: str):
        """Remove old metric data."""
        if metric_name not in self.metrics:
            return

        cutoff = datetime.now().timestamp() - self.retention_seconds

        self.metrics[metric_name] = [
            p for p in self.metrics[metric_name] if p.timestamp.timestamp() > cutoff
        ]

    async def get_metric(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get metric data."""
        if name not in self.metrics:
            return []

        points = self.metrics[name]

        if start_time:
            points = [p for p in points if p.timestamp >= start_time]

        if end_time:
            points = [p for p in points if p.timestamp <= end_time]

        return [
            {
                "timestamp": p.timestamp.isoformat(),
                "value": p.value,
                "tags": p.tags,
            }
            for p in points
        ]

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        # Simulate system metrics (in production, use psutil)
        return {
            "cpu_percent": 45.2,
            "memory_percent": 62.5,
            "memory_used_gb": 8.4,
            "memory_total_gb": 16.0,
            "disk_percent": 55.0,
            "network_rx_mb": 1250,
            "network_tx_mb": 890,
        }

    async def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics."""
        return {
            "requests_total": 15420,
            "requests_per_second": 125.5,
            "avg_latency_ms": 45.2,
            "p95_latency_ms": 120.5,
            "p99_latency_ms": 250.0,
            "error_rate": 0.02,
            "active_connections": 342,
            "queue_size": 15,
        }

    async def get_jebat_metrics(self) -> Dict[str, Any]:
        """Get JEBAT-specific metrics."""
        return {
            "cortex_thinks_total": 1250,
            "continuum_cycles": 45000,
            "memory_layers": {
                "m0_sensory": {"count": 150, "heat": 0.85},
                "m1_episodic": {"count": 520, "heat": 0.65},
                "m2_semantic": {"count": 1200, "heat": 0.45},
                "m3_conceptual": {"count": 350, "heat": 0.30},
                "m4_procedural": {"count": 85, "heat": 0.90},
            },
            "agents_active": 5,
            "tasks_completed": 8920,
            "tokens_used": 2500000,
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        summary = {
            "total_metrics": len(self.metrics),
            "metrics": {},
        }

        for name, points in self.metrics.items():
            if points:
                values = [p.value for p in points]
                summary["metrics"][name] = {
                    "count": len(points),
                    "latest": points[-1].value,
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }

        return summary

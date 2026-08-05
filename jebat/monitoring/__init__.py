"""
JEBAT Monitoring System

Real-time metrics collection and dashboard for system observability.
"""

try:
    from .dashboard import run_dashboard
except ImportError:
    run_dashboard = None
from .metrics_collector import MetricsCollector

__all__ = ["MetricsCollector", "run_dashboard"]

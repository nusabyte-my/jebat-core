"""
Pydantic models for monitoring data.
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime


class SystemMetric(BaseModel):
    """Individual metric data point."""
    timestamp: datetime
    component: str
    metric_name: str
    metric_value: float
    metric_labels: Dict[str, Any] = {}


class ComponentStats(BaseModel):
    """Statistics for a specific component."""
    component: str
    timestamp: datetime
    metrics: Dict[str, float]
    labels: Dict[str, Any] = {}


class MonitoringSnapshot(BaseModel):
    """Snapshot of all monitored components at a point in time."""
    timestamp: datetime
    components: Dict[str, ComponentStats]
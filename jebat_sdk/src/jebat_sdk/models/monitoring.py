"""
Monitoring models for JEBAT SDK.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    healthy: bool
    database: bool
    redis: bool
    timestamp: datetime


class StatusResponse(BaseModel):
    """System status response."""
    status: str
    version: str
    timestamp: datetime
    components: Dict[str, str]


class MetricsResponse(BaseModel):
    """System metrics response."""
    ultra_loop: Dict[str, Any] = Field(default_factory=dict)
    ultra_think: Dict[str, Any] = Field(default_factory=dict)
    memory: Dict[str, Any] = Field(default_factory=dict)
    orchestrator: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class MonitoringSnapshot(BaseModel):
    """Monitoring dashboard snapshot."""
    timestamp: datetime
    components: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ComponentMetrics(BaseModel):
    """Component metrics."""
    component: str
    timestamp: datetime
    metrics: Dict[str, float] = Field(default_factory=dict)
    labels: Dict[str, Any] = Field(default_factory=dict)


class TimeSeriesData(BaseModel):
    """Time series data point."""
    component: str
    metric_name: str
    interval: str
    start_time: datetime
    end_time: datetime
    data: List[Dict[str, Any]] = Field(default_factory=list)
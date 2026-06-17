"""
API endpoints for JEBAT monitoring dashboard.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
import logging

from .models import ComponentStats, MonitoringSnapshot
from .storage import MonitoringStorage, get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

@router.get("/snapshot", response_model=MonitoringSnapshot)
async def get_latest_snapshot(
    storage: MonitoringStorage = Depends(get_storage)
):
    """
    Get the latest monitoring snapshot from all components.
    """
    try:
        # Get latest metrics (we'll construct a snapshot from latest individual metrics)
        latest_metrics = await storage.get_latest_metrics(limit=1000)
        
        # Group by timestamp and component to reconstruct snapshot
        # For simplicity, we'll use the most recent timestamp and latest value for each component/metric
        components_data: Dict[str, Dict[str, Any]] = {}
        latest_timestamp = datetime.min
        
        for record in latest_metrics:
            timestamp = record['time']
            if timestamp > latest_timestamp:
                latest_timestamp = timestamp
            
            component = record['component']
            metric_name = record['metric_name']
            metric_value = record['metric_value']
            metric_labels = record['metric_labels'] or {}
            
            if component not in components_data:
                components_data[component] = {'metrics': {}, 'labels': {}, 'timestamp': timestamp}
            
            components_data[component]['metrics'][metric_name] = metric_value
            # Merge labels (latest wins)
            components_data[component]['labels'].update(metric_labels)
            components_data[component]['timestamp'] = max(
                components_data[component]['timestamp'], 
                timestamp
            )
        
        # Build component stats
        components: Dict[str, ComponentStats] = {}
        for component_name, data in components_data.items():
            components[component_name] = ComponentStats(
                component=component_name,
                timestamp=data['timestamp'],
                metrics=data['metrics'],
                labels=data['labels']
            )
        
        snapshot = MonitoringSnapshot(
            timestamp=latest_timestamp,
            components=components
        )
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Failed to get monitoring snapshot: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve monitoring data")

@router.get("/metrics/{component}/{metric_name}")
async def get_metric_time_series(
    component: str,
    metric_name: str,
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    interval: str = Query("1 hour", regex="^(1 minute|5 minutes|15 minutes|1 hour|6 hours|12 hours)$"),
    storage: MonitoringStorage = Depends(get_storage)
):
    """
    get time series data for a specific metric.
    """
    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # Get aggregated data
        aggregated_data = await storage.get_aggregated_metrics(
            component=component,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            interval=interval
        )
        
        return {
            "component": component,
            "metric_name": metric_name,
            "interval": interval,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "data": aggregated_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get metric time series: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metric data")

@router.get("/components")
async def get_available_components(
    storage: MonitoringStorage = Depends(get_storage)
):
    """
    Get list of all components that have monitoring data.
    """
    try:
        # Get a sample of recent data to determine available components
        recent_metrics = await storage.get_latest_metrics(limit=100)
        components = list(set(record['component'] for record in recent_metrics))
        return {"components": sorted(components)}
        
    except Exception as e:
        logger.error(f"Failed to get available components: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve component list")

@router.get("/metrics/{component}")
async def get_component_metrics(
    component: str,
    hours: int = Query(24, ge=1, le=168),
    storage: MonitoringStorage = Depends(get_storage)
):
    """
    Get all metrics for a specific component over a time range.
    """
    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # Get raw metrics for the component
        metrics = await storage.get_latest_metrics(component=component, limit=10000)
        
        # Filter by time range
        filtered_metrics = [
            record for record in metrics
            if start_time <= record['time'] <= end_time
        ]
        
        # Group by metric name
        grouped_data: Dict[str, List[Dict[str, Any]]] = {}
        for record in filtered_metrics:
            metric_name = record['metric_name']
            if metric_name not in grouped_data:
                grouped_data[metric_name] = []
            grouped_data[metric_name].append({
                'timestamp': record['time'].isoformat(),
                'value': record['metric_value'],
                'labels': record['metric_labels']
            })
        
        return {
            "component": component,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "metrics": grouped_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get component metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve component metrics")

@router.get("/health")
async def get_system_health(
    storage: MonitoringStorage = Depends(get_storage)
):
    """
    Get overall system health status based on recent metrics.
    """
    try:
        # Get recent metrics to assess health
        recent_metrics = await storage.get_latest_metrics(limit=500)
        
        # Simple health assessment (can be enhanced)
        health_status = "healthy"
        issues = []
        
        # Check if we're receiving data
        if not recent_metrics:
            health_status = "unhealthy"
            issues.append("No metrics data received recently")
        else:
            # Check timestamp of latest data
            latest_time = max(record['time'] for record in recent_metrics)
            time_diff = datetime.now(timezone.utc) - latest_time
            if time_diff > timedelta(minutes=5):
                health_status = "degraded"
                issues.append(f"No recent data (last update: {time_diff.total_seconds():.0f}s ago)")
        
        # TODO: Add more sophisticated health checks based on actual metric values
        
        return {
            "status": health_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "issues": issues,
            "metrics_count": len(recent_metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to assess system health")

# Export the router
__all__ = ["router"]
"""
JEBAT Metrics Collector

Centralized metrics collection from all JEBAT systems:
- Ultra-Loop metrics
- Ultra-Think metrics
- Memory system metrics
- Agent system metrics
- System health metrics
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System-wide metrics"""

    uptime_seconds: float = 0.0
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_percent: float = 0.0
    active_agents: int = 0
    active_channels: int = 0
    database_connected: bool = False
    redis_connected: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "uptime_seconds": self.uptime_seconds,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_used_mb": self.memory_used_mb,
            "memory_available_mb": self.memory_available_mb,
            "disk_percent": self.disk_percent,
            "active_agents": self.active_agents,
            "active_channels": self.active_channels,
            "database_connected": self.database_connected,
            "redis_connected": self.redis_connected,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class UltraLoopMetrics:
    """Ultra-Loop specific metrics"""

    cycles_per_second: float = 0.0
    total_cycles: int = 0
    successful_cycles: int = 0
    failed_cycles: int = 0
    success_rate: float = 0.0
    avg_cycle_time_ms: float = 0.0
    phase_distribution: Dict[str, int] = field(default_factory=dict)
    recent_errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cycles_per_second": self.cycles_per_second,
            "total_cycles": self.total_cycles,
            "successful_cycles": self.successful_cycles,
            "failed_cycles": self.failed_cycles,
            "success_rate": self.success_rate,
            "avg_cycle_time_ms": self.avg_cycle_time_ms,
            "phase_distribution": self.phase_distribution,
            "recent_errors": self.recent_errors[-10:],  # Last 10 errors
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class UltraThinkMetrics:
    """Ultra-Think specific metrics"""

    thoughts_per_second: float = 0.0
    total_sessions: int = 0
    successful_sessions: int = 0
    failed_sessions: int = 0
    total_thoughts: int = 0
    avg_thoughts_per_session: float = 0.0
    avg_confidence: float = 0.0
    mode_distribution: Dict[str, int] = field(default_factory=dict)
    avg_session_duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "thoughts_per_second": self.thoughts_per_second,
            "total_sessions": self.total_sessions,
            "successful_sessions": self.successful_sessions,
            "failed_sessions": self.failed_sessions,
            "total_thoughts": self.total_thoughts,
            "avg_thoughts_per_session": self.avg_thoughts_per_session,
            "avg_confidence": self.avg_confidence,
            "mode_distribution": self.mode_distribution,
            "avg_session_duration_ms": self.avg_session_duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MemoryMetrics:
    """Memory system metrics"""

    total_memories: int = 0
    memories_by_layer: Dict[str, int] = field(default_factory=dict)
    storage_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    search_latency_ms: float = 0.0
    avg_heat_score: float = 0.0
    high_heat_count: int = 0
    low_heat_count: int = 0
    recent_stores: int = 0  # Last hour
    recent_retrievals: int = 0  # Last hour
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_memories": self.total_memories,
            "memories_by_layer": self.memories_by_layer,
            "storage_latency_ms": self.storage_latency_ms,
            "retrieval_latency_ms": self.retrieval_latency_ms,
            "search_latency_ms": self.search_latency_ms,
            "avg_heat_score": self.avg_heat_score,
            "high_heat_count": self.high_heat_count,
            "low_heat_count": self.low_heat_count,
            "recent_stores": self.recent_stores,
            "recent_retrievals": self.recent_retrievals,
            "timestamp": self.timestamp.isoformat(),
        }


class MetricsCollector:
    """
    Centralized metrics collector for JEBAT system.

    Collects, aggregates, and provides access to all system metrics.
    """

    def __init__(self):
        """Initialize the metrics collector"""
        self.start_time = datetime.utcnow()
        self._system_metrics = SystemMetrics()
        self._ultra_loop_metrics = UltraLoopMetrics()
        self._ultra_think_metrics = UltraThinkMetrics()
        self._memory_metrics = MemoryMetrics()

        # History for trending (last 100 data points)
        self._history_max_size = 100
        self._system_history: List[SystemMetrics] = []
        self._ultra_loop_history: List[UltraLoopMetrics] = []
        self._ultra_think_history: List[UltraThinkMetrics] = []

        logger.info("MetricsCollector initialized")

    def collect_system_metrics(
        self,
        database_connected: bool = False,
        redis_connected: bool = False,
        active_agents: int = 0,
        active_channels: int = 0,
    ) -> SystemMetrics:
        """
        Collect system-wide metrics.

        Args:
            database_connected: Database connection status
            redis_connected: Redis connection status
            active_agents: Number of active agents
            active_channels: Number of active channels

        Returns:
            SystemMetrics instance
        """
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            self._system_metrics = SystemMetrics(
                uptime_seconds=(datetime.utcnow() - self.start_time).total_seconds(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_percent=disk.percent,
                active_agents=active_agents,
                active_channels=active_channels,
                database_connected=database_connected,
                redis_connected=redis_connected,
                timestamp=datetime.utcnow(),
            )
        except ImportError:
            # psutil not installed, use basic metrics
            self._system_metrics = SystemMetrics(
                uptime_seconds=(datetime.utcnow() - self.start_time).total_seconds(),
                cpu_percent=0.0,
                memory_percent=0.0,
                active_agents=active_agents,
                active_channels=active_channels,
                database_connected=database_connected,
                redis_connected=redis_connected,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")

        # Add to history
        self._add_to_history(self._system_history, self._system_metrics)

        return self._system_metrics

    def collect_ultra_loop_metrics(
        self,
        ultra_loop_instance=None,
    ) -> UltraLoopMetrics:
        """
        Collect Ultra-Loop metrics.

        Args:
            ultra_loop_instance: UltraLoop instance to collect from

        Returns:
            UltraLoopMetrics instance
        """
        if ultra_loop_instance:
            try:
                metrics = ultra_loop_instance.get_metrics()

                self._ultra_loop_metrics = UltraLoopMetrics(
                    cycles_per_second=metrics.get("cycles_per_second", 0.0),
                    total_cycles=metrics.get("total_cycles", 0),
                    successful_cycles=metrics.get("successful_cycles", 0),
                    failed_cycles=metrics.get("failed_cycles", 0),
                    success_rate=metrics.get("success_rate", 0.0),
                    avg_cycle_time_ms=metrics.get("avg_cycle_time_ms", 0.0),
                    phase_distribution=metrics.get("phase_distribution", {}),
                    recent_errors=metrics.get("errors", [])[-10:],
                    timestamp=datetime.utcnow(),
                )
            except Exception as e:
                logger.warning(f"Failed to collect Ultra-Loop metrics: {e}")

        # Add to history
        self._add_to_history(self._ultra_loop_history, self._ultra_loop_metrics)

        return self._ultra_loop_metrics

    def collect_ultra_think_metrics(
        self,
        ultra_think_instance=None,
    ) -> UltraThinkMetrics:
        """
        Collect Ultra-Think metrics.

        Args:
            ultra_think_instance: UltraThink instance to collect from

        Returns:
            UltraThinkMetrics instance
        """
        if ultra_think_instance:
            try:
                stats = ultra_think_instance.get_statistics()

                self._ultra_think_metrics = UltraThinkMetrics(
                    thoughts_per_second=stats.get("thoughts_per_second", 0.0),
                    total_sessions=stats.get("total_sessions", 0),
                    successful_sessions=stats.get("successful_sessions", 0),
                    failed_sessions=stats.get("failed_sessions", 0),
                    total_thoughts=stats.get("total_thoughts", 0),
                    avg_thoughts_per_session=stats.get("avg_thoughts_per_session", 0.0),
                    avg_confidence=stats.get("avg_confidence", 0.0),
                    mode_distribution=stats.get("mode_distribution", {}),
                    avg_session_duration_ms=stats.get("avg_session_duration_ms", 0.0),
                    timestamp=datetime.utcnow(),
                )
            except Exception as e:
                logger.warning(f"Failed to collect Ultra-Think metrics: {e}")

        # Add to history
        self._add_to_history(self._ultra_think_history, self._ultra_think_metrics)

        return self._ultra_think_metrics

    def collect_memory_metrics(
        self,
        memory_manager=None,
    ) -> MemoryMetrics:
        """
        Collect memory system metrics.

        Args:
            memory_manager: MemoryManager instance to collect from

        Returns:
            MemoryMetrics instance
        """
        if memory_manager:
            try:
                stats = memory_manager.get_statistics()

                self._memory_metrics = MemoryMetrics(
                    total_memories=stats.get("total_memories", 0),
                    memories_by_layer=stats.get("memories_by_layer", {}),
                    storage_latency_ms=stats.get("storage_latency_ms", 0.0),
                    retrieval_latency_ms=stats.get("retrieval_latency_ms", 0.0),
                    search_latency_ms=stats.get("search_latency_ms", 0.0),
                    avg_heat_score=stats.get("avg_heat_score", 0.0),
                    high_heat_count=stats.get("high_heat_count", 0),
                    low_heat_count=stats.get("low_heat_count", 0),
                    recent_stores=stats.get("recent_stores", 0),
                    recent_retrievals=stats.get("recent_retrievals", 0),
                    timestamp=datetime.utcnow(),
                )
            except Exception as e:
                logger.warning(f"Failed to collect memory metrics: {e}")
        else:
            # Basic metrics without manager
            self._memory_metrics = MemoryMetrics(
                timestamp=datetime.utcnow(),
            )

        return self._memory_metrics

    def _add_to_history(self, history_list: List, metric: Any):
        """Add metric to history with size limit"""
        history_list.append(metric)
        while len(history_list) > self._history_max_size:
            history_list.pop(0)

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all current metrics.

        Returns:
            Dictionary containing all metrics
        """
        return {
            "system": self._system_metrics.to_dict(),
            "ultra_loop": self._ultra_loop_metrics.to_dict(),
            "ultra_think": self._ultra_think_metrics.to_dict(),
            "memory": self._memory_metrics.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get historical metrics for trending.

        Returns:
            Dictionary containing historical data
        """
        return {
            "system": [m.to_dict() for m in self._system_history],
            "ultra_loop": [m.to_dict() for m in self._ultra_loop_history],
            "ultra_think": [m.to_dict() for m in self._ultra_think_history],
        }

    def get_uptime(self) -> timedelta:
        """Get system uptime"""
        return datetime.utcnow() - self.start_time

    def reset(self):
        """Reset all metrics"""
        self.start_time = datetime.utcnow()
        self._system_history.clear()
        self._ultra_loop_history.clear()
        self._ultra_think_history.clear()
        logger.info("MetricsCollector reset")

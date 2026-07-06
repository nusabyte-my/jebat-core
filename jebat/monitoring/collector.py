"""
Metrics collector service for JEBAT monitoring subsystem.
Collects metrics from all registered components at regular intervals.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from jebat.core.agents import AgentOrchestrator
from jebat.core.memory.manager import MemoryManager
from jebat.core.decision.engine import DecisionEngine
from jebat.core.cache.smart_cache import SmartCache
from jebat.core.config import JebatLLMConfig
from jebat.core.llm.chat_runtime import generate_chat_reply
from jebat.integrations.channels.channel_manager import ChannelManager
from jebat.cortex.intelligent_skill import IntelligentSkill

from .models import ComponentStats, MonitoringSnapshot
from .storage import MonitoringStorage

logger = logging.getLogger(__name__)

class MonitoringCollector:
    """
    Collects metrics from all JEBAT components at regular intervals.
    """
    
    def __init__(self, storage: MonitoringStorage, collection_interval: int = 10):
        """
        Initialize the monitoring collector.
        
        Args:
            storage: Storage backend for metrics
            collection_interval: Seconds between collection cycles
        """
        self.storage = storage
        self.collection_interval = collection_interval
        self._is_running = False
        self._collection_task: Optional[asyncio.Task] = None
        
        # Component references (will be injected)
        self.orchestrator: Optional[AgentOrchestrator] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.decision_engine: Optional[DecisionEngine] = None
        self.smart_cache: Optional[SmartCache] = None
        self.llm_config: Optional[JebatLLMConfig] = None
        self.channel_manager: Optional[ChannelManager] = None
        self.intelligent_skill: Optional[IntelligentSkill] = None
        
        logger.info(f"MonitoringCollector initialized with {collection_interval}s interval")
    
    def set_orchestrator(self, orchestrator: AgentOrchestrator):
        """Set the orchestrator reference."""
        self.orchestrator = orchestrator
        logger.debug("Orchestrator reference set")
    
    def set_memory_manager(self, memory_manager: MemoryManager):
        """Set the memory manager reference."""
        self.memory_manager = memory_manager
        logger.debug("Memory manager reference set")
    
    def set_decision_engine(self, decision_engine: DecisionEngine):
        """Set the decision engine reference."""
        self.decision_engine = decision_engine
        logger.debug("Decision engine reference set")
    
    def set_smart_cache(self, smart_cache: SmartCache):
        """Set the smart cache reference."""
        self.smart_cache = smart_cache
        logger.debug("Smart cache reference set")
    
    def set_llm_config(self, llm_config: JebatLLMConfig):
        """Set the LLM config reference."""
        self.llm_config = llm_config
        logger.debug("LLM config reference set")
    
    def set_channel_manager(self, channel_manager: ChannelManager):
        """Set the channel manager reference."""
        self.channel_manager = channel_manager
        logger.debug("Channel manager reference set")
    
    def set_intelligent_skill(self, intelligent_skill: IntelligentSkill):
        """Set the intelligent skill reference."""
        self.intelligent_skill = intelligent_skill
        logger.debug("Intelligent skill reference set")
    
    async def start(self):
        """Start the metrics collection loop."""
        if self._is_running:
            logger.warning("MonitoringCollector is already running")
            return
        
        self._is_running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("MonitoringCollector started")
    
    async def stop(self):
        """Stop the metrics collection loop."""
        if not self._is_running:
            logger.warning("MonitoringCollector is not running")
            return
        
        self._is_running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
            self._collection_task = None
        logger.info("MonitoringCollector stopped")
    
    async def _collection_loop(self):
        """Main collection loop."""
        logger.info("Starting metrics collection loop")
        while self._is_running:
            try:
                await self._collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                logger.info("Collection loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}", exc_info=True)
                # Continue looping despite errors
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_all_metrics(self):
        """Collect metrics from all registered components."""
        timestamp = datetime.now(timezone.utc)
        components_stats: Dict[str, ComponentStats] = {}
        
        # Collect orchestrator metrics
        if self.orchestrator:
            try:
                stats = self.orchestrator.get_stats()
                components_stats["orchestrator"] = ComponentStats(
                    component="orchestrator",
                    timestamp=timestamp,
                    metrics=self._extract_numeric_metrics(stats),
                    labels=self._extract_label_metrics(stats)
                )
            except Exception as e:
                logger.error(f"Failed to collect orchestrator metrics: {e}")
        
        # Collect memory manager metrics
        if self.memory_manager:
            try:
                stats = self.memory_manager.get_stats()
                components_stats["memory_manager"] = ComponentStats(
                    component="memory_manager",
                    timestamp=timestamp,
                    metrics=self._extract_numeric_metrics(stats),
                    labels=self._extract_label_metrics(stats)
                )
            except Exception as e:
                logger.error(f"Failed to collect memory manager metrics: {e}")
        
        # Collect decision engine metrics
        if self.decision_engine:
            try:
                stats = self.decision_engine.get_stats()
                components_stats["decision_engine"] = ComponentStats(
                    component="decision_engine",
                    timestamp=timestamp,
                    metrics=self._extract_numeric_metrics(stats),
                    labels=self._extract_label_metrics(stats)
                )
            except Exception as e:
                logger.error(f"Failed to collect decision engine metrics: {e}")
        
        # Collect smart cache metrics
        if self.smart_cache:
            try:
                stats = self.smart_cache.get_stats()
                components_stats["smart_cache"] = ComponentStats(
                    component="smart_cache",
                    timestamp=timestamp,
                    metrics=self._extract_numeric_metrics(stats),
                    labels=self._extract_label_metrics(stats)
                )
            except Exception as e:
                logger.error(f"Failed to collect smart cache metrics: {e}")
        
        # Collect channel manager metrics
        if self.channel_manager:
            try:
                stats = self.channel_manager.get_stats()
                components_stats["channel_manager"] = ComponentStats(
                    component="channel_manager",
                    timestamp=timestamp,
                    metrics=self._extract_numeric_metrics(stats),
                    labels=self._extract_label_metrics(stats)
                )
            except Exception as e:
                logger.error(f"Failed to collect channel manager metrics: {e}")
        
        # Collect intelligent skill metrics
        if self.intelligent_skill:
            try:
                stats = self.intelligent_skill.get_stats()
                components_stats["intelligent_skill"] = ComponentStats(
                    component="intelligent_skill",
                    timestamp=timestamp,
                    metrics=self._extract_numeric_metrics(stats),
                    labels=self._extract_label_metrics(stats)
                )
            except Exception as e:
                logger.error(f"Failed to collect intelligent skill metrics: {e}")
        
        # Create snapshot and store
        snapshot = MonitoringSnapshot(
            timestamp=timestamp,
            components=components_stats
        )
        
        try:
            await self.storage.store_snapshot(snapshot)
            logger.debug(f"Stored monitoring snapshot with {len(components_stats)} components")
        except Exception as e:
            logger.error(f"Failed to store monitoring snapshot: {e}")
    
    def _extract_numeric_metrics(self, stats: Dict[str, Any]) -> Dict[str, float]:
        """Extract numeric values from stats dictionary."""
        numeric_metrics = {}
        for key, value in stats.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                numeric_metrics[key] = float(value)
            elif isinstance(value, dict):
                # Recursively extract from nested dictionaries
                nested = self._extract_numeric_metrics(value)
                for nested_key, nested_value in nested.items():
                    numeric_metrics[f"{key}.{nested_key}"] = nested_value
        return numeric_metrics
    
    def _extract_label_metrics(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Extract non-numeric values as labels."""
        label_metrics = {}
        for key, value in stats.items():
            if not isinstance(value, (int, float, bool)) and value is not None:
                # Convert to string for storage, but keep original for display
                label_metrics[key] = str(value)
            elif isinstance(value, dict):
                # Recursively extract from nested dictionaries
                nested = self._extract_label_metrics(value)
                for nested_key, nested_value in nested.items():
                    label_metrics[f"{key}.{nested_key}"] = nested_value
        return label_metrics

# Global collector instance
_collector: Optional[MonitoringCollector] = None

def get_collector() -> Optional[MonitoringCollector]:
    """Get the global monitoring collector instance."""
    return _collector

def initialize_collector(storage: MonitoringStorage, collection_interval: int = 10) -> MonitoringCollector:
    """Initialize the global monitoring collector."""
    global _collector
    _collector = MonitoringCollector(storage, collection_interval)
    return _collector
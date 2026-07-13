"""
JEBAT Memory Manager

Central controller for 6-type memory system (Working, Episodic, Semantic, Procedural, Relational, Vector) with:
- Automatic consolidation
- Heat-based importance scoring
- Cross-layer search
- User profile aggregation

Delegates to EnhancedMemorySystem for rich memory features
(forgetting curves, pattern extraction, self-learning).
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .layers import (
    HeatScore,
    Memory,
    MemoryImportance,
    MemoryLayer,
    MemoryMetadata,
    MemoryModality,
)

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central memory management system.

    Manages 6-type memory with automatic consolidation,
    heat scoring, and intelligent retrieval.

    Delegates to EnhancedMemorySystem when available for:
    - Ebbinghaus forgetting curves
    - Pattern extraction
    - Self-learning memory
    - Spreading activation retrieval
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Memory Manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.memories: Dict[MemoryLayer, List[Memory]] = {
            layer: [] for layer in MemoryLayer
        }
        self.consolidation_interval = self.config.get(
            "consolidation_interval", 3600
        )  # 1 hour
        self._consolidation_task: Optional[asyncio.Task] = None

        # Lazy init enhanced memory system
        self._enhanced_memory = None

        logger.info("MemoryManager initialized with all memory layers")

    def _get_enhanced_memory(self):
        """Lazily initialize EnhancedMemorySystem."""
        if self._enhanced_memory is None:
            try:
                from jebat.features.memory import EnhancedMemorySystem
                self._enhanced_memory = EnhancedMemorySystem()
            except Exception:
                pass
        return self._enhanced_memory

    async def store(
        self,
        content: str,
        layer: MemoryLayer = MemoryLayer.M1_EPISODIC,
        user_id: str = "default",
        metadata: Optional[MemoryMetadata] = None,
    ) -> str:
        """
        Store a memory in both legacy and enhanced systems.

        Args:
            content: Memory content
            layer: Target memory layer
            user_id: User identifier
            metadata: Optional metadata

        Returns:
            Memory ID
        """
        # Legacy storage
        memory = Memory(
            memory_id=f"mem_{datetime.now(timezone.utc).timestamp()}",
            content=content,
            layer=layer,
            metadata=metadata or MemoryMetadata(user_id=user_id),
            heat=HeatScore(),
            created_at=datetime.now(timezone.utc),
        )
        self.memories[layer].append(memory)

        # Also store in enhanced memory system
        enhanced = self._get_enhanced_memory()
        if enhanced:
            try:
                from jebat.features.memory import MemoryType
                type_map = {
                    MemoryLayer.M0_SENSORY: MemoryType.WORKING,
                    MemoryLayer.M1_EPISODIC: MemoryType.EPISODIC,
                    MemoryLayer.M2_SEMANTIC: MemoryType.SEMANTIC,
                    MemoryLayer.M3_CONCEPTUAL: MemoryType.SEMANTIC,
                    MemoryLayer.M4_PROCEDURAL: MemoryType.PROCEDURAL,
                }
                mem_type = type_map.get(layer, MemoryType.EPISODIC)
                await enhanced.encode(
                    content=content,
                    memory_type=mem_type,
                    importance=0.5,
                    context={"user_id": user_id, "legacy_id": memory.memory_id},
                )
            except Exception:
                pass

        logger.info(f"Stored memory in {layer.value}: {content[:50]}...")
        return memory.memory_id

    def search(
        self,
        query: str,
        user_id: str,
        layer: Optional[MemoryLayer] = None,
        limit: int = 10,
    ) -> List[Memory]:
        """
        Search memories using legacy substring search.

        For async context with enhanced memory, use `asearch()` instead.
        """
        results = []
        layers_to_search = [layer] if layer else list(MemoryLayer)

        # Legacy substring search
        for lyr in layers_to_search:
            for memory in self.memories[lyr]:
                if memory.metadata.user_id != user_id:
                    continue
                if query.lower() in memory.content.lower():
                    results.append(memory)
                    if len(results) >= limit:
                        return results

        return results

    async def asearch(
        self,
        query: str,
        user_id: str,
        layer: Optional[MemoryLayer] = None,
        limit: int = 10,
    ) -> List[Memory]:
        """
        Async search using both legacy substring and enhanced memory similarity.
        """
        # Start with legacy search
        results = self.search(query, user_id, layer, limit)

        # If few results, try enhanced memory system
        if len(results) < limit:
            enhanced = self._get_enhanced_memory()
            if enhanced:
                try:
                    traces = await enhanced.retrieve(query, limit=limit - len(results))
                    for trace in traces:
                        # Convert trace to legacy Memory format
                        mem = Memory(
                            memory_id=trace.trace_id,
                            content=trace.content,
                            layer=MemoryLayer.M2_SEMANTIC,
                            metadata=MemoryMetadata(user_id=user_id),
                            heat=HeatScore(
                                visit_count=trace.access_count,
                                interaction_depth=trace.importance,
                            ),
                            created_at=trace.created_at,
                        )
                        results.append(mem)
                        if len(results) >= limit:
                            break
                except Exception:
                    pass

        return results

    def get_stats(self) -> Dict:
        """Get memory statistics from both systems."""
        base_stats = {
            "total_memories": sum(len(mems) for mems in self.memories.values()),
            "by_layer": {
                layer.value: len(mems) for layer, mems in self.memories.items()
            },
            "consolidation_interval": self.consolidation_interval,
        }

        # Add enhanced memory stats if available
        enhanced = self._get_enhanced_memory()
        if enhanced:
            try:
                base_stats["enhanced_memory"] = {
                    "total_traces": len(enhanced.traces),
                    "working_memory_size": len(enhanced.working_memory),
                    "patterns_extracted": len(enhanced.extracted_patterns),
                }
            except Exception:
                pass

        # Add monitoring-specific metrics
        monitoring_stats = {
            "memory_monitoring": {
                "total_memories": sum(len(mems) for mems in self.memories.values()),
                "memories_by_layer": {
                    layer.value: len(mems) for layer, mems in self.memories.items()
                },
                "consolidation_interval": self.consolidation_interval,
                "layers_count": len(self.memories),
                "avg_memories_per_layer": (
                    sum(len(mems) for mems in self.memories.values()) /
                    max(len(self.memories), 1)
                ),
                "total_embedding_dimensions": sum(
                    getattr(layer, 'embedding_dimension', 0)
                    for layer in self.memories.keys()
                ),
                "consolidation_enabled": self.consolidation_interval > 0,
            }
        }

        # Merge base stats with monitoring stats
        base_stats.update(monitoring_stats)
        return base_stats

    async def start_consolidation(self):
        """Start automatic consolidation."""

        async def consolidation_loop():
            while True:
                await asyncio.sleep(self.consolidation_interval)
                await self.consolidate()

        self._consolidation_task = asyncio.create_task(consolidation_loop())
        logger.info("Memory consolidation started")

    async def consolidate(self):
        """Run memory consolidation on both systems."""
        logger.info("Running memory consolidation...")

        # Consolidate enhanced memory system
        enhanced = self._get_enhanced_memory()
        if enhanced:
            try:
                await enhanced.consolidate()
                logger.info("Enhanced memory consolidation complete")
            except Exception as e:
                logger.warning(f"Enhanced memory consolidation failed: {e}")

        logger.info("Memory consolidation complete")

    def stop(self):
        """Stop consolidation task."""
        if self._consolidation_task:
            self._consolidation_task.cancel()
            logger.info("Memory consolidation stopped")

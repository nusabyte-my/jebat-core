"""
JEBAT Memory Manager

Central controller for 5-layer memory system with:
- Automatic consolidation
- Heat-based importance scoring
- Cross-layer search
- User profile aggregation
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
)

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central memory management system.

    Manages 5-layer memory with automatic consolidation,
    heat scoring, and intelligent retrieval.
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
        logger.info("MemoryManager initialized with all memory layers")

    async def store(
        self,
        content: str,
        layer: MemoryLayer = MemoryLayer.M1_EPISODIC,
        user_id: str = "default",
        metadata: Optional[MemoryMetadata] = None,
    ) -> str:
        """
        Store a memory.

        Args:
            content: Memory content
            layer: Target memory layer
            user_id: User identifier
            metadata: Optional metadata

        Returns:
            Memory ID
        """
        memory = Memory(
            memory_id=f"mem_{datetime.now(timezone.utc).timestamp()}",
            content=content,
            layer=layer,
            metadata=metadata or MemoryMetadata(user_id=user_id),
            heat=HeatScore(),
            created_at=datetime.now(timezone.utc),
        )

        self.memories[layer].append(memory)
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
        Search memories, ranked by heat score (importance), not insertion order.

        Matching memories have their heat updated on access (visit frequency
        and recency rise), so frequently-retrieved memories surface higher over
        time — the core premise of the heat-scoring architecture.

        Args:
            query: Search query
            user_id: User identifier
            layer: Optional layer filter
            limit: Max results

        Returns:
            List of matching memories, highest-heat first
        """
        query_lower = query.lower()
        layers = [layer] if layer else list(MemoryLayer)

        matches: List[Memory] = []
        for lyr in layers:
            for memory in self.memories[lyr]:
                if memory.metadata.user_id != user_id:
                    continue
                if query_lower in memory.content.lower():
                    self._register_access(memory)
                    matches.append(memory)

        # Rank by live heat score (descending), then recency as tie-breaker.
        matches.sort(
            key=lambda m: (m.heat.calculate(), m.created_at),
            reverse=True,
        )
        return matches[:limit]

    def _register_access(self, memory: Memory) -> None:
        """Bump heat signals when a memory is retrieved.

        Visit frequency climbs toward 1.0 with diminishing returns; recency
        resets to fresh. This is what lets hot memories rank above cold ones.
        """
        heat = memory.heat
        # Diminishing-returns increment so a single hot memory can't dominate.
        heat.visit_frequency = min(1.0, heat.visit_frequency + (1.0 - heat.visit_frequency) * 0.2)
        heat.recency = 1.0
        memory.updated_at = datetime.now(timezone.utc)

    def get_stats(self) -> Dict:
        """Get memory statistics."""
        base_stats = {
            "total_memories": sum(len(mems) for mems in self.memories.values()),
            "by_layer": {
                layer.value: len(mems) for layer, mems in self.memories.items()
            },
            "consolidation_interval": self.consolidation_interval,
        }
        
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
        """Run memory consolidation: decay idle memories and prune cold ones.

        Consolidation is what keeps the store from growing unbounded and lets
        the heat ranking stay meaningful over time:
          1. Recency decays on every memory (older, untouched memories cool).
          2. Memories whose heat falls below the prune threshold are dropped,
             except CRITICAL/HIGH importance which are always retained.
        """
        logger.info("Running memory consolidation...")

        decay = float(self.config.get("recency_decay", 0.9))
        prune_threshold = float(self.config.get("prune_threshold", 0.05))
        protected = {MemoryImportance.CRITICAL, MemoryImportance.HIGH}

        pruned = 0
        for layer, memories in self.memories.items():
            survivors: List[Memory] = []
            for memory in memories:
                # Cool down recency; frequently-accessed memories were just
                # refreshed to 1.0 by _register_access so they decay slowly.
                memory.heat.recency *= decay

                if (
                    memory.heat.calculate() < prune_threshold
                    and memory.metadata.importance not in protected
                ):
                    pruned += 1
                    continue
                survivors.append(memory)
            self.memories[layer] = survivors

        logger.info(f"Memory consolidation complete (pruned {pruned} cold memories)")
        return pruned

    def stop(self):
        """Stop consolidation task."""
        if self._consolidation_task:
            self._consolidation_task.cancel()
            logger.info("Memory consolidation stopped")

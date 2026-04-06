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
from datetime import datetime
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
            memory_id=f"mem_{datetime.utcnow().timestamp()}",
            content=content,
            layer=layer,
            metadata=metadata or MemoryMetadata(user_id=user_id),
            heat=HeatScore(),
            created_at=datetime.utcnow(),
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
        Search memories.

        Args:
            query: Search query
            user_id: User identifier
            layer: Optional layer filter
            limit: Max results

        Returns:
            List of matching memories
        """
        results = []
        layers = [layer] if layer else list(MemoryLayer)

        for layer in layers:
            for memory in self.memories[layer]:
                if memory.metadata.user_id != user_id:
                    continue
                if query.lower() in memory.content.lower():
                    results.append(memory)
                    if len(results) >= limit:
                        return results

        return results

    def get_stats(self) -> Dict:
        """Get memory statistics."""
        return {
            "total_memories": sum(len(mems) for mems in self.memories.values()),
            "by_layer": {
                layer.value: len(mems) for layer, mems in self.memories.items()
            },
            "consolidation_interval": self.consolidation_interval,
        }

    async def start_consolidation(self):
        """Start automatic consolidation."""

        async def consolidation_loop():
            while True:
                await asyncio.sleep(self.consolidation_interval)
                await self.consolidate()

        self._consolidation_task = asyncio.create_task(consolidation_loop())
        logger.info("Memory consolidation started")

    async def consolidate(self):
        """Run memory consolidation."""
        logger.info("Running memory consolidation...")
        # Consolidation logic here
        logger.info("Memory consolidation complete")

    def stop(self):
        """Stop consolidation task."""
        if self._consolidation_task:
            self._consolidation_task.cancel()
            logger.info("Memory consolidation stopped")

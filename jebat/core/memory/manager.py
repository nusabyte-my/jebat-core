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
from pathlib import Path
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
        """Lazily initialize EnhancedMemorySystem (with vector search if configured)."""
        if self._enhanced_memory is None:
            try:
                from jebat.features.memory import EnhancedMemorySystem

                ghost_client, embedding_fn = (None, None)
                if self.config.get("vector_search"):
                    ghost_client, embedding_fn = self._build_vector_search()

                # Coerce: the config carries a string, but the enhanced system
                # calls `.mkdir()` on it. Passing the raw string raised
                # AttributeError into the bare `except` below, which returned
                # None and silently downgraded every read to legacy-substring.
                storage_path = self.config.get("storage_path")
                self._enhanced_memory = EnhancedMemorySystem(
                    storage_path=Path(storage_path) if storage_path else None,
                    ghost_client=ghost_client,
                    embedding_fn=embedding_fn,
                )
            except Exception:
                # Not silent: a failure here costs similarity/vector recall for
                # the whole process, and two real bugs hid behind this `pass`.
                logger.warning(
                    "EnhancedMemorySystem unavailable; memory reads fall back to "
                    "legacy substring search",
                    exc_info=True,
                )
        return self._enhanced_memory

    def _build_vector_search(self):
        """Best-effort build a Ghost DB client + embedding function.

        Returns (ghost_client, embedding_fn) or (None, None) if unavailable
        (e.g. sqlite-vec not installed, or no embedding model configured). When
        unavailable, EnhancedMemorySystem transparently falls back to n-gram
        similarity, so recall still works.
        """
        try:
            import os

            from jebat.features.ghost_db.client import GhostClient, GhostConfig
            from jebat.features.ghost_db.embeddings import get_embedding_provider

            path = self.config.get("ghost_db_path") or os.path.expanduser(
                "~/.jebat/ghost/memory.db"
            )
            client = GhostClient(config=GhostConfig(path=path))

            provider = get_embedding_provider(
                self.config.get("embedding_provider", "local"),
                self.config.get("embedding_model"),
            )

            def embedding_fn(text: str):
                return provider.embed([text]).vectors[0].tolist()

            async def aembedding_fn(text: str):
                return embedding_fn(text)

            return client, aembedding_fn
        except Exception:
            return None, None

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
        normalized = " ".join(content.lower().split())
        for existing in self.memories[layer]:
            if (
                existing.metadata.user_id == user_id
                and " ".join(existing.content.lower().split()) == normalized
            ):
                return existing.memory_id

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
                # `legacy_id` must NOT go in `context`. EnhancedMemorySystem.encode
                # dedups on (memory_type, content, context), and the legacy id is
                # `mem_<timestamp>` — unique per call — so including it defeated
                # dedup entirely and re-stored the same text on every call.
                # Measured: 17 identical traces for one sentence. The linkage is
                # carried by `source_trace_id` instead, which is not compared.
                await enhanced.encode(
                    content=content,
                    memory_type=mem_type,
                    importance=0.5,
                    context={"user_id": user_id},
                    source_trace_id=memory.memory_id,
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
                    seen = {m.content for m in results}
                    for trace in traces:
                        if trace.context.get("user_id") != user_id:
                            continue
                        if trace.content in seen:
                            continue
                        # Convert trace to legacy Memory format
                        mem = Memory(
                            memory_id=trace.trace_id,
                            content=trace.content,
                            layer=MemoryLayer.M2_SEMANTIC,
                            metadata=MemoryMetadata(
                                user_id=user_id,
                                source=trace.context.get("source"),
                                context={"trace_id": trace.trace_id},
                            ),
                            heat=HeatScore(
                                # `HeatScore` field names matter: this call used
                                # `visit_count=`, which does not exist, so every
                                # enhanced result raised TypeError into the bare
                                # `except` below and the whole similarity/vector
                                # branch silently returned nothing.
                                visit_frequency=min(1.0, trace.access_count * 0.1),
                                interaction_depth=trace.importance,
                            ),
                            created_at=trace.created_at,
                        )
                        results.append(mem)
                        seen.add(trace.content)
                        if len(results) >= limit:
                            break
                except Exception:
                    # Never silent: swallowing here hid a total failure of the
                    # enhanced recall branch (see the HeatScore note above).
                    logger.warning(
                        "Enhanced memory search failed; returning legacy-only results",
                        exc_info=True,
                    )

        return results

    def forget(self, memory_id: str, user_id: str = "default") -> bool:
        """Delete a memory by id from both the legacy and enhanced stores.

        Synchronous, like `search`/`get_stats`, so async callers can offload it
        with `asyncio.to_thread`.

        Both stores must be cleared together. `asearch` merges enhanced traces
        into its results, so dropping only the legacy record leaves the same
        content reachable through the enhanced store — a forget that looks
        like it worked and then un-forgets itself on the next search.

        Returns True when something was actually removed.
        """
        # Resolve the id against BOTH stores before deleting. A legacy id
        # (`mem_<ts>`) is the enhanced trace's `source_trace`, but an id
        # returned by `asearch` is the *enhanced trace* id — and deleting only
        # that direction leaves the legacy record behind, so the memory still
        # shows up in `get_stats` (and the two stores drift apart).
        legacy_ids = {memory_id}
        enhanced_ids = {memory_id}
        enhanced = self._get_enhanced_memory()
        if enhanced is not None:
            for trace_id, trace in enhanced.traces.items():
                if trace_id != memory_id and trace.source_trace != memory_id:
                    continue
                legacy_ids.add(trace_id)
                enhanced_ids.add(trace_id)
                if trace.source_trace:
                    legacy_ids.add(trace.source_trace)
                    enhanced_ids.add(trace.source_trace)

        removed = False
        for layer in MemoryLayer:
            kept = []
            for memory in self.memories[layer]:
                if memory.memory_id in legacy_ids and memory.metadata.user_id == user_id:
                    removed = True
                else:
                    kept.append(memory)
            self.memories[layer] = kept

        if enhanced is not None:
            try:
                for trace_id in enhanced_ids:
                    if enhanced.forget(trace_id):
                        removed = True
            except Exception:
                logger.warning("Enhanced memory forget failed", exc_info=True)

        return removed

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

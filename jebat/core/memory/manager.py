"""Memory manager for the 5-layer eternal memory system."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jebat.core.memory.layers import MemoryLayer

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages the 5-layer memory system: Sensory → Episodic → Semantic → Conceptual → Permanent."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._store: Dict[str, List[Dict[str, Any]]] = {
            layer.value: [] for layer in MemoryLayer
        }

    async def store(
        self,
        content: str,
        layer: MemoryLayer = MemoryLayer.M1_EPISODIC,
        user_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        memory_id = str(uuid4())
        entry = {
            "id": memory_id,
            "content": content,
            "user_id": user_id,
            "metadata": metadata or {},
        }
        self._store[layer.value].append(entry)
        return memory_id

    async def retrieve(
        self,
        query: str,
        layer: Optional[MemoryLayer] = None,
        user_id: str = "default",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        layers = [layer] if layer else list(MemoryLayer)
        results = []
        for mem_layer in layers:
            for entry in self._store.get(mem_layer.value, []):
                if entry.get("user_id") == user_id:
                    results.append({**entry, "layer": mem_layer.value})
        return results[:limit]

    async def search_memories(
        self, query: str, user_id: str = "default", limit: int = 10
    ) -> List[Dict[str, Any]]:
        results = []
        for layer_entries in self._store.values():
            for entry in layer_entries:
                if query.lower() in entry.get("content", "").lower():
                    results.append(entry)
        return results[:limit]

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        return {"user_id": user_id, "memory_count": sum(
            len(entries) for entries in self._store.values()
        )}

    def get_memory_stats(self) -> Dict[str, Any]:
        return {
            layer.value: len(entries)
            for layer, entries in zip(MemoryLayer, self._store.values())
        }

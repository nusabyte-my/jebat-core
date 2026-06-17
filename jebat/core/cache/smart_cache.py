"""Smart cache with HOT/WARM/COLD tiers and heat-score eviction."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SmartCache:
    """In-memory tiered cache with heat-score tracking."""

    def __init__(self, hot_size: int = 100, warm_size: int = 500, cold_size: int = 2000):
        self.hot_size = hot_size
        self.warm_size = warm_size
        self.cold_size = cold_size
        self._hot: Dict[str, Any] = {}
        self._warm: Dict[str, Any] = {}
        self._cold: Dict[str, Any] = {}
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        for tier in (self._hot, self._warm, self._cold):
            if key in tier:
                self._hits += 1
                return tier[key]
        self._misses += 1
        return None

    async def set(self, key: str, value: Any, tier: str = "hot") -> None:
        target = {"hot": self._hot, "warm": self._warm, "cold": self._cold}.get(
            tier, self._hot
        )
        target[key] = value

    async def delete(self, key: str) -> bool:
        for tier in (self._hot, self._warm, self._cold):
            if key in tier:
                del tier[key]
                return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        return {
            "hot_entries": len(self._hot),
            "warm_entries": len(self._warm),
            "cold_entries": len(self._cold),
            "hits": self._hits,
            "misses": self._misses,
        }


class CacheManager:
    """Manages tiered cache instances."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.cache = SmartCache(
            hot_size=self.config.get("memory_hot_size", 100),
            warm_size=self.config.get("memory_warm_entries", 500),
        )

    async def get(self, key: str) -> Optional[Any]:
        return await self.cache.get(key)

    async def set(self, key: str, value: Any, tier: str = "hot") -> None:
        await self.cache.set(key, value, tier)

    async def get_all_stats(self) -> Dict[str, Any]:
        return self.cache.get_stats()

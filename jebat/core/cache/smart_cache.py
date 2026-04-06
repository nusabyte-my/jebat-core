"""
JEBAT Smart Cache

Multi-tier caching system with intelligent eviction.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, OrderedDict

logger = logging.getLogger(__name__)


class CacheTier(str, Enum):
    """Cache tiers."""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    tier: CacheTier
    heat: float = 1.0
    accesses: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def access(self):
        """Record access."""
        self.accesses += 1
        self.last_accessed = datetime.utcnow()
        self.heat = min(1.0, self.heat + 0.1)


class SmartCache:
    """
    Smart cache with heat-based eviction.

    Automatically promotes/demotes entries between tiers
    based on access patterns.
    """

    def __init__(
        self,
        tier: CacheTier = CacheTier.HOT,
        max_size: int = 1000,
        ttl_seconds: Optional[int] = None,
    ):
        """
        Initialize smart cache.

        Args:
            tier: Cache tier
            max_size: Maximum entries
            ttl_seconds: Optional TTL
        """
        self.tier = tier
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else None
        self.entries: OrderedDict[str, CacheEntry] = OrderedDict()
        logger.info(f"SmartCache initialized: {tier.value}, max={max_size}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.entries:
            return None

        entry = self.entries[key]
        if entry.is_expired():
            del self.entries[key]
            return None

        entry.access()
        self.entries.move_to_end(key)
        return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set value in cache."""
        expires = None
        if ttl_seconds:
            expires = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        elif self.ttl:
            expires = datetime.utcnow() + self.ttl

        entry = CacheEntry(
            key=key,
            value=value,
            tier=self.tier,
            expires_at=expires,
        )

        if len(self.entries) >= self.max_size:
            await self._evict()

        self.entries[key] = entry
        logger.debug(f"Cached: {key} in {self.tier.value}")

    async def _evict(self):
        """Evict lowest heat entry."""
        if not self.entries:
            return

        # Remove oldest (lowest heat) entry
        self.entries.popitem(last=False)
        logger.debug(f"Evicted from {self.tier.value}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "tier": self.tier.value,
            "size": len(self.entries),
            "max_size": self.max_size,
            "hit_rate": self._calculate_hit_rate(),
        }

    def _calculate_hit_rate(self) -> float:
        """Calculate hit rate."""
        if not self.entries:
            return 0.0
        total_accesses = sum(e.accesses for e in self.entries.values())
        return total_accesses / len(self.entries) if self.entries else 0.0


class CacheManager:
    """
    Multi-tier cache manager.

    Manages HOT, WARM, and COLD cache tiers with
    automatic promotion/demotion.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize cache manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Initialize tiers
        hot_config = self.config.get("hot", {"max_size": 1000, "ttl": 300})
        warm_config = self.config.get("warm", {"max_size": 5000, "ttl": 3600})
        cold_config = self.config.get("cold", {"max_size": 20000, "ttl": 86400})

        self.hot = SmartCache(
            tier=CacheTier.HOT,
            max_size=hot_config.get("max_size", 1000),
            ttl_seconds=hot_config.get("ttl", 300),
        )
        self.warm = SmartCache(
            tier=CacheTier.WARM,
            max_size=warm_config.get("max_size", 5000),
            ttl_seconds=warm_config.get("ttl", 3600),
        )
        self.cold = SmartCache(
            tier=CacheTier.COLD,
            max_size=cold_config.get("max_size", 20000),
            ttl_seconds=cold_config.get("ttl", 86400),
        )

        logger.info("CacheManager initialized with 3 tiers")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from any tier."""
        # Try HOT first
        value = await self.hot.get(key)
        if value is not None:
            return value

        # Try WARM
        value = await self.warm.get(key)
        if value is not None:
            # Promote to HOT
            await self.hot.set(key, value)
            return value

        # Try COLD
        value = await self.cold.get(key)
        if value is not None:
            # Promote to WARM
            await self.warm.set(key, value)
            return value

        return None

    async def set(self, key: str, value: Any, tier: CacheTier = CacheTier.HOT):
        """Set value in specified tier."""
        if tier == CacheTier.HOT:
            await self.hot.set(key, value)
        elif tier == CacheTier.WARM:
            await self.warm.set(key, value)
        else:
            await self.cold.set(key, value)

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all tiers."""
        return {
            "hot": self.hot.get_stats(),
            "warm": self.warm.get_stats(),
            "cold": self.cold.get_stats(),
        }

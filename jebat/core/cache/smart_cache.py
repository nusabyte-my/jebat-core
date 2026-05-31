"""JEBAT Smart Cache

Multi-tier caching system with intelligent eviction and heat-based optimization.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, OrderedDict, Set, Tuple
from collections import defaultdict, deque

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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    # Dependency tracking
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    # Access pattern tracking
    access_times: deque = field(default_factory=lambda: deque(maxlen=100))
    size_estimate: int = 0

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def access(self):
        """Record access."""
        self.accesses += 1
        now = datetime.now(timezone.utc)
        self.last_accessed = now
        self.access_times.append(now.timestamp())
        
        # Heat calculation with recency weighting
        # More recent accesses increase heat more
        if len(self.access_times) >= 2:
            time_span = self.access_times[-1] - self.access_times[0]
            if time_span > 0:
                access_rate = len(self.access_times) / time_span  # accesses per second
                # Boost heat for frequently accessed items
                self.heat = min(10.0, self.heat + (access_rate * 0.1))
        else:
            self.heat = min(10.0, self.heat + 0.1)

    def get_heat_score(self) -> float:
        """Get current heat score for eviction decisions."""
        # Base heat from access patterns
        base_heat = self.heat
        
        # Recency factor - more recent = higher score
        if self.access_times:
            time_since_last = time.time() - self.access_times[-1]
            recency_factor = max(0.1, min(2.0, 300.0 / max(time_since_last, 1)))  # 5 min window
        else:
            recency_factor = 0.1
            
        # Frequency factor
        frequency_factor = min(2.0, self.accesses / 100.0)  # Normalize to ~100 accesses
        
        return base_heat * recency_factor * frequency_factor


class SmartCache:
    """Smart cache with heat-based eviction and intelligent tier management."""

    def __init__(
        self,
        tier: CacheTier = CacheTier.HOT,
        max_size: int = 1000,
        ttl_seconds: Optional[int] = None,
        enable_monitoring: bool = True,
    ):
        """Initialize smart cache.

        Args:
            tier: Cache tier
            max_size: Maximum entries
            ttl_seconds: Optional TTL
            enable_monitoring: Enable detailed monitoring metrics
        """
        self.tier = tier
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else None
        self.entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self.enable_monitoring = enable_monitoring
        
        # Monitoring metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.promotions = 0
        self.demotions = 0
        self.total_get_calls = 0
        
        logger.info(f"SmartCache initialized: {tier.value}, max={max_size}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        self.total_get_calls += 1
        
        if key not in self.entries:
            self.misses += 1
            return None

        entry = self.entries[key]
        if entry.is_expired():
            del self.entries[key]
            self.misses += 1
            return None

        entry.access()
        self.hits += 1
        self.entries.move_to_end(key)
        return entry.value

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache."""
        expires = None
        if ttl_seconds:
            expires = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        elif self.ttl:
            expires = datetime.now(timezone.utc) + self.ttl

        # Estimate size (simplified)
        size_estimate = len(str(key)) + len(str(value))

        entry = CacheEntry(
            key=key,
            value=value,
            tier=self.tier,
            expires_at=expires,
            size_estimate=size_estimate,
        )

        # Check if we need to evict
        if len(self.entries) >= self.max_size:
            await self._evict()

        self.entries[key] = entry
        logger.debug(f"Cached: {key} in {self.tier.value}")

    async def _evict(self) -> None:
        """Evict entry with lowest heat score."""
        if not self.entries:
            return

        # Find entry with lowest heat score
        lowest_heat_key = None
        lowest_heat_score = float('inf')
        
        for key, entry in self.entries.items():
            heat_score = entry.get_heat_score()
            if heat_score < lowest_heat_score:
                lowest_heat_score = heat_score
                lowest_heat_key = key

        if lowest_heat_key is not None:
            del self.entries[lowest_heat_key]
            self.evictions += 1
            logger.debug(f"Evicted {lowest_heat_key} from {self.tier.value} (heat={lowest_heat_score:.2f})")

    def promote_entry(self, key: str) -> bool:
        """Promote entry to next higher tier (called by CacheManager)."""
        if key not in self.entries:
            return False
            
        entry = self.entries[key]
        if self.tier == CacheTier.HOT:
            return False  # Already at highest tier
            
        # Move to next tier (this is handled by CacheManager)
        self.promotions += 1
        logger.debug(f"Promoting {key} from {self.tier.value}")
        return True

    def demote_entry(self, key: str) -> bool:
        """Demote entry to next lower tier (called by CacheManager)."""
        if key not in self.entries:
            return False
            
        if self.tier == CacheTier.COLD:
            return False  # Already at lowest tier
            
        self.demotions += 1
        logger.debug(f"Demoting {key} from {self.tier.value}")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        base_stats = {
            "tier": self.tier.value,
            "size": len(self.entries),
            "max_size": self.max_size,
            "hit_rate": self._calculate_hit_rate(),
        }

        if self.enable_monitoring:
            # Add monitoring-specific metrics
            monitoring_stats = {
                "cache_monitoring": {
                    "tier": self.tier.value,
                    "size": len(self.entries),
                    "max_size": self.max_size,
                    "utilization_ratio": len(self.entries) / max(self.max_size, 1),
                    "hit_rate": self._calculate_hit_rate(),
                    "total_accesses": self.hits + self.misses,
                    "hit_count": self.hits,
                    "miss_count": self.misses,
                    "eviction_count": self.evictions,
                    "promotion_count": self.promotions,
                    "demotion_count": self.demotions,
                    "total_get_calls": self.total_get_calls,
                    "avg_accesses_per_entry": (
                        sum(e.accesses for e in self.entries.values()) /
                        max(len(self.entries), 1)
                    ) if self.entries else 0,
                    "is_full": len(self.entries) >= self.max_size,
                    "is_empty": len(self.entries) == 0,
                }
            }
            
            # Merge base stats with monitoring stats
            base_stats.update(monitoring_stats)

        return base_stats

    def _calculate_hit_rate(self) -> float:
        """Calculate hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def get_top_entries_by_heat(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get top entries by heat score for monitoring."""
        if not self.entries:
            return []
            
        entries_with_heat = [
            (key, entry.get_heat_score()) 
            for key, entry in self.entries.items()
        ]
        entries_with_heat.sort(key=lambda x: x[1], reverse=True)
        return entries_with_heat[:limit]


class CacheManager:
    """Multi-tier cache manager with intelligent heat-based tier management."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize cache manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Initialize tiers with configuration from plan
        hot_config = self.config.get("hot", {"max_size": 1000, "ttl": 300})   # 100MB, 1000 entries, <10ms
        warm_config = self.config.get("warm", {"max_size": 5000, "ttl": 3600}) # 500MB, 5000 entries, <100ms
        cold_config = self.config.get("cold", {"max_size": 20000, "ttl": 86400}) # 2GB, 20000 entries, <500ms

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

        # Tier promotion/demotion thresholds (from heat scoring)
        self.promotion_threshold = 0.8   # Promote if heat > 80% of max
        self.demotion_threshold = 0.3    # Demote if heat < 30% of max
        
        logger.info("CacheManager initialized with 3 tiers")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from any tier with intelligent tier promotion."""
        # Try HOT first
        value = await self.hot.get(key)
        if value is not None:
            return value

        # Try WARM
        value = await self.warm.get(key)
        if value is not None:
            # Promote to HOT if heat score is high enough
            # Find the entry in warm to check its heat
            if key in self.warm.entries:
                entry = self.warm.entries[key]
                heat_score = entry.get_heat_score()
                # Normalize heat score (assuming max ~10.0 from our calculations)
                normalized_heat = min(1.0, heat_score / 10.0)
                if normalized_heat > self.promotion_threshold:
                    # Promote to HOT
                    await self.hot.set(key, value)
                    # Remove from WARM to avoid duplication
                    del self.warm.entries[key]
                    self.warm.promotions += 1
                    logger.debug(f"Promoted {key} from WARM to HOT (heat={heat_score:.2f})")
            return value

        # Try COLD
        value = await self.cold.get(key)
        if value is not None:
            # Promote to WARM if heat score warrants it
            if key in self.cold.entries:
                entry = self.cold.entries[key]
                heat_score = entry.get_heat_score()
                normalized_heat = min(1.0, heat_score / 10.0)
                if normalized_heat > self.promotion_threshold * 0.5:  # Lower threshold for COLD->WARM
                    # Promote to WARM
                    await self.warm.set(key, value)
                    # Remove from COLD
                    del self.cold.entries[key]
                    self.cold.promotions += 1
                    logger.debug(f"Promoted {key} from COLD to WARM (heat={heat_score:.2f})")
            return value

        return None

    async def set(
        self, key: str, value: Any, tier: CacheTier = CacheTier.HOT
    ) -> None:
        """Set value in specified tier."""
        if tier == CacheTier.HOT:
            await self.hot.set(key, value)
        elif tier == CacheTier.WARM:
            await self.warm.set(key, value)
        else:
            await self.cold.set(key, value)

    async def evict_lowest_heat_across_tiers(self, count: int = 1) -> List[str]:
        """Evict the lowest heat entries across all tiers."""
        evicted_keys = []
        
        # Collect all entries with their heat scores and tier info
        all_entries = []
        
        for tier_name, tier_cache in [("hot", self.hot), ("warm", self.warm), ("cold", self.cold)]:
            for key, entry in tier_cache.entries.items():
                heat_score = entry.get_heat_score()
                all_entries.append((key, heat_score, tier_name, tier_cache))
        
        # Sort by heat score (lowest first)
        all_entries.sort(key=lambda x: x[1])
        
        # Evict the lowest heat entries
        for i in range(min(count, len(all_entries))):
            key, heat_score, tier_name, tier_cache = all_entries[i]
            if key in tier_cache.entries:
                del tier_cache.entries[key]
                evicted_keys.append(key)
                # Increment eviction counter for the appropriate tier
                if tier_name == "hot":
                    tier_cache.evictions += 1
                elif tier_name == "warm":
                    tier_cache.evictions += 1
                else:
                    tier_cache.evictions += 1
                logger.debug(f"Evicted {key} from {tier_name} (heat={heat_score:.2f})")
                
        return evicted_keys

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all tiers."""
        return {
            "hot": self.hot.get_stats(),
            "warm": self.warm.get_stats(),
            "cold": self.cold.get_stats(),
        }

    def get_cache_health(self) -> Dict[str, Any]:
        """Get overall cache health metrics."""
        hot_stats = self.hot.get_stats()
        warm_stats = self.warm.get_stats()
        cold_stats = self.cold.get_stats()
        
        total_size = (
            hot_stats["size"] + 
            warm_stats["size"] + 
            cold_stats["size"]
        )
        total_capacity = (
            hot_stats["max_size"] + 
            warm_stats["max_size"] + 
            cold_stats["max_size"]
        )
        
        overall_hit_rate = 0
        total_requests = (
            hot_stats.get("cache_monitoring", {}).get("total_accesses", 0) +
            warm_stats.get("cache_monitoring", {}).get("total_accesses", 0) +
            cold_stats.get("cache_monitoring", {}).get("total_accesses", 0)
        )
        
        if total_requests > 0:
            total_hits = (
                hot_stats.get("cache_monitoring", {}).get("hit_count", 0) +
                warm_stats.get("cache_monitoring", {}).get("hit_count", 0) +
                cold_stats.get("cache_monitoring", {}).get("hit_count", 0)
            )
            overall_hit_rate = total_hits / total_requests
            
        return {
            "total_entries": total_size,
            "total_capacity": total_capacity,
            "utilization_ratio": total_size / max(total_capacity, 1),
            "overall_hit_rate": overall_hit_rate,
            "tier_distribution": {
                "hot": hot_stats["size"],
                "warm": warm_stats["size"],
                "cold": cold_stats["size"],
            },
            "total_evictions": (
                hot_stats.get("cache_monitoring", {}).get("eviction_count", 0) +
                warm_stats.get("cache_monitoring", {}).get("eviction_count", 0) +
                cold_stats.get("cache_monitoring", {}).get("eviction_count", 0)
            ),
        }
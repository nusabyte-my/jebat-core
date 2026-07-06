"""
JEBAT Cache System

3-tier smart cache with heat-based eviction:
- HOT: Frequently accessed (<10ms)
- WARM: Occasionally accessed (<100ms)
- COLD: Rarely accessed (<500ms)
"""

from .smart_cache import CacheManager, CacheTier, SmartCache

__all__ = ["CacheManager", "SmartCache", "CacheTier"]

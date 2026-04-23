"""
JEBAT Agent Performance Optimizations

Quick-win performance improvements:
- Model caching for frequent responses
- Connection pooling for LLM providers
- Request deduplication
- Smart routing
- Async processing
"""

import asyncio
import hashlib
import time
from typing import Any, Dict, List, Optional
from collections import OrderedDict
from dataclasses import dataclass, field
import json
import aiohttp


@dataclass
class CacheEntry:
    """Represents a cached response."""
    response: Any
    timestamp: float
    ttl: int  # Time-to-live in seconds
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl

    @property
    def age(self) -> float:
        return time.time() - self.timestamp


class LRUCache:
    """Least Recently Used cache with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            self.misses += 1
            return None

        entry = self._cache[key]
        if entry.is_expired:
            del self._cache[key]
            self.misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.hit_count += 1
        self.hits += 1
        return entry.response

    def put(self, key: str, value: Any, ttl: Optional[int] = None):
        """Put value in cache."""
        if key in self._cache:
            del self._cache[key]
        elif len(self._cache) >= self.max_size:
            # Remove least recently used
            self._cache.popitem(last=False)

        self._cache[key] = CacheEntry(
            response=value,
            timestamp=time.time(),
            ttl=ttl or self.default_ttl
        )

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def size(self) -> int:
        return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{self.hit_rate:.2%}"
        }


class ConnectionPool:
    """Connection pool for LLM providers."""

    def __init__(self, max_connections: int = 50, max_keepalive: int = 10):
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        self._pool_stats: Dict[str, Dict[str, int]] = {}

    async def get_session(self, provider: str) -> aiohttp.ClientSession:
        """Get or create a session for a provider."""
        if provider not in self._sessions:
            connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_keepalive,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self._sessions[provider] = aiohttp.ClientSession(connector=connector)
            self._pool_stats[provider] = {"created": 1, "requests": 0}
        else:
            self._pool_stats[provider]["requests"] += 1

        return self._sessions[provider]

    async def close_all(self):
        """Close all sessions."""
        for session in self._sessions.values():
            await session.close()
        self._sessions.clear()

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "active_connections": len(self._sessions),
            "max_connections": self.max_connections,
            "pool_stats": self._pool_stats
        }


class RequestDeduplicator:
    """Deduplicate identical concurrent requests."""

    def __init__(self):
        self._pending: Dict[str, asyncio.Future] = {}
        self._deduped_count = 0

    def _generate_key(self, provider: str, model: str, messages: List[Dict]) -> str:
        """Generate unique key for a request."""
        content = json.dumps({
            "provider": provider,
            "model": model,
            "messages": messages
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    async def execute(self, provider: str, model: str, messages: List[Dict], executor_func):
        """Execute request, deduplicating if same request is pending."""
        key = self._generate_key(provider, model, messages)

        if key in self._pending:
            # Same request is already being processed
            self._deduped_count += 1
            return await self._pending[key]

        # Create future for this request
        future = asyncio.get_event_loop().create_future()
        self._pending[key] = future

        try:
            result = await executor_func()
            future.set_result(result)
            return result
        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            del self._pending[key]

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "pending_requests": len(self._pending),
            "deduped_requests": self._deduped_count
        }


class SmartRouter:
    """Route requests to the fastest available provider."""

    def __init__(self):
        self._latencies: Dict[str, List[float]] = {}
        self._availability: Dict[str, bool] = {}

    def record_latency(self, provider: str, latency: float):
        """Record request latency for a provider."""
        if provider not in self._latencies:
            self._latencies[provider] = []

        # Keep last 10 measurements
        self._latencies[provider].append(latency)
        if len(self._latencies[provider]) > 10:
            self._latencies[provider] = self._latencies[provider][-10:]

    def record_availability(self, provider: str, available: bool):
        """Record provider availability."""
        self._availability[provider] = available

    def get_fastest_provider(self, providers: List[str]) -> Optional[str]:
        """Get the fastest available provider."""
        available = [p for p in providers if self._availability.get(p, True)]

        if not available:
            return None

        # Sort by average latency
        available.sort(key=lambda p: self._get_avg_latency(p))
        return available[0]

    def _get_avg_latency(self, provider: str) -> float:
        """Get average latency for a provider."""
        latencies = self._latencies.get(provider, [])
        return sum(latencies) / len(latencies) if latencies else float('inf')

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "providers": {
                p: {
                    "avg_latency": f"{self._get_avg_latency(p):.2f}s",
                    "available": self._availability.get(p, True),
                    "samples": len(self._latencies.get(p, []))
                }
                for p in set(list(self._latencies.keys()) + list(self._availability.keys()))
            }
        }


class SpeculativeDecoding:
    """Speed up generation by using a small draft model to predict tokens."""

    def __init__(self, draft_model: str = "phi3", target_model: str = "qwen2.5:14b"):
        self.draft_model = draft_model
        self.target_model = target_model
        self._lookahead = 5
        self._success_count = 0
        self._total_speculated = 0

    def record_success(self, accepted_tokens: int):
        self._success_count += 1
        self._total_speculated += accepted_tokens

    @property
    def efficiency_gain(self) -> float:
        return self._total_speculated / self._success_count if self._success_count > 0 else 0.0

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "draft_model": self.draft_model,
            "target_model": self.target_model,
            "avg_accepted_tokens": f"{self.efficiency_gain:.2f}",
            "lookahead": self._lookahead
        }


# Global instances for use across the application
response_cache = LRUCache(max_size=5000, default_ttl=7200)  # 2 hour TTL
connection_pool = ConnectionPool(max_connections=100, max_keepalive=20)
request_deduplicator = RequestDeduplicator()
smart_router = SmartRouter()
speculative_engine = SpeculativeDecoding()


def generate_cache_key(provider: str, model: str, messages: List[Dict], **kwargs) -> str:
    """Generate cache key for a request."""
    content = json.dumps({
        "provider": provider,
        "model": model,
        "messages": messages,
        **kwargs
    }, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def get_performance_stats() -> Dict[str, Any]:
    """Get comprehensive performance statistics."""
    return {
        "cache": response_cache.stats(),
        "connection_pool": connection_pool.stats,
        "deduplication": request_deduplicator.stats,
        "routing": smart_router.stats,
        "speculative_decoding": speculative_engine.stats
    }

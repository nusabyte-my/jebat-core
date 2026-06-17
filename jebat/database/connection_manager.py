"""Database connection management with asyncpg pool and Redis async client.

Provides:
    DatabaseManager — asyncpg connection pool with health checks and circuit breaker
    RedisManager — redis.asyncio client with health checks
    get_db / get_redis — FastAPI dependency-injection helpers
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncGenerator, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


class ConnectionState(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    RECOVERING = "RECOVERING"


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

@dataclass
class CircuitBreakerState:
    state: ConnectionState = ConnectionState.CONNECTED
    failure_count: int = 0
    last_failure_time: Optional[float] = None
    success_count: int = 0
    open_timeout: float = 60.0

    def record_success(self) -> None:
        self.success_count += 1
        self.failure_count = 0
        self.state = ConnectionState.CONNECTED

    def record_failure(self, threshold: int = 5) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= threshold:
            self.state = ConnectionState.ERROR

    def should_allow(self) -> bool:
        if self.state != ConnectionState.ERROR:
            return True
        if self.last_failure_time and (time.time() - self.last_failure_time) > self.open_timeout:
            self.state = ConnectionState.RECOVERING
            return True
        return False


# ---------------------------------------------------------------------------
# PostgreSQL connection manager (asyncpg)
# ---------------------------------------------------------------------------

class DatabaseManager:
    """Manages an asyncpg connection pool for PostgreSQL."""

    def __init__(
        self,
        dsn: Optional[str] = None,
        min_size: int = 2,
        max_size: int = 10,
        timeout: float = 10.0,
    ) -> None:
        self._dsn = dsn or self._build_dsn()
        self._min_size = min_size
        self._max_size = max_size
        self._timeout = timeout
        self._pool: Any = None  # asyncpg.Pool
        self._circuit = CircuitBreakerState()
        self._connected_at: Optional[float] = None

    # -- lifecycle ---------------------------------------------------------

    async def connect(self) -> None:
        """Create the connection pool."""
        import asyncpg  # noqa: F811

        logger.info("Connecting to PostgreSQL (%s) …", self._dsn.split("@")[-1])
        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
            timeout=self._timeout,
            command_timeout=30,
        )
        # Validate with a ping
        async with self._pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        self._circuit.record_success()
        self._connected_at = time.time()
        logger.info("PostgreSQL pool connected (min=%d, max=%d)", self._min_size, self._max_size)

    async def close(self) -> None:
        """Drain and close the pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            self._circuit.state = ConnectionState.DISCONNECTED
            logger.info("PostgreSQL pool closed.")

    # -- health ------------------------------------------------------------

    async def ping(self) -> bool:
        """Return True if a ping succeeds."""
        if self._pool is None:
            return False
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            self._circuit.record_success()
            return True
        except Exception as exc:
            logger.warning("PostgreSQL ping failed: %s", exc)
            self._circuit.record_failure()
            return False

    async def health(self) -> dict[str, Any]:
        """Return a health status dict."""
        ok = await self.ping()
        return {
            "status": "connected" if ok else "error",
            "backend": "postgresql",
            "dsn_host": self._dsn.split("@")[-1] if "@" in self._dsn else "unknown",
            "pool_size": self._pool.get_size() if self._pool else 0,
            "pool_free_size": self._pool.get_idle_size() if self._pool else 0,
            "uptime_s": round(time.time() - self._connected_at, 1) if self._connected_at else None,
            "circuit": self._circuit.state.value,
        }

    # -- query helpers -----------------------------------------------------

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """Execute a SELECT and return rows as dicts."""
        if not self._circuit.should_allow():
            raise RuntimeError("Circuit breaker open — PostgreSQL unavailable")
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            self._circuit.record_success()
            return [dict(r) for r in rows]

    async def fetchrow(self, query: str, *args: Any) -> Optional[dict[str, Any]]:
        """Execute a SELECT and return one row as dict."""
        if not self._circuit.should_allow():
            raise RuntimeError("Circuit breaker open — PostgreSQL unavailable")
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            self._circuit.record_success()
            return dict(row) if row else None

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Execute a query and return a single scalar value."""
        if not self._circuit.should_allow():
            raise RuntimeError("Circuit breaker open — PostgreSQL unavailable")
        async with self._pool.acquire() as conn:
            val = await conn.fetchval(query, *args)
            self._circuit.record_success()
            return val

    async def execute(self, query: str, *args: Any) -> str:
        """Execute an INSERT/UPDATE/DELETE and return status tag."""
        if not self._circuit.should_allow():
            raise RuntimeError("Circuit breaker open — PostgreSQL unavailable")
        async with self._pool.acquire() as conn:
            status = await conn.execute(query, *args)
            self._circuit.record_success()
            return status

    async def executemany(self, query: str, args_list: list[tuple[Any, ...]]) -> None:
        """Execute a query against many argument sets."""
        if not self._circuit.should_allow():
            raise RuntimeError("Circuit breaker open — PostgreSQL unavailable")
        async with self._pool.acquire() as conn:
            await conn.executemany(query, args_list)
            self._circuit.record_success()

    async def fetch_json(self, query: str, *args: Any) -> Any:
        """Execute a query and parse the first column as JSON."""
        raw = await self.fetchval(query, *args)
        if raw is None:
            return None
        if isinstance(raw, str):
            return json.loads(raw)
        return raw

    # -- private -----------------------------------------------------------

    @staticmethod
    def _build_dsn() -> str:
        import os
        return os.getenv(
            "DATABASE_URL",
            "postgresql://jebat:jebat_password@localhost:5432/jebat_db",
        )


# ---------------------------------------------------------------------------
# Redis connection manager
# ---------------------------------------------------------------------------

class RedisManager:
    """Manages a redis.asyncio client."""

    def __init__(
        self,
        url: Optional[str] = None,
        decode_responses: bool = True,
    ) -> None:
        self._url = url or self._build_url()
        self._decode = decode_responses
        self._client: Any = None  # redis.asyncio.Redis
        self._circuit = CircuitBreakerState()
        self._connected_at: Optional[float] = None

    # -- lifecycle ---------------------------------------------------------

    async def connect(self) -> None:
        """Create the Redis connection."""
        import redis.asyncio as aioredis  # noqa: F811

        logger.info("Connecting to Redis (%s) …", self._url.split("@")[-1] if "@" in self._url else self._url)
        self._client = aioredis.from_url(
            self._url,
            decode_responses=self._decode,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        # Validate
        await self._client.ping()
        self._circuit.record_success()
        self._connected_at = time.time()
        logger.info("Redis connected.")

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._circuit.state = ConnectionState.DISCONNECTED
            logger.info("Redis closed.")

    # -- health ------------------------------------------------------------

    async def ping(self) -> bool:
        """Return True if PING succeeds."""
        if self._client is None:
            return False
        try:
            ok = await self._client.ping()
            if ok:
                self._circuit.record_success()
            return bool(ok)
        except Exception as exc:
            logger.warning("Redis ping failed: %s", exc)
            self._circuit.record_failure()
            return False

    async def health(self) -> dict[str, Any]:
        """Return a health status dict."""
        ok = await self.ping()
        info: dict[str, Any] = {}
        if ok and self._client is not None:
            try:
                raw_info = await self._client.info("memory")
                info = {
                    "used_memory_human": raw_info.get("used_memory_human", "unknown"),
                    "connected_clients": raw_info.get("connected_clients", 0),
                }
            except Exception:
                pass
        return {
            "status": "connected" if ok else "error",
            "backend": "redis",
            "url_host": self._url.split("@")[-1] if "@" in self._url else self._url,
            "uptime_s": round(time.time() - self._connected_at, 1) if self._connected_at else None,
            "circuit": self._circuit.state.value,
            **info,
        }

    # -- key/value helpers -------------------------------------------------

    async def get(self, key: str) -> Optional[str]:
        if self._client is None:
            return None
        return await self._client.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        if self._client is not None:
            await self._client.set(key, value, ex=ex)

    async def delete(self, *keys: str) -> int:
        if self._client is None or not keys:
            return 0
        return await self._client.delete(*keys)

    async def exists(self, key: str) -> bool:
        if self._client is None:
            return False
        return bool(await self._client.exists(key))

    async def incr(self, key: str) -> int:
        if self._client is None:
            return 0
        return await self._client.incr(key)

    async def publish(self, channel: str, message: str) -> int:
        if self._client is None:
            return 0
        return await self._client.publish(channel, message)

    @property
    def client(self) -> Any:
        """Direct access to the underlying redis.asyncio client."""
        return self._client

    # -- private -----------------------------------------------------------

    @staticmethod
    def _build_url() -> str:
        import os
        return os.getenv("REDIS_URL", "redis://localhost:6379/0")


# ---------------------------------------------------------------------------
# Singleton instances (lazily initialised)
# ---------------------------------------------------------------------------

_db: Optional[DatabaseManager] = None
_redis: Optional[RedisManager] = None


def get_db_manager() -> DatabaseManager:
    global _db
    if _db is None:
        _db = DatabaseManager()
    return _db


def get_redis_manager() -> RedisManager:
    global _redis
    if _redis is None:
        _redis = RedisManager()
    return _redis


async def get_db() -> AsyncGenerator[DatabaseManager, None]:
    """FastAPI dependency — yields the DatabaseManager."""
    mgr = get_db_manager()
    if mgr._pool is None:
        await mgr.connect()
    yield mgr


async def get_redis() -> AsyncGenerator[RedisManager, None]:
    """FastAPI dependency — yields the RedisManager."""
    mgr = get_redis_manager()
    if mgr._client is None:
        await mgr.connect()
    yield mgr


async def close_all() -> None:
    """Close both PG and Redis connections (call during app shutdown)."""
    global _db, _redis
    if _db is not None:
        await _db.close()
    if _redis is not None:
        await _redis.close()

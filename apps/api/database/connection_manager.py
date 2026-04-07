# ==================== JEBAT AI System - Database Connection Manager ====================
# Version: 1.0.0
# Manages database connections with pooling, error recovery, and health checks
#
# This module provides a robust connection management system for:
# - PostgreSQL (async with connection pooling)
# - Redis (async with connection pooling)
# - Qdrant (async vector database)
# - Health monitoring and automatic recovery
# - Circuit breaker pattern for fault tolerance
# - Connection pooling optimization

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

import asyncpg
import redis.asyncio as redis
from asyncpg import Connection, Pool
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool as RedisPool

# Configure logging
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection state enumeration"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class DatabaseType(Enum):
    """Database type enumeration"""

    POSTGRESQL = "postgresql"
    REDIS = "redis"
    QDRANT = "qdrant"


@dataclass
class ConnectionConfig:
    """Database connection configuration"""

    db_type: DatabaseType
    host: str
    port: int
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    pool_size: int = 10
    max_overflow: int = 10
    pool_timeout: float = 30.0
    command_timeout: float = 60.0
    health_check_interval: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0

    # Redis-specific settings
    redis_db: int = 0
    redis_decode_responses: bool = True

    # PostgreSQL-specific settings
    postgres_min_size: int = 5
    postgres_max_size: int = 20
    postgres_max_queries: int = 50000
    postgres_max_inactive_connection_lifetime: float = 300.0


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""

    failure_count: int = 0
    last_failure_time: float = 0.0
    state: ConnectionState = ConnectionState.CONNECTED
    next_attempt_time: float = 0.0


class DatabaseConnectionManager:
    """
    Advanced database connection manager with pooling, error recovery, and health checks.

    Features:
    - Connection pooling for optimal performance
    - Circuit breaker pattern for fault tolerance
    - Automatic health monitoring
    - Exponential backoff retry logic
    - Connection timeout handling
    - Graceful degradation and recovery
    - Support for PostgreSQL, Redis, and Qdrant
    """

    def __init__(self, config: ConnectionConfig):
        """
        Initialize database connection manager.

        Args:
            config: Database connection configuration
        """
        self.config = config
        self.state = ConnectionState.DISCONNECTED
        self.circuit_breaker = CircuitBreakerState()

        # Connection pools
        self.postgres_pool: Optional[Pool] = None
        self.redis_pool: Optional[RedisPool] = None
        self.qdrant_client: Optional[Any] = None

        # Health monitoring
        self.last_health_check: float = 0.0
        self.health_check_task: Optional[asyncio.Task] = None
        self.is_monitoring: bool = False

        # Statistics
        self.stats = {
            "connection_attempts": 0,
            "successful_connections": 0,
            "failed_connections": 0,
            "reconnections": 0,
            "health_checks": 0,
            "failed_health_checks": 0,
            "circuit_breaker_trips": 0,
            "circuit_breaker_resets": 0,
        }

        # Event callbacks
        self.on_connection_event: Optional[
            Callable[[str, Dict[str, Any]], Awaitable[None]]
        ] = None
        self.on_error: Optional[Callable[[Exception], Awaitable[None]]] = None

        logger.info(
            f"DatabaseConnectionManager initialized for {config.db_type.value} at {config.host}:{config.port}"
        )

    async def connect(self) -> bool:
        """
        Establish database connection with retry logic and circuit breaker.

        Returns:
            bool: True if connection successful, False otherwise
        """
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            logger.warning(f"Circuit breaker is open, skipping connection attempt")
            return False

        self.state = ConnectionState.CONNECTING
        self.stats["connection_attempts"] += 1

        try:
            if self.config.db_type == DatabaseType.POSTGRESQL:
                success = await self._connect_postgres()
            elif self.config.db_type == DatabaseType.REDIS:
                success = await self._connect_redis()
            elif self.config.db_type == DatabaseType.QDRANT:
                success = await self._connect_qdrant()
            else:
                logger.error(f"Unsupported database type: {self.config.db_type}")
                success = False

            if success:
                self.state = ConnectionState.CONNECTED
                self.stats["successful_connections"] += 1
                self.circuit_breaker.failure_count = 0
                self.circuit_breaker.state = ConnectionState.CONNECTED

                # Start health monitoring
                if not self.is_monitoring:
                    self._start_health_monitoring()

                await self._emit_event(
                    "connected", {"db_type": self.config.db_type.value}
                )
                logger.info(
                    f"Successfully connected to {self.config.db_type.value} at {self.config.host}:{self.config.port}"
                )
                return True
            else:
                raise ConnectionError("Connection failed")

        except Exception as e:
            self.state = ConnectionState.ERROR
            self.stats["failed_connections"] += 1
            self._handle_connection_failure(e)
            await self._emit_error(e)
            logger.error(f"Failed to connect to {self.config.db_type.value}: {e}")
            return False

    async def _connect_postgres(self) -> bool:
        """Establish PostgreSQL connection pool."""
        try:
            self.postgres_pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.postgres_min_size,
                max_size=self.config.postgres_max_size,
                max_queries=self.config.postgres_max_queries,
                max_inactive_connection_lifetime=self.config.postgres_max_inactive_connection_lifetime,
                command_timeout=self.config.command_timeout,
                connection_timeout=self.config.pool_timeout,
            )

            # Test connection
            async with self.postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            logger.info(
                f"PostgreSQL pool created with {self.config.postgres_min_size}-{self.config.postgres_max_size} connections"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            self.postgres_pool = None
            return False

    async def _connect_redis(self) -> bool:
        """Establish Redis connection pool."""
        try:
            self.redis_pool = aioredis.ConnectionPool.from_url(
                f"redis://:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.redis_db}",
                max_connections=self.config.pool_size + self.config.max_overflow,
                socket_timeout=self.config.command_timeout,
                socket_connect_timeout=self.config.pool_timeout,
                decode_responses=self.config.redis_decode_responses,
            )

            # Test connection
            redis = Redis(connection_pool=self.redis_pool)
            await redis.ping()
            await redis.close()

            logger.info(
                f"Redis pool created with {self.config.pool_size + self.config.max_overflow} connections"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create Redis pool: {e}")
            self.redis_pool = None
            return False

    async def _connect_qdrant(self) -> bool:
        """Establish Qdrant connection (placeholder - implement based on Qdrant client)."""
        # Placeholder for Qdrant connection
        # In production, you would use the Qdrant client library
        logger.info("Qdrant connection placeholder - implement Qdrant client")
        return True

    @asynccontextmanager
    async def get_postgres_connection(self):
        """
        Get PostgreSQL connection from pool with automatic error recovery.

        Yields:
            Connection: PostgreSQL connection object
        """
        if self.postgres_pool is None:
            raise RuntimeError("PostgreSQL pool not initialized")

        conn = None
        try:
            conn = await self.postgres_pool.acquire()
            yield conn
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e}")
            await self._emit_error(e)
            raise
        finally:
            if conn:
                await self.postgres_pool.release(conn)

    @asynccontextmanager
    async def get_redis_connection(self):
        """
        Get Redis connection from pool with automatic error recovery.

        Yields:
            Redis: Redis connection object
        """
        if self.redis_pool is None:
            raise RuntimeError("Redis pool not initialized")

        redis = None
        try:
            redis = Redis(connection_pool=self.redis_pool)
            yield redis
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            await self._emit_error(e)
            raise
        finally:
            if redis:
                await redis.close()

    async def execute_postgres_query(
        self, query: str, *args, timeout: Optional[float] = None
    ) -> Any:
        """
        Execute PostgreSQL query with automatic retry and circuit breaker.

        Args:
            query: SQL query string
            *args: Query parameters
            timeout: Query timeout (uses default if None)

        Returns:
            Any: Query result

        Raises:
            Exception: If query fails after retries
        """
        if self._is_circuit_breaker_open():
            raise RuntimeError("Circuit breaker is open, query execution blocked")

        query_timeout = timeout or self.config.command_timeout
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                async with self.get_postgres_connection() as conn:
                    result = await conn.fetch(query, *args, timeout=query_timeout)
                    return result

            except Exception as e:
                last_exception = e
                logger.warning(f"Query attempt {attempt + 1} failed: {e}")

                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(
                        self.config.retry_delay * (2**attempt)
                    )  # Exponential backoff

        # All retries failed
        self._handle_connection_failure(last_exception)
        raise last_exception

    async def execute_redis_command(
        self, command: str, *args, timeout: Optional[float] = None
    ) -> Any:
        """
        Execute Redis command with automatic retry and circuit breaker.

        Args:
            command: Redis command
            *args: Command arguments
            timeout: Command timeout (uses default if None)

        Returns:
            Any: Command result

        Raises:
            Exception: If command fails after retries
        """
        if self._is_circuit_breaker_open():
            raise RuntimeError("Circuit breaker is open, command execution blocked")

        command_timeout = timeout or self.config.command_timeout
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                async with self.get_redis_connection() as redis:
                    result = await asyncio.wait_for(
                        redis.execute_command(command, *args), timeout=command_timeout
                    )
                    return result

            except Exception as e:
                last_exception = e
                logger.warning(f"Redis command attempt {attempt + 1} failed: {e}")

                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2**attempt))

        # All retries failed
        self._handle_connection_failure(last_exception)
        raise last_exception

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on database connection.

        Returns:
            Dict[str, Any]: Health check results
        """
        self.stats["health_checks"] += 1
        self.last_health_check = time.time()

        health_result = {
            "db_type": self.config.db_type.value,
            "host": self.config.host,
            "port": self.config.port,
            "state": self.state.value,
            "timestamp": self.last_health_check,
            "is_healthy": False,
            "latency_ms": 0.0,
            "details": {},
        }

        start_time = time.time()

        try:
            if self.config.db_type == DatabaseType.POSTGRESQL and self.postgres_pool:
                async with self.get_postgres_connection() as conn:
                    await conn.fetchval("SELECT 1")
                health_result["is_healthy"] = True
                health_result["details"]["pool_size"] = self.postgres_pool.get_size()
                health_result["details"]["available_connections"] = (
                    self.postgres_pool.get_idle_size()
                )

            elif self.config.db_type == DatabaseType.REDIS and self.redis_pool:
                async with self.get_redis_connection() as redis:
                    await redis.ping()
                health_result["is_healthy"] = True
                health_result["details"]["pool_connections"] = (
                    self.redis_pool.connection_pool.connection_pool_counter.get()
                )

            elif self.config.db_type == DatabaseType.QDRANT:
                # Placeholder for Qdrant health check
                health_result["is_healthy"] = True

            health_result["latency_ms"] = (time.time() - start_time) * 1000

        except Exception as e:
            self.stats["failed_health_checks"] += 1
            health_result["is_healthy"] = False
            health_result["error"] = str(e)
            logger.error(f"Health check failed: {e}")

        return health_result

    async def reconnect(self) -> bool:
        """
        Attempt to reconnect to database with full connection reset.

        Returns:
            bool: True if reconnection successful, False otherwise
        """
        logger.info(f"Attempting to reconnect to {self.config.db_type.value}")
        await self.disconnect()
        await asyncio.sleep(self.config.retry_delay)

        success = await self.connect()

        if success:
            self.stats["reconnections"] += 1
            await self._emit_event(
                "reconnected", {"db_type": self.config.db_type.value}
            )
            logger.info(f"Successfully reconnected to {self.config.db_type.value}")
        else:
            logger.error(f"Failed to reconnect to {self.config.db_type.value}")

        return success

    async def disconnect(self) -> None:
        """Close all database connections and stop monitoring."""
        logger.info(f"Disconnecting from {self.config.db_type.value}")

        # Stop health monitoring
        if self.health_check_task:
            self.health_check_task.cancel()
            self.health_check_task = None
            self.is_monitoring = False

        # Close connection pools
        if self.postgres_pool:
            await self.postgres_pool.close()
            self.postgres_pool = None

        if self.redis_pool:
            await self.redis_pool.disconnect()
            self.redis_pool = None

        # Close Qdrant client
        if self.qdrant_client:
            # Close Qdrant client
            self.qdrant_client = None

        self.state = ConnectionState.DISCONNECTED
        await self._emit_event("disconnected", {"db_type": self.config.db_type.value})
        logger.info(f"Disconnected from {self.config.db_type.value}")

    def _is_circuit_breaker_open(self) -> bool:
        """
        Check if circuit breaker is open.

        Returns:
            bool: True if circuit breaker is open, False otherwise
        """
        if (
            self.circuit_breaker.state == ConnectionState.ERROR
            and time.time() < self.circuit_breaker.next_attempt_time
        ):
            return True
        return False

    def _handle_connection_failure(self, error: Exception) -> None:
        """
        Handle connection failure with circuit breaker logic.

        Args:
            error: Exception that caused the failure
        """
        self.circuit_breaker.failure_count += 1
        self.circuit_breaker.last_failure_time = time.time()

        if self.circuit_breaker.failure_count >= self.config.circuit_breaker_threshold:
            self.circuit_breaker.state = ConnectionState.ERROR
            self.circuit_breaker.next_attempt_time = (
                time.time() + self.config.circuit_breaker_timeout
            )
            self.stats["circuit_breaker_trips"] += 1

            logger.warning(
                f"Circuit breaker opened after {self.circuit_breaker.failure_count} failures. "
                f"Will retry after {self.config.circuit_breaker_timeout} seconds"
            )
            asyncio.create_task(self._reset_circuit_breaker())

    async def _reset_circuit_breaker(self) -> None:
        """Reset circuit breaker after timeout."""
        await asyncio.sleep(self.config.circuit_breaker_timeout)

        if self.circuit_breaker.state == ConnectionState.ERROR:
            self.circuit_breaker.state = ConnectionState.CONNECTING
            self.circuit_breaker.failure_count = 0
            self.stats["circuit_breaker_resets"] += 1

            logger.info("Circuit breaker reset, allowing reconnection attempts")
            await self.reconnect()

    def _start_health_monitoring(self) -> None:
        """Start health monitoring task."""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.health_check_task = asyncio.create_task(self._health_monitor_loop())
            logger.info("Health monitoring started")

    async def _health_monitor_loop(self) -> None:
        """Health monitoring loop."""
        while self.is_monitoring:
            try:
                health = await self.health_check()

                if not health["is_healthy"] and self.state == ConnectionState.CONNECTED:
                    logger.warning(f"Health check failed, attempting reconnection")
                    await self.reconnect()

                await asyncio.sleep(self.config.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(self.config.health_check_interval)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit connection event to registered callback."""
        if self.on_connection_event:
            try:
                await self.on_connection_event(event_type, data)
            except Exception as e:
                logger.error(f"Error emitting event: {e}")

    async def _emit_error(self, error: Exception) -> None:
        """Emit error to registered callback."""
        if self.on_error:
            try:
                await self.on_error(error)
            except Exception as e:
                logger.error(f"Error emitting error: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get connection manager statistics.

        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = self.stats.copy()
        stats["state"] = self.state.value
        stats["circuit_breaker"] = {
            "failure_count": self.circuit_breaker.failure_count,
            "state": self.circuit_breaker.state.value,
            "last_failure_time": self.circuit_breaker.last_failure_time,
            "next_attempt_time": self.circuit_breaker.next_attempt_time,
        }

        if self.postgres_pool:
            stats["postgres_pool"] = {
                "size": self.postgres_pool.get_size(),
                "idle": self.postgres_pool.get_idle_size(),
            }

        if self.redis_pool:
            stats["redis_pool"] = {
                "connections": self.redis_pool.connection_pool.connection_pool_counter.get(),
            }

        return stats

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DatabaseConnectionManager("
            f"db_type={self.config.db_type.value}, "
            f"host={self.config.host}:{self.config.port}, "
            f"state={self.state.value})"
        )


class DatabaseManager:
    """
    High-level database manager that manages multiple database connections.

    Provides a unified interface for managing all database connections in the system.
    """

    def __init__(self):
        """Initialize database manager."""
        self.connections: Dict[str, DatabaseConnectionManager] = {}
        self.logger = logging.getLogger(__name__)

    def add_connection(self, name: str, config: ConnectionConfig) -> None:
        """
        Add a database connection.

        Args:
            name: Connection name
            config: Connection configuration
        """
        if name in self.connections:
            raise ValueError(f"Connection '{name}' already exists")

        self.connections[name] = DatabaseConnectionManager(config)
        self.logger.info(
            f"Added database connection '{name}' for {config.db_type.value}"
        )

    async def connect_all(self) -> Dict[str, bool]:
        """
        Connect to all databases.

        Returns:
            Dict[str, bool]: Connection results
        """
        results = {}

        for name, manager in self.connections.items():
            results[name] = await manager.connect()

        return results

    async def disconnect_all(self) -> None:
        """Disconnect from all databases."""
        for name, manager in self.connections.items():
            await manager.disconnect()

        self.logger.info("Disconnected from all databases")

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on all databases.

        Returns:
            Dict[str, Dict[str, Any]]: Health check results
        """
        results = {}

        for name, manager in self.connections.items():
            results[name] = await manager.health_check()

        return results

    def get_connection(self, name: str) -> DatabaseConnectionManager:
        """
        Get database connection manager by name.

        Args:
            name: Connection name

        Returns:
            DatabaseConnectionManager: Connection manager
        """
        if name not in self.connections:
            raise ValueError(f"Connection '{name}' not found")

        return self.connections[name]

    def get_statistics_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all connections.

        Returns:
            Dict[str, Dict[str, Any]]: Statistics dictionary
        """
        results = {}

        for name, manager in self.connections.items():
            results[name] = manager.get_statistics()

        return results


# ==================== Utility Functions ====================


async def create_connection_manager(
    db_type: DatabaseType,
    host: str,
    port: int,
    database: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs,
) -> DatabaseConnectionManager:
    """
    Create and connect a database connection manager.

    Args:
        db_type: Database type
        host: Database host
        port: Database port
        database: Database name
        username: Database username (for PostgreSQL)
        password: Database password
        **kwargs: Additional configuration options

    Returns:
        DatabaseConnectionManager: Connected database manager
    """
    config = ConnectionConfig(
        db_type=db_type,
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        **kwargs,
    )

    manager = DatabaseConnectionManager(config)
    await manager.connect()

    return manager


# ==================== Example Usage ====================


async def example_usage():
    """Example usage of database connection manager."""
    # Create connection manager
    config = ConnectionConfig(
        db_type=DatabaseType.POSTGRESQL,
        host="localhost",
        port=5432,
        database="jebat_db",
        username="jebat",
        password="jebat_secure_password",
        pool_size=10,
        max_overflow=10,
    )

    manager = DatabaseConnectionManager(config)

    # Use context manager
    async with manager:
        # Execute query with automatic retry
        result = await manager.execute_postgres_query(
            "SELECT * FROM users WHERE username = $1", "admin"
        )
        print(f"Query result: {result}")

        # Health check
        health = await manager.health_check()
        print(f"Health check: {health}")

        # Statistics
        stats = manager.get_statistics()
        print(f"Statistics: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())

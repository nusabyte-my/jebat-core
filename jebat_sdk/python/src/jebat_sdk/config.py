"""JEBAT SDK — Configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class RetryConfig:
    """Retry configuration for HTTP requests."""

    max_attempts: int = 3
    backoff: Literal["fixed", "exponential", "jitter"] = "exponential"
    initial_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    retryable_statuses: set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})

    def get_delay(self, attempt: int, status_code: int | None = None) -> float:
        """Calculate delay for a given attempt."""
        if self.backoff == "fixed":
            return min(self.initial_delay, self.max_delay)
        elif self.backoff == "exponential":
            return min(self.initial_delay * (2 ** (attempt - 1)), self.max_delay)
        else:  # jitter
            import random
            base = min(self.initial_delay * (2 ** (attempt - 1)), self.max_delay)
            return random.uniform(base * 0.5, base * 1.5)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    enabled: bool = True
    failure_threshold: int = 5  # consecutive failures
    success_threshold: int = 2  # consecutive successes to close
    timeout: float = 60.0  # seconds before half-open
    half_open_max_calls: int = 3


class ClientConfig(BaseModel):
    """JEBAT client configuration."""

    base_url: str = "http://localhost:8080"
    api_key: str | None = None
    api_key_env: str = "JEBAT_API_KEY"

    timeout: float = Field(default=30.0, gt=0, le=300)
    connect_timeout: float = Field(default=10.0, gt=0, le=60)

    # Transport
    transport: Literal["http", "websocket", "mcp"] = "http"
    mcp_command: str = "npx @nusabyte/jebat mcp serve"
    mcp_transport: Literal["stdio", "http", "streamable-http"] = "stdio"

    # Retry & Resilience
    retry: RetryConfig = Field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)

    # HTTP/2
    http2: bool = True

    # Headers
    default_headers: dict[str, str] = Field(default_factory=dict)
    user_agent: str = "jebat-sdk-python/1.0.0"

    # Auth
    auth_header: str = "Authorization"
    auth_scheme: str = "Bearer"

    # Streaming
    stream_chunk_size: int = 8192

    # Observability
    enable_tracing: bool = False
    trace_sample_rate: float = Field(default=0.1, ge=0, le=1)

    model_config = {"arbitrary_types_allowed": True}

    def __post_init__(self):
        if self.api_key is None:
            import os
            self.api_key = os.getenv(self.api_key_env)

    @classmethod
    def from_env(cls, **overrides) -> "ClientConfig":
        """Create config from environment variables."""
        import os

        env_defaults = {
            "base_url": os.getenv("JEBAT_BASE_URL", "http://localhost:8080"),
            "api_key": os.getenv("JEBAT_API_KEY"),
            "timeout": float(os.getenv("JEBAT_TIMEOUT", "30")),
            "transport": os.getenv("JEBAT_TRANSPORT", "http"),
        }
        return cls(**{**env_defaults, **overrides})


class WebSocketConfig(BaseModel):
    """WebSocket-specific configuration."""

    url: str
    auto_reconnect: bool = True
    reconnect_interval: float = 5.0
    max_reconnect_interval: float = 60.0
    reconnect_jitter: float = 0.5
    ping_interval: float = 30.0
    ping_timeout: float = 10.0
    max_message_size: int = 16 * 1024 * 1024  # 16MB

    # Message queue during disconnect
    queue_max_size: int = 1000
    queue_on_disconnect: bool = True


class MCPConfig(BaseModel):
    """MCP transport configuration."""

    command: str = "npx @nusabyte/jebat mcp serve"
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    transport: Literal["stdio", "http", "streamable-http"] = "stdio"
    http_port: int = 8099
    http_host: str = "127.0.0.1"
    cwd: str | None = None

    # Connection
    startup_timeout: float = 30.0
    request_timeout: float = 60.0

    # Reconnection
    auto_reconnect: bool = True
    reconnect_interval: float = 5.0
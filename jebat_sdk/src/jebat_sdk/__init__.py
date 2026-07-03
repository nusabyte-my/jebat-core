"""
JEBAT Python SDK

Official Python SDK for JEBAT AI Assistant REST API.
"""

from .client import JebatClient
from .async_client import AsyncJebatClient
from .websocket import JebatWebSocketClient, JebatWebSocketClientSync

from .models import (
    # Auth
    TokenRequest,
    TokenResponse,
    RefreshTokenRequest,
    APIKeyCreateRequest,
    APIKeyResponse,
    UserResponse,
    # Chat
    ChatRequest,
    ChatResponse,
    Message,
    OpenAIMessage,
    OpenAIChatRequest,
    OpenAIChatResponse,
    OpenAIChatChoice,
    SwarmTaskRequest,
    SwarmTaskResponse,
    SwarmPlanResponse,
    StreamChunk,
    # Memories
    MemoryItem,
    MemoryListResponse,
    MemoryCreateRequest,
    MemorySearchRequest,
    # Agents
    AgentInfo,
    AgentListResponse,
    AgentExecuteRequest,
    AgentExecuteResponse,
    # Channels
    ChannelInfo,
    ChannelConfig,
    ChannelStatus,
    ChannelListResponse,
    # Monitoring
    HealthResponse,
    StatusResponse,
    MetricsResponse,
    MonitoringSnapshot,
    ComponentMetrics,
    TimeSeriesData,
    # WebSocket
    ConnectionState,
    JebatWebSocketClient,
    JebatWebSocketClientSync,
)

from .exceptions import (
    JebatError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    TimeoutError,
    ConnectionError,
)

from .retry import (
    standard_retry,
    quick_retry,
    aggressive_retry,
    rate_limit_retry,
    get_retry_decorator,
)

__version__ = "0.1.0"

__all__ = [
    # Clients
    "JebatClient",
    "AsyncJebatClient",
    "JebatWebSocketClient",
    "JebatWebSocketClientSync",
    # Auth
    "TokenRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "APIKeyCreateRequest",
    "APIKeyResponse",
    "UserResponse",
    # Chat
    "ChatRequest",
    "ChatResponse",
    "Message",
    "OpenAIMessage",
    "OpenAIChatRequest",
    "OpenAIChatResponse",
    "OpenAIChatChoice",
    "SwarmTaskRequest",
    "SwarmTaskResponse",
    "SwarmPlanResponse",
    "StreamChunk",
    # Memories
    "MemoryItem",
    "MemoryListResponse",
    "MemoryCreateRequest",
    "MemorySearchRequest",
    # Agents
    "AgentInfo",
    "AgentListResponse",
    "AgentExecuteRequest",
    "AgentExecuteResponse",
    # Channels
    "ChannelInfo",
    "ChannelConfig",
    "ChannelStatus",
    "ChannelListResponse",
    # Monitoring
    "HealthResponse",
    "StatusResponse",
    "MetricsResponse",
    "MonitoringSnapshot",
    "ComponentMetrics",
    "TimeSeriesData",
    # WebSocket
    "ConnectionState",
    "JebatWebSocketClient",
    "JebatWebSocketClientSync",
    # Exceptions
    "JebatError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "TimeoutError",
    "ConnectionError",
    # Retry
    "standard_retry",
    "quick_retry",
    "aggressive_retry",
    "rate_limit_retry",
    "get_retry_decorator",
]
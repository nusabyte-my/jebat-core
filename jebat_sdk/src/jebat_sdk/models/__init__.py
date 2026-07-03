"""
Models package for JEBAT SDK.
"""

from .common import (
    ErrorDetail,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
    TimestampMixin,
    DateTimeRange,
)

from .auth import (
    TokenRequest,
    TokenResponse,
    RefreshTokenRequest,
    APIKeyCreateRequest,
    APIKeyResponse,
    UserResponse,
)

from .chat import (
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
)

from .memories import (
    MemoryItem,
    MemoryListResponse,
    MemoryCreateRequest,
    MemorySearchRequest,
)

from .agents import (
    AgentInfo,
    AgentListResponse,
    AgentExecuteRequest,
    AgentExecuteResponse,
)

from .channels import (
    ChannelInfo,
    ChannelConfig,
    ChannelStatus,
    ChannelListResponse,
)

from .monitoring import (
    HealthResponse,
    StatusResponse,
    MetricsResponse,
    MonitoringSnapshot,
    ComponentMetrics,
    TimeSeriesData,
)

from ..websocket import (
    StreamChunk,
    ConnectionState,
    JebatWebSocketClient,
    JebatWebSocketClientSync,
)

__all__ = [
    # Common
    "ErrorDetail",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    "TimestampMixin",
    "DateTimeRange",
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
    "StreamChunk",
]
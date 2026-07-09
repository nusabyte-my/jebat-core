/**
 * Models package for JEBAT TypeScript SDK.
 * Exports all TypeScript interfaces and Zod schemas.
 */

// Types (from src/types.ts)
export type {
  // Common
  ErrorDetail,
  ErrorResponse,
  PaginationParams,
  PaginatedResponse,
  TimestampMixin,
  DateTimeRange,
  ErrorCode,
  ThinkingMode,
  MemoryLayer,
  SwarmExecutionMode,
  AgentStatus,
  ChannelStatus,
  ConnectionState,
  StreamChunkType,
  HttpMethod,
} from '../types';

// Zod-inferred types (re-exported with explicit export type)
export type {
  // Auth
  TokenRequest,
  TokenResponse,
  RefreshTokenRequest,
  APIKeyCreateRequest,
  APIKeyResponse,
  UserResponse,
  // Chat
  ChatRequest,
  ChatResponse,
  Message,
  OpenAIMessage,
  OpenAIChatRequest,
  OpenAIChatResponse,
  OpenAIChatChoice,
  // Memories
  MemoryItem,
  MemoryListResponse,
  MemoryCreateRequest,
  MemorySearchRequest,
  // Agents
  AgentInfo,
  AgentListResponse,
  AgentExecuteRequest,
  AgentExecuteResponse,
  // Channels
  ChannelInfo,
  ChannelConfig,
  ChannelListResponse,
  // Monitoring
  HealthResponse,
  StatusResponse,
  MetricsResponse,
  // Swarm
  SwarmTaskRequest,
  SwarmTaskResponse,
  SwarmPlanResponse,
} from '../schemas';

// RetryConfig (from src/retry.ts)
export type { RetryConfig } from '../retry';
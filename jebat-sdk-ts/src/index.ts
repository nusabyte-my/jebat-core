/**
 * JEBAT TypeScript SDK
 *
 * Official TypeScript SDK for JEBAT AI Assistant REST API.
 *
 * @packageDocumentation
 */

// Core clients
export { JebatClient } from './client';
export { AsyncJebatClient } from './async-client';
export { HttpClient } from './http-client';

// WebSocket client and StreamChunk (type)
export { JebatWebSocketClient } from './websocket';
export type { StreamChunk } from './websocket';

// Types - re-export with explicit export type
export type {
  ClientOptions,
  HttpMethod,
  PaginationParams,
  PaginatedResponse,
  ErrorDetail,
  ErrorResponse,
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
} from './types';

// RetryConfig from types (re-exported via retry.ts)
export type { RetryConfig } from './retry';

// Models - re-export with explicit export type
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
} from './models';

// Zod schemas (for runtime validation)
export * from './schemas';

// Exceptions
export {
  JebatError,
  AuthenticationError,
  TokenExpiredError,
  TokenInvalidError,
  PermissionDeniedError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ServerError,
  TimeoutError,
  ConnectionError,
  mapHttpError,
  isRetryableError,
  ErrorCodes,
} from './exceptions';

// Retry utilities
export {
  withRetry,
  retry,
  createRetryableFetch,
  calculateWaitTime,
  sleep,
  DEFAULT_RETRY_CONFIG,
  RetryPresets,
} from './retry';
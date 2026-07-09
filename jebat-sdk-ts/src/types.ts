/**
 * Common types shared across the SDK.
 */

/** HTTP methods. */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

/** Pagination parameters. */
export interface PaginationParams {
  limit?: number;
  offset?: number;
}

/** Paginated response wrapper. */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/** Error detail from API. */
export interface ErrorDetail {
  field?: string;
  message: string;
  code?: string;
}

/** Standard error response. */
export interface ErrorResponse {
  detail: string;
  errors?: ErrorDetail[];
  status_code?: number;
}

/** Timestamp mixin. */
export interface TimestampMixin {
  created_at: string;
  updated_at?: string;
}

/** Date time range filter. */
export interface DateTimeRange {
  start?: string;
  end?: string;
}

/** API error codes. */
export enum ErrorCode {
  AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED',
  TOKEN_EXPIRED = 'TOKEN_EXPIRED',
  TOKEN_INVALID = 'TOKEN_INVALID',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  NOT_FOUND = 'NOT_FOUND',
  VALIDATION_FAILED = 'VALIDATION_FAILED',
  RATE_LIMITED = 'RATE_LIMITED',
  SERVER_ERROR = 'SERVER_ERROR',
  CONNECTION_FAILED = 'CONNECTION_FAILED',
  TIMEOUT = 'TIMEOUT',
}

/** Thinking modes for chat. */
export type ThinkingMode =
  | 'fast'
  | 'deliberate'
  | 'deep'
  | 'strategic'
  | 'creative'
  | 'critical';

/** Memory layers. */
export type MemoryLayer =
  | 'M0_IMMEDIATE'
  | 'M1_EPISODIC'
  | 'M2_SEMANTIC'
  | 'M3_PROCEDURAL'
  | 'M4_STRATEGIC';

/** Swarm execution modes. */
export type SwarmExecutionMode = 'single' | 'swarm' | 'consensus';

/** Agent statuses. */
export type AgentStatus = 'idle' | 'active' | 'busy' | 'error';

/** Channel statuses. */
export type ChannelStatus = 'connected' | 'disconnected' | 'connecting' | 'error';

/** WebSocket connection states. */
export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'closed';

/** Stream chunk types. */
export type StreamChunkType = 'content' | 'thinking' | 'complete' | 'error';

/** Base client options. */
export interface ClientOptions {
  baseUrl: string;
  timeout?: number;
  headers?: Record<string, string>;
  maxRetries?: number;
}

/** Retry configuration. */
export interface RetryConfig {
  maxAttempts?: number;
  minWait?: number;
  maxWait?: number;
  multiplier?: number;
}
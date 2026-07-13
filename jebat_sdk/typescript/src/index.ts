/**
 * JEBAT SDK — TypeScript
 * 
 * @packageDocumentation
 */

// Clients
export { JebatClient, createJebatClient } from './core/client.js';
export { AsyncJebatClient, createAsyncJebatClient } from './core/async-client.js';

// Config
export { ClientConfig, RetryConfig, CircuitBreakerConfig } from './core/config.js';

// Errors
export {
  JebatError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  NotFoundError,
  ServerError,
  TimeoutError,
  ConnectionError,
  WebSocketError,
  MCPError,
  CircuitBreakerOpenError,
  createError,
  isJebatError,
  isRetryableError,
} from './errors/index.js';

// Models - Enums
export {
  ThinkingMode,
  MemoryLayer,
  AgentStatus,
  ScanProfile,
  ScanStatus,
  SandboxLanguage,
  MCPTransport,
  SSOProvider,
} from './models/enums.js';

// Models - Core
export type {
  ChatMessage,
  ChatCompleteRequest,
  ChatCompleteResponse,
  ChatStreamChunk,
  ToolCall,
  ToolDefinition,
} from './models/core.js';

// Models - Memory
export type {
  MemoryQueryRequest,
  MemoryQueryResponse,
  MemoryAddRequest,
  MemoryAddResponse,
} from './models/memory.js';

// Models - Agents
export type {
  AgentCreateRequest,
  AgentCreateResponse,
  AgentRunRequest,
  AgentRunResponse,
} from './models/agents.js';

// Models - Tools
export type {
  ToolCallRequest,
  ToolCallResponse,
  ToolListResponse,
} from './models/tools.js';

// Models - Sentinel
export type {
  ScanRequest,
  ScanResponse,
  CVEResult,
  ScanReport,
} from './models/sentinel.js';

// Models - DevSuite
export type {
  GenerateRequest,
  GenerateResponse,
  ReviewRequest,
  ReviewResponse,
  SandboxRunRequest,
  SandboxRunResponse,
  IDEConfigRequest,
  IDEConfigResponse,
} from './models/devsuite.js';

// Models - Companion
export type {
  CompanionChatRequest,
  CompanionChatResponse,
  BriefingRequest,
  BriefingResponse,
  MeetingSummarizeRequest,
  MeetingSummarizeResponse,
  TaskListRequest,
  TaskListResponse,
} from './models/companion.js';

// Models - Nexus
export type {
  BotCreateRequest,
  BotCreateResponse,
  BroadcastRequest,
  BroadcastResponse,
  ChannelListResponse,
} from './models/nexus.js';

// Models - MCP
export type {
  MCPToolCallRequest,
  MCPToolCallResponse,
  MCPToolListResponse,
  MCPResourceListResponse,
  MCPPromptGetRequest,
  MCPPromptGetResponse,
} from './models/mcp.js';

// Models - Admin
export type {
  HealthResponse,
  APIKeyCreateRequest,
  APIKeyCreateResponse,
  APIKeyListResponse,
} from './models/admin.js';

// Models - RBAC
export type {
  OrgCreateRequest,
  OrgCreateResponse,
  TeamCreateRequest,
  TeamCreateResponse,
  ProjectCreateRequest,
  ProjectCreateResponse,
  RoleAssignRequest,
  AuditLogEntry,
  ServiceAccountCreateRequest,
  ServiceAccountCreateResponse,
  ServiceAccountKeyCreateRequest,
  ServiceAccountKeyCreateResponse,
} from './models/rbac.js';

// Models - SSO
export type {
  SSOConfigRequest,
  SSOTestResponse,
} from './models/sso.js';

// Models - WebSocket
export type {
  WSEvent,
  AgentStatusEvent,
  ChannelEvent,
  MetricEvent,
} from './models/websocket.js';

// Models - Pagination
export type {
  PaginationParams,
  PaginatedResponse,
} from './models/pagination.js';

// Models - Webhooks
export type {
  WebhookConfig,
  WebhookDelivery,
} from './models/webhooks.js';

// Testing
export { createMockClient, mockChatResponse } from './testing/index.js';

// React Hooks
export { JebatProvider, useChat, useAgent, useMemory, useSentinel, useTools } from './hooks/index.js';
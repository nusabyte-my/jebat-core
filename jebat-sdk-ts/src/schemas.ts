/**
 * Zod schemas for runtime validation.
 * These mirror the TypeScript interfaces but provide runtime type checking.
 */

import { z } from 'zod';

// Common schemas
export const ErrorDetailSchema = z.object({
  field: z.string().optional(),
  message: z.string(),
  code: z.string().optional(),
});

export const ErrorResponseSchema = z.object({
  detail: z.string(),
  errors: z.array(ErrorDetailSchema).optional(),
  status_code: z.number().optional(),
});

export const PaginationParamsSchema = z.object({
  limit: z.number().int().positive().max(100).default(20),
  offset: z.number().int().nonnegative().default(0),
});

export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    total: z.number().int().nonnegative(),
    limit: z.number().int().positive(),
    offset: z.number().int().nonnegative(),
    has_more: z.boolean(),
  });

// Auth schemas
export const TokenRequestSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
});

export const TokenResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string().default('bearer'),
  expires_in: z.number().int().positive(),
});

export const RefreshTokenRequestSchema = z.object({
  refresh_token: z.string(),
});

export const APIKeyCreateRequestSchema = z.object({
  name: z.string().min(1),
  expires_in_days: z.number().int().positive().optional(),
});

export const APIKeyResponseSchema = z.object({
  id: z.string(),
  name: z.string(),
  prefix: z.string(),
  key: z.string().optional(),
  is_active: z.boolean(),
  last_used: z.string().datetime().optional(),
  expires_at: z.string().datetime().optional(),
  created_at: z.string().datetime(),
});

export const UserResponseSchema = z.object({
  id: z.string(),
  username: z.string(),
  email: z.string().email(),
  full_name: z.string().optional(),
  role: z.string(),
  is_active: z.boolean(),
  created_at: z.string().datetime(),
});

// Chat schemas
export const ChatRequestSchema = z.object({
  message: z.string().min(1),
  user_id: z.string().optional(),
  mode: z.enum(['fast', 'deliberate', 'deep', 'strategic', 'creative', 'critical']).default('deliberate'),
  timeout: z.number().int().positive().max(300).default(30),
  stream: z.boolean().default(false),
});

export const ChatResponseSchema = z.object({
  response: z.string(),
  confidence: z.number().min(0).max(1),
  thinking_steps: z.number().int().nonnegative(),
  execution_time: z.number(),
  user_id: z.string().optional(),
  swarm_lead: z.record(z.unknown()).optional(),
  reducer: z.record(z.unknown()).optional(),
  doctrine: z.record(z.unknown()).optional(),
  security_layer: z.record(z.unknown()).optional(),
});

export const MessageSchema = z.object({
  id: z.string(),
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string(),
  timestamp: z.string().datetime(),
  is_streaming: z.boolean().default(false),
  confidence: z.number().min(0).max(1).optional(),
  thinking_steps: z.number().int().nonnegative().optional(),
});

export const OpenAIMessageSchema = z.object({
  role: z.string(),
  content: z.string(),
});

export const OpenAIChatRequestSchema = z.object({
  model: z.string().default('jebat-pro'),
  messages: z.array(OpenAIMessageSchema),
  stream: z.boolean().default(false),
  temperature: z.number().min(0).max(2).default(0.7),
  max_tokens: z.number().int().positive().optional(),
});

export const OpenAIChatChoiceSchema = z.object({
  index: z.number().int().nonnegative(),
  message: OpenAIMessageSchema,
  finish_reason: z.string().optional(),
});

export const OpenAIChatResponseSchema = z.object({
  id: z.string(),
  object: z.string().default('chat.completion'),
  created: z.number().int().positive(),
  model: z.string(),
  choices: z.array(OpenAIChatChoiceSchema),
  usage: z.record(z.number().int()),
});

// Memory schemas
export const MemoryItemSchema = z.object({
  id: z.string(),
  content: z.string(),
  layer: z.enum(['M0_IMMEDIATE', 'M1_EPISODIC', 'M2_SEMANTIC', 'M3_PROCEDURAL', 'M4_STRATEGIC']),
  user_id: z.string(),
  created_at: z.string().datetime(),
  heat_score: z.number().min(0).max(1),
  metadata: z.record(z.unknown()).optional(),
});

export const MemoryListResponseSchema = PaginatedResponseSchema(MemoryItemSchema);

export const MemoryCreateRequestSchema = z.object({
  content: z.string().min(1),
  user_id: z.string(),
  layer: z.enum(['M0_IMMEDIATE', 'M1_EPISODIC', 'M2_SEMANTIC', 'M3_PROCEDURAL', 'M4_STRATEGIC']).default('M1_EPISODIC'),
  metadata: z.record(z.unknown()).optional(),
});

export const MemorySearchRequestSchema = z.object({
  query: z.string().min(1),
  user_id: z.string().optional(),
  layer: z.enum(['M0_IMMEDIATE', 'M1_EPISODIC', 'M2_SEMANTIC', 'M3_PROCEDURAL', 'M4_STRATEGIC']).optional(),
  limit: z.number().int().positive().max(100).default(20),
  offset: z.number().int().nonnegative().default(0),
});

// Agent schemas
export const AgentInfoSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.string(),
  status: z.enum(['idle', 'active', 'busy', 'error']),
  capabilities: z.array(z.string()).default([]),
  description: z.string().optional(),
});

export const AgentListResponseSchema = z.object({
  agents: z.array(AgentInfoSchema),
  total: z.number().int().nonnegative(),
  active: z.number().int().nonnegative(),
  idle: z.number().int().nonnegative(),
});

export const AgentExecuteRequestSchema = z.object({
  task: z.string().min(1),
  agent_id: z.string().optional(),
  mode: z.enum(['fast', 'deliberate', 'deep', 'strategic', 'creative', 'critical']).default('deliberate'),
  timeout: z.number().int().positive().max(300).default(30),
});

export const AgentExecuteResponseSchema = z.object({
  task_id: z.string(),
  success: z.boolean(),
  result: z.string().optional(),
  error: z.string().optional(),
  execution_time: z.number(),
  agent_id: z.string(),
});

// Channel schemas
export const ChannelInfoSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  status: z.enum(['connected', 'disconnected', 'connecting', 'error']),
  config: z.record(z.unknown()).default({}),
});

export const ChannelConfigSchema = z.object({
  bot_token: z.string().optional(),
  phone_number_id: z.string().optional(),
  access_token: z.string().optional(),
  verify_token: z.string().optional(),
});

export const ChannelStatusSchema = z.object({
  channel_id: z.string(),
  status: z.enum(['connected', 'disconnected', 'connecting', 'error']),
  message: z.string().optional(),
});

export const ChannelListResponseSchema = z.object({
  channels: z.array(ChannelInfoSchema),
  total: z.number().int().nonnegative(),
  connected: z.number().int().nonnegative(),
  disconnected: z.number().int().nonnegative(),
});

// Monitoring schemas
export const HealthResponseSchema = z.object({
  healthy: z.boolean(),
  database: z.boolean(),
  redis: z.boolean(),
  timestamp: z.string().datetime(),
});

export const StatusResponseSchema = z.object({
  status: z.string(),
  version: z.string(),
  timestamp: z.string().datetime(),
  components: z.record(z.string()),
});

export const MetricsResponseSchema = z.object({
  ultra_loop: z.record(z.unknown()).default({}),
  ultra_think: z.record(z.unknown()).default({}),
  memory: z.record(z.unknown()).default({}),
  orchestrator: z.record(z.unknown()).default({}),
  timestamp: z.string().datetime(),
});

// Swarm schemas
export const SwarmTaskRequestSchema = z.object({
  description: z.string().min(1),
  user_id: z.string().optional().default('default'),
  execution_mode: z.enum(['single', 'swarm', 'consensus']).default('consensus'),
  required_capabilities: z.array(z.string()).default([]),
  enable_search: z.boolean().default(true),
  search_queries: z.array(z.string()).default([]),
  max_agents: z.number().int().positive().max(8).default(5),
  parameters: z.record(z.unknown()).default({}),
});

export const SwarmTaskResponseSchema = z.object({
  task_id: z.string(),
  success: z.boolean(),
  execution_mode: z.string(),
  execution_time: z.number(),
  result: z.unknown().optional(),
  error: z.string().optional(),
  swarm_lead: z.record(z.unknown()).optional(),
  reducer: z.record(z.unknown()).optional(),
  doctrine: z.record(z.unknown()).optional(),
  security_layer: z.record(z.unknown()).optional(),
  full_orchestration: z.boolean().default(false),
  stats: z.record(z.unknown()).default({}),
});

export const SwarmPlanResponseSchema = z.object({
  task_id: z.string(),
  execution_mode: z.string(),
  required_capabilities: z.array(z.string()).default([]),
  preferred_roles: z.array(z.string()).default([]),
  recommended_delivery_mode: z.string(),
  search_enabled: z.boolean(),
  require_consensus: z.boolean(),
  full_orchestration: z.boolean(),
  security_layer: z.record(z.unknown()).default({}),
  swarm_lead: z.record(z.unknown()).optional(),
  ranked_agents: z.array(z.record(z.unknown())).default([]),
  selected_agents: z.array(z.record(z.unknown())).default([]),
});

// Type exports (inferred from schemas)
export type ErrorDetail = z.infer<typeof ErrorDetailSchema>;
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
export type PaginationParams = z.infer<typeof PaginationParamsSchema>;
export type PaginatedResponse<T> = z.infer<ReturnType<typeof PaginatedResponseSchema<z.ZodTypeAny>>>;

export type TokenRequest = z.infer<typeof TokenRequestSchema>;
export type TokenResponse = z.infer<typeof TokenResponseSchema>;
export type RefreshTokenRequest = z.infer<typeof RefreshTokenRequestSchema>;
export type APIKeyCreateRequest = z.infer<typeof APIKeyCreateRequestSchema>;
export type APIKeyResponse = z.infer<typeof APIKeyResponseSchema>;
export type UserResponse = z.infer<typeof UserResponseSchema>;

export type ChatRequest = z.infer<typeof ChatRequestSchema>;
export type ChatResponse = z.infer<typeof ChatResponseSchema>;
export type Message = z.infer<typeof MessageSchema>;
export type OpenAIMessage = z.infer<typeof OpenAIMessageSchema>;
export type OpenAIChatRequest = z.infer<typeof OpenAIChatRequestSchema>;
export type OpenAIChatResponse = z.infer<typeof OpenAIChatResponseSchema>;
export type OpenAIChatChoice = z.infer<typeof OpenAIChatChoiceSchema>;

export type MemoryItem = z.infer<typeof MemoryItemSchema>;
export type MemoryListResponse = z.infer<typeof MemoryListResponseSchema>;
export type MemoryCreateRequest = z.infer<typeof MemoryCreateRequestSchema>;
export type MemorySearchRequest = z.infer<typeof MemorySearchRequestSchema>;

export type AgentInfo = z.infer<typeof AgentInfoSchema>;
export type AgentListResponse = z.infer<typeof AgentListResponseSchema>;
export type AgentExecuteRequest = z.infer<typeof AgentExecuteRequestSchema>;
export type AgentExecuteResponse = z.infer<typeof AgentExecuteResponseSchema>;

export type ChannelInfo = z.infer<typeof ChannelInfoSchema>;
export type ChannelConfig = z.infer<typeof ChannelConfigSchema>;
export type ChannelStatus = z.infer<typeof ChannelStatusSchema>;
export type ChannelListResponse = z.infer<typeof ChannelListResponseSchema>;

export type HealthResponse = z.infer<typeof HealthResponseSchema>;
export type StatusResponse = z.infer<typeof StatusResponseSchema>;
export type MetricsResponse = z.infer<typeof MetricsResponseSchema>;

export type SwarmTaskRequest = z.infer<typeof SwarmTaskRequestSchema>;
export type SwarmTaskResponse = z.infer<typeof SwarmTaskResponseSchema>;
export type SwarmPlanResponse = z.infer<typeof SwarmPlanResponseSchema>;
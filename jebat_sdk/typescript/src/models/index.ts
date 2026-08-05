/**
 * JEBAT SDK — TypeScript Types & Zod Schemas
 */

import { z } from 'zod';

// ─── Enums ────────────────────────────────────────────────────────────

export const ThinkingModeSchema = z.enum([
  'fast', 'deliberate', 'deep', 'strategic', 'creative', 'critical', 'custom'
]);
export type ThinkingMode = z.infer<typeof ThinkingModeSchema>;

export const MemoryLayerSchema = z.enum(['M0', 'M1', 'M2', 'M3', 'M4']);
export type MemoryLayer = z.infer<typeof MemoryLayerSchema>;

export const AgentStatusSchema = z.enum(['pending', 'running', 'completed', 'failed', 'cancelled']);
export type AgentStatus = z.infer<typeof AgentStatusSchema>;

export const ScanProfileSchema = z.enum(['quick', 'standard', 'full', 'vulnerability']);
export type ScanProfile = z.infer<typeof ScanProfileSchema>;

export const ScanStatusSchema = z.enum(['queued', 'running', 'completed', 'failed', 'cancelled']);
export type ScanStatus = z.infer<typeof ScanStatusSchema>;

export const SandboxLanguageSchema = z.enum(['python', 'javascript', 'typescript', 'go', 'rust']);
export type SandboxLanguage = z.infer<typeof SandboxLanguageSchema>;

export const MCPTransportSchema = z.enum(['stdio', 'http', 'streamable-http']);
export type MCPTransport = z.infer<typeof MCPTransportSchema>;

export const SSOProviderSchema = z.enum(['oidc', 'saml', 'ldap']);
export type SSOProvider = z.infer<typeof SSOProviderSchema>;

// ─── Core Chat ────────────────────────────────────────────────────────

export const ChatMessageSchema = z.object({
  role: z.enum(['system', 'user', 'assistant', 'tool']),
  content: z.string(),
  name: z.string().optional(),
  tool_call_id: z.string().optional(),
  tool_calls: z.array(z.object({
    id: z.string(),
    type: z.string(),
    function: z.object({
      name: z.string(),
      arguments: z.string(),
    })),
  })).optional(),
});
export type ChatMessage = z.infer<typeof ChatMessageSchema>;

export const ChatCompleteRequestSchema = z.object({
  messages: z.array(ChatMessageSchema),
  model: z.string().default('jebat-core-v8.2'),
  mode: ThinkingModeSchema.default('deliberate'),
  temperature: z.number().min(0).max(2).default(0.7),
  max_tokens: z.number().int().min(1).max(128000).default(4096),
  top_p: z.number().min(0).max(1).default(1),
  frequency_penalty: z.number().min(-2).max(2).default(0),
  presence_penalty: z.number().min(-2).max(2).default(0),
  tools: z.array(z.record(z.unknown())).optional(),
  tool_choice: z.union([z.string(), z.record(z.unknown())]).optional().default('auto'),
  stream: z.boolean().default(false),
  metadata: z.record(z.unknown()).optional(),
});
export type ChatCompleteRequest = z.infer<typeof ChatCompleteRequestSchema>;

export const ChatCompleteResponseSchema = z.object({
  id: z.string(),
  object: z.string().default('chat.completion'),
  created: z.number().int(),
  model: z.string(),
  choices: z.array(z.object({
    index: z.number().int(),
    message: z.object({
      role: z.string(),
      content: z.string().nullable(),
      tool_calls: z.array(z.object({
        id: z.string(),
        type: z.string(),
        function: z.object({
          name: z.string(),
          arguments: z.string(),
        }),
      })).optional(),
    }),
    finish_reason: z.string().nullable(),
  })),
  usage: z.object({
    prompt_tokens: z.number().int(),
    completion_tokens: z.number().int(),
    total_tokens: z.number().int(),
  }),
  system_fingerprint: z.string().nullable().optional(),
});
export type ChatCompleteResponse = z.infer<typeof ChatCompleteResponseSchema>;

export const ChatStreamChunkSchema = z.object({
  id: z.string(),
  object: z.string().default('chat.completion.chunk'),
  created: z.number().int(),
  model: z.string(),
  choices: z.array(z.object({
    index: z.number().int(),
    delta: z.object({
      role: z.string().optional(),
      content: z.string().optional(),
      tool_calls: z.array(z.object({
        index: z.number().int(),
        id: z.string(),
        type: z.string(),
        function: z.object({
          name: z.string(),
          arguments: z.string(),
        }),
      })).optional(),
    }),
    finish_reason: z.string().nullable(),
  })),
  system_fingerprint: z.string().nullable().optional(),
});
export type ChatStreamChunk = z.infer<typeof ChatStreamChunkSchema>;

// ─── Memory ───────────────────────────────────────────────────────────

export const MemoryQueryRequestSchema = z.object({
  query: z.string(),
  layer: z.union([MemoryLayerSchema, z.literal('all')]).default('all'),
  limit: z.number().int().min(1).max(100).default(10),
  min_score: z.number().min(0).max(1).default(0.7),
  filters: z.record(z.unknown()).optional(),
  include_metadata: z.boolean().default(true),
});
export type MemoryQueryRequest = z.infer<typeof MemoryQueryRequestSchema>;

export const MemoryQueryResponseSchema = z.object({
  results: z.array(z.object({
    id: z.string(),
    text: z.string(),
    score: z.number(),
    layer: MemoryLayerSchema,
    metadata: z.record(z.unknown()).optional(),
  })),
  total: z.number().int(),
  query_time_ms: z.number(),
});
export type MemoryQueryResponse = z.infer<typeof MemoryQueryResponseSchema>;

export const MemoryAddRequestSchema = z.object({
  content: z.string(),
  layer: MemoryLayerSchema,
  metadata: z.record(z.unknown()).optional(),
  ttl_seconds: z.number().int().positive().optional(),
});
export type MemoryAddRequest = z.infer<typeof MemoryAddRequestSchema>;

export const MemoryAddResponseSchema = z.object({
  id: z.string(),
  layer: MemoryLayerSchema,
  created_at: z.string().datetime(),
});
export type MemoryAddResponse = z.infer<typeof MemoryAddResponseSchema>;

// ─── Agents ───────────────────────────────────────────────────────────

export const AgentCreateRequestSchema = z.object({
  name: z.string(),
  description: z.string(),
  system_prompt: z.string(),
  tools: z.array(z.string()).default([]),
  thinking_mode: ThinkingModeSchema.default('deliberate'),
  memory_layers: z.array(MemoryLayerSchema).default(['M2', 'M3']),
  max_iterations: z.number().int().min(1).max(50).default(10),
  temperature: z.number().min(0).max(2).default(0.7),
});
export type AgentCreateRequest = z.infer<typeof AgentCreateRequestSchema>;

export const AgentCreateResponseSchema = z.object({
  id: z.string(),
  name: z.string(),
  status: AgentStatusSchema.default('pending'),
  created_at: z.string().datetime(),
});
export type AgentCreateResponse = z.infer<typeof AgentCreateResponseSchema>;

export const AgentRunRequestSchema = z.object({
  input: z.string(),
  context: z.record(z.unknown()).optional(),
  files: z.array(z.string()).optional(),
  stream: z.boolean().default(false),
});
export type AgentRunRequest = z.infer<typeof AgentRunRequestSchema>;

export const AgentRunResponseSchema = z.object({
  run_id: z.string(),
  agent_id: z.string(),
  status: AgentStatusSchema,
  output: z.string().nullable(),
  error: z.string().nullable(),
  steps: z.array(z.record(z.unknown())).nullable().optional(),
  started_at: z.string().datetime(),
  completed_at: z.string().datetime().nullable().optional(),
  usage: z.object({
    prompt_tokens: z.number().int(),
    completion_tokens: z.number().int(),
  }).nullable().optional(),
});
export type AgentRunResponse = z.infer<typeof AgentRunResponseSchema>;

// ─── Tools ────────────────────────────────────────────────────────────

export const ToolDefinitionSchema = z.object({
  name: z.string(),
  description: z.string(),
  parameters: z.record(z.unknown()),
  required: z.array(z.string()).default([]),
});
export type ToolDefinition = z.infer<typeof ToolDefinitionSchema>;

export const ToolCallRequestSchema = z.object({
  name: z.string(),
  arguments: z.record(z.unknown()),
  trace_id: z.string().optional(),
});
export type ToolCallRequest = z.infer<typeof ToolCallRequestSchema>;

export const ToolCallResponseSchema = z.object({
  result: z.unknown(),
  error: z.string().nullable(),
  is_error: z.boolean().default(false),
});
export type ToolCallResponse = z.infer<typeof ToolCallResponseSchema>;

// ─── Sentinel ─────────────────────────────────────────────────────────

export const ScanRequestSchema = z.object({
  target: z.string(),
  profile: ScanProfileSchema.default('standard'),
  config: z.record(z.unknown()).optional(),
  credentials: z.record(z.string()).optional(),
});
export type ScanRequest = z.infer<typeof ScanRequestSchema>;

export const ScanResponseSchema = z.object({
  scan_id: z.string(),
  status: ScanStatusSchema.default('queued'),
  target: z.string(),
  profile: ScanProfileSchema,
  created_at: z.string().datetime(),
});
export type ScanResponse = z.infer<typeof ScanResponseSchema>;

export const CVEResultSchema = z.object({
  cve_id: z.string(),
  severity: z.enum(['critical', 'high', 'medium', 'low', 'none']),
  cvss_score: z.number(),
  description: z.string(),
  affected_versions: z.array(z.string()),
  fixed_versions: z.array(z.string()).nullable().optional(),
  references: z.array(z.string()).default([]),
});
export type CVEResult = z.infer<typeof CVEResultSchema>;

export const ScanReportSchema = z.object({
  scan_id: z.string(),
  target: z.string(),
  status: ScanStatusSchema,
  summary: z.object({
    critical: z.number().int(),
    high: z.number().int(),
    medium: z.number().int(),
    low: z.number().int(),
  }),
  cves: z.array(CVEResultSchema),
  start_time: z.string().datetime(),
  end_time: z.string().datetime().nullable().optional(),
  duration_seconds: z.number().nullable().optional(),
  recommendations: z.array(z.string()).default([]),
});
export type ScanReport = z.infer<typeof ScanReportSchema>;

// ─── DevSuite ─────────────────────────────────────────────────────────

export const GenerateRequestSchema = z.object({
  prompt: z.string(),
  language: z.string().default('python'),
  context: z.record(z.unknown()).optional(),
  files: z.array(z.object({ path: z.string(), content: z.string() })).optional(),
  temperature: z.number().min(0).max(1).default(0.2),
});
export type GenerateRequest = z.infer<typeof GenerateRequestSchema>;

export const GenerateResponseSchema = z.object({
  code: z.string(),
  files: z.record(z.string()).nullable().optional(),
  explanation: z.string().nullable().optional(),
  tests: z.string().nullable().optional(),
  usage: z.record(z.number().int()),
});
export type GenerateResponse = z.infer<typeof GenerateResponseSchema>;

export const ReviewRequestSchema = z.object({
  code: z.string(),
  language: z.string(),
  context: z.record(z.unknown()).optional(),
  focus_areas: z.array(z.string()).optional(),
  diff: z.string().optional(),
});
export type ReviewRequest = z.infer<typeof ReviewRequestSchema>;

export const ReviewResponseSchema = z.object({
  issues: z.array(z.object({
    severity: z.enum(['critical', 'high', 'medium', 'low']),
    line: z.number().int().optional(),
    message: z.string(),
    suggestion: z.string().optional(),
  })),
  suggestions: z.array(z.string()),
  score: z.number().min(0).max(100),
  summary: z.string(),
  fixed_code: z.string().nullable().optional(),
});
export type ReviewResponse = z.infer<typeof ReviewResponseSchema>;

export const SandboxRunRequestSchema = z.object({
  code: z.string(),
  language: SandboxLanguageSchema,
  stdin: z.string().optional(),
  timeout: z.number().int().min(1).max(300).default(30),
  memory_mb: z.number().int().min(64).max(4096).default(512),
  network: z.boolean().default(false),
  dependencies: z.array(z.string()).optional(),
});
export type SandboxRunRequest = z.infer<typeof SandboxRunRequestSchema>;

export const SandboxRunResponseSchema = z.object({
  stdout: z.string(),
  stderr: z.string(),
  exit_code: z.number().int(),
  duration_ms: z.number(),
  memory_peak_mb: z.number(),
  timed_out: z.boolean(),
  error: z.string().nullable().optional(),
});
export type SandboxRunResponse = z.infer<typeof SandboxRunResponseSchema>;

export const IDEConfigRequestSchema = z.object({
  editor: z.enum(['cursor', 'vscode', 'zed', 'windsurf', 'jetbrains']),
  workspace_path: z.string(),
  include_mcp: z.boolean().default(true),
});
export type IDEConfigRequest = z.infer<typeof IDEConfigRequestSchema>;

export const IDEConfigResponseSchema = z.object({
  config: z.record(z.unknown()),
  mcp_servers: z.array(z.record(z.unknown())).nullable().optional(),
  instructions: z.string(),
});
export type IDEConfigResponse = z.infer<typeof IDEConfigResponseSchema>;

// ─── Companion ────────────────────────────────────────────────────────

export const CompanionChatRequestSchema = z.object({
  message: z.string(),
  session_id: z.string().optional(),
  context: z.record(z.unknown()).optional(),
});
export type CompanionChatRequest = z.infer<typeof CompanionChatRequestSchema>;

export const CompanionChatResponseSchema = z.object({
  response: z.string(),
  session_id: z.string(),
  memory_updated: z.boolean().default(false),
  tasks_created: z.array(z.string()).default([]),
});
export type CompanionChatResponse = z.infer<typeof CompanionChatResponseSchema>;

export const BriefingRequestSchema = z.object({
  date: z.string().optional(),
  include_tasks: z.boolean().default(true),
  include_meetings: z.boolean().default(true),
  include_memory: z.boolean().default(true),
  format: z.enum(['markdown', 'html', 'json']).default('markdown'),
});
export type BriefingRequest = z.infer<typeof BriefingRequestSchema>;

export const BriefingResponseSchema = z.object({
  briefing: z.string(),
  date: z.string(),
  tasks: z.array(z.record(z.unknown())).default([]),
  meetings: z.array(z.record(z.unknown())).default([]),
  memory_highlights: z.array(z.string()).default([]),
});
export type BriefingResponse = z.infer<typeof BriefingResponseSchema>;

export const MeetingSummarizeRequestSchema = z.object({
  transcript: z.string(),
  participants: z.array(z.string()).optional(),
  extract_tasks: z.boolean().default(true),
  extract_decisions: z.boolean().default(true),
  format: z.enum(['markdown', 'html', 'json']).default('markdown'),
});
export type MeetingSummarizeRequest = z.infer<typeof MeetingSummarizeRequestSchema>;

export const MeetingSummarizeResponseSchema = z.object({
  summary: z.string(),
  tasks: z.array(z.record(z.unknown())).default([]),
  decisions: z.array(z.string()).default([]),
  action_items: z.array(z.record(z.unknown())).default([]),
  key_points: z.array(z.string()).default([]),
});
export type MeetingSummarizeResponse = z.infer<typeof MeetingSummarizeResponseSchema>;

export const TaskListRequestSchema = z.object({
  session_id: z.string().optional(),
  status: z.enum(['all', 'pending', 'in_progress', 'completed']).default('all'),
  assignee: z.string().optional(),
  limit: z.number().int().min(1).max(200).default(50),
});
export type TaskListRequest = z.infer<typeof TaskListRequestSchema>;

export const TaskListResponseSchema = z.object({
  tasks: z.array(z.record(z.unknown())),
  total: z.number().int(),
});
export type TaskListResponse = z.infer<typeof TaskListResponseSchema>;

// ─── Nexus ────────────────────────────────────────────────────────────

export const BotCreateRequestSchema = z.object({
  name: z.string(),
  description: z.string(),
  platform: z.enum(['telegram', 'discord', 'slack', 'whatsapp', 'signal', 'matrix']),
  platform_config: z.record(z.unknown()),
  webhook_url: z.string().url().optional(),
});
export type BotCreateRequest = z.infer<typeof BotCreateRequestSchema>;

export const BotCreateResponseSchema = z.object({
  bot_id: z.string(),
  name: z.string(),
  platform: z.string(),
  status: z.enum(['active', 'inactive', 'error']),
  webhook_url: z.string().url().nullable().optional(),
});
export type BotCreateResponse = z.infer<typeof BotCreateResponseSchema>;

export const BroadcastRequestSchema = z.object({
  message: z.string(),
  channels: z.array(z.string()).optional(),
  platforms: z.array(z.string()).optional(),
  format: z.enum(['markdown', 'html', 'plain']).default('markdown'),
});
export type BroadcastRequest = z.infer<typeof BroadcastRequestSchema>;

export const BroadcastResponseSchema = z.object({
  sent: z.number().int(),
  failed: z.number().int(),
  errors: z.array(z.object({
    channel: z.string(),
    error: z.string(),
  })).default([]),
});
export type BroadcastResponse = z.infer<typeof BroadcastResponseSchema>;

export const ChannelListResponseSchema = z.object({
  channels: z.array(z.record(z.unknown())),
  total: z.number().int(),
});
export type ChannelListResponse = z.infer<typeof ChannelListResponseSchema>;

// ─── MCP ──────────────────────────────────────────────────────────────

export const MCPToolCallRequestSchema = z.object({
  name: z.string(),
  arguments: z.record(z.unknown()),
  request_id: z.string().optional(),
});
export type MCPToolCallRequest = z.infer<typeof MCPToolCallRequestSchema>;

export const MCPToolCallResponseSchema = z.object({
  result: z.unknown(),
  error: z.string().nullable(),
  is_error: z.boolean().default(false),
});
export type MCPToolCallResponse = z.infer<typeof MCPToolCallResponseSchema>;

export const MCPToolListResponseSchema = z.object({
  tools: z.array(ToolDefinitionSchema),
  total: z.number().int(),
});
export type MCPToolListResponse = z.infer<typeof MCPToolListResponseSchema>;

export const MCPResourceListResponseSchema = z.object({
  resources: z.array(z.record(z.unknown())),
  total: z.number().int(),
});
export type MCPResourceListResponse = z.infer<typeof MCPResourceListResponseSchema>;

// ─── Admin ────────────────────────────────────────────────────────────

export const HealthResponseSchema = z.object({
  status: z.enum(['healthy', 'degraded', 'unhealthy']),
  version: z.string(),
  uptime_seconds: z.number(),
  components: z.record(z.string()),
});
export type HealthResponse = z.infer<typeof HealthResponseSchema>;

export const APIKeyCreateRequestSchema = z.object({
  name: z.string(),
  scopes: z.array(z.string()).default([]),
  expires_in_days: z.number().int().positive().optional(),
  rate_limit: z.number().int().positive().optional(),
});
export type APIKeyCreateRequest = z.infer<typeof APIKeyCreateRequestSchema>;

export const APIKeyCreateResponseSchema = z.object({
  key_id: z.string(),
  name: z.string(),
  key: z.string(),
  scopes: z.array(z.string()),
  expires_at: z.string().datetime().nullable().optional(),
  created_at: z.string().datetime(),
});
export type APIKeyCreateResponse = z.infer<typeof APIKeyCreateResponseSchema>;

export const APIKeyListResponseSchema = z.object({
  keys: z.array(z.record(z.unknown())),
  total: z.number().int(),
});
export type APIKeyListResponse = z.infer<typeof APIKeyListResponseSchema>;

// ─── RBAC ─────────────────────────────────────────────────────────────

export const OrgCreateRequestSchema = z.object({
  name: z.string(),
  slug: z.string(),
  billing_email: z.string().email().optional(),
});
export type OrgCreateRequest = z.infer<typeof OrgCreateRequestSchema>;

export const OrgCreateResponseSchema = z.object({
  org_id: z.string(),
  name: z.string(),
  slug: z.string(),
  owner_id: z.string(),
  created_at: z.string().datetime(),
});
export type OrgCreateResponse = z.infer<typeof OrgCreateResponseSchema>;

export const TeamCreateRequestSchema = z.object({
  name: z.string(),
  slug: z.string(),
  description: z.string().optional(),
});
export type TeamCreateRequest = z.infer<typeof TeamCreateRequestSchema>;

export const TeamCreateResponseSchema = z.object({
  team_id: z.string(),
  name: z.string(),
  org_id: z.string(),
  member_count: z.number().int().default(0),
});
export type TeamCreateResponse = z.infer<typeof TeamCreateResponseSchema>;

export const ProjectCreateRequestSchema = z.object({
  name: z.string(),
  slug: z.string(),
  team_id: z.string().optional(),
  environment: z.enum(['development', 'staging', 'production']).default('development'),
});
export type ProjectCreateRequest = z.infer<typeof ProjectCreateRequestSchema>;

export const ProjectCreateResponseSchema = z.object({
  project_id: z.string(),
  name: z.string(),
  org_id: z.string(),
  team_id: z.string().nullable(),
  environment: z.string(),
});
export type ProjectCreateResponse = z.infer<typeof ProjectCreateResponseSchema>;

export const RoleAssignRequestSchema = z.object({
  user_id: z.string(),
  role: z.string(),
  scope: z.enum(['org', 'team', 'project']),
  scope_id: z.string().nullable().optional(),
  expires_at: z.string().datetime().nullable().optional(),
});
export type RoleAssignRequest = z.infer<typeof RoleAssignRequestSchema>;

export const AuditLogEntrySchema = z.object({
  id: z.string(),
  timestamp: z.string().datetime(),
  actor: z.object({
    type: z.enum(['user', 'service_account', 'system']),
    id: z.string(),
    email: z.string().optional(),
    ip: z.string().optional(),
    user_agent: z.string().optional(),
  }),
  action: z.string(),
  resource: z.object({
    type: z.string(),
    id: z.string(),
    name: z.string().optional(),
  }),
  outcome: z.enum(['success', 'failure', 'partial']),
  severity: z.enum(['info', 'warning', 'critical']),
  metadata: z.record(z.unknown()),
});
export type AuditLogEntry = z.infer<typeof AuditLogEntrySchema>;

export const ServiceAccountCreateRequestSchema = z.object({
  name: z.string(),
  description: z.string().optional(),
  role: z.string().default('role:service'),
  expires_in_days: z.number().int().positive().optional(),
});
export type ServiceAccountCreateRequest = z.infer<typeof ServiceAccountCreateRequestSchema>;

export const ServiceAccountCreateResponseSchema = z.object({
  sa_id: z.string(),
  name: z.string(),
  org_id: z.string(),
  role: z.string(),
  api_key: z.string(),
  expires_at: z.string().datetime().nullable().optional(),
});
export type ServiceAccountCreateResponse = z.infer<typeof ServiceAccountCreateResponseSchema>;

export const ServiceAccountKeyCreateRequestSchema = z.object({
  name: z.string(),
  expires_in_days: z.number().int().positive().optional(),
  ip_allowlist: z.array(z.string()).optional(),
  allowed_paths: z.array(z.string()).optional(),
});
export type ServiceAccountKeyCreateRequest = z.infer<typeof ServiceAccountKeyCreateRequestSchema>;

export const ServiceAccountKeyCreateResponseSchema = z.object({
  key_id: z.string(),
  name: z.string(),
  key: z.string(),
  prefix: z.string(),
  expires_at: z.string().datetime().nullable().optional(),
});
export type ServiceAccountKeyCreateResponse = z.infer<typeof ServiceAccountKeyCreateResponseSchema>;

// ─── SSO ──────────────────────────────────────────────────────────────

export const SSOConfigRequestSchema = z.object({
  provider: z.enum(['oidc', 'saml', 'ldap']),
  config: z.record(z.unknown()),
  auto_provision: z.boolean().default(true),
  default_role: z.string().default('role:viewer'),
  group_mapping: z.record(z.string()).default({}),
});
export type SSOConfigRequest = z.infer<typeof SSOConfigRequestSchema>;

export const SSOTestResponseSchema = z.object({
  success: z.boolean(),
  user_info: z.record(z.unknown()).nullable().optional(),
  error: z.string().nullable().optional(),
});
export type SSOTestResponse = z.infer<typeof SSOTestResponseSchema>;

// ─── WebSocket Events ─────────────────────────────────────────────────

export const WSEventSchema = z.object({
  type: z.string(),
  data: z.record(z.unknown()),
  timestamp: z.string().datetime().default(() => new Date().toISOString()),
});
export type WSEvent = z.infer<typeof WSEventSchema>;

export const AgentStatusEventSchema = WSEventSchema.extend({
  type: z.literal('agent.status'),
});
export type AgentStatusEvent = z.infer<typeof AgentStatusEventSchema>;

export const ChannelEventSchema = WSEventSchema.extend({
  type: z.literal('channel.message'),
});
export type ChannelEvent = z.infer<typeof ChannelEventSchema>;

export const MetricEventSchema = WSEventSchema.extend({
  type: z.literal('metric.update'),
});
export type MetricEvent = z.infer<typeof MetricEventSchema>;

// ─── Pagination ───────────────────────────────────────────────────────

export const PaginationParamsSchema = z.object({
  page: z.number().int().min(1).default(1),
  per_page: z.number().int().min(1).max(100).default(20),
  sort: z.string().optional(),
  order: z.enum(['asc', 'desc']).default('desc'),
});
export type PaginationParams = z.infer<typeof PaginationParamsSchema>;

export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    total: z.number().int(),
    page: z.number().int(),
    per_page: z.number().int(),
    total_pages: z.number().int(),
  });
export type PaginatedResponse<T> = z.infer<ReturnType<typeof PaginatedResponseSchema>>;

// ─── Webhook ──────────────────────────────────────────────────────────

export const WebhookConfigSchema = z.object({
  url: z.string().url(),
  events: z.array(z.string()),
  secret: z.string().optional(),
  active: z.boolean().default(true),
});
export type WebhookConfig = z.infer<typeof WebhookConfigSchema>;

export const WebhookDeliverySchema = z.object({
  id: z.string(),
  event: z.string(),
  payload: z.record(z.unknown()),
  status: z.enum(['pending', 'delivered', 'failed']),
  attempts: z.number().int(),
  created_at: z.string().datetime(),
  delivered_at: z.string().datetime().nullable().optional(),
});
export type WebhookDelivery = z.infer<typeof WebhookDeliverySchema>;
/**
 * JEBAT SDK — Core HTTP Client (Sync)
 */

import { FetchRequest, FetchResponse, RequestInit } from 'undici';
import {
  ClientConfig,
  RetryConfig,
  CircuitBreakerConfig,
  createConfig,
  DEFAULT_CONFIG,
} from './config.js';
import {
  JebatError,
  createError,
  isRetryableError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  NotFoundError,
  ServerError,
  TimeoutError,
  ConnectionError,
  CircuitBreakerOpenError,
} from '../errors/index.js';

interface CircuitBreakerState {
  state: 'closed' | 'open' | 'half-open';
  failureCount: number;
  successCount: number;
  lastFailureTime: number;
}

export class JebatClient {
  private config: ClientConfig;
  private circuitBreaker: CircuitBreakerState;
  private requestCounter = 0;
  private baseHeaders: Record<string, string>;

  constructor(config: Partial<ClientConfig> = {}) {
    this.config = createConfig(config);
    this.circuitBreaker = {
      state: 'closed',
      failureCount: 0,
      successCount: 0,
      lastFailureTime: 0,
    };
    this.baseHeaders = {
      'User-Agent': 'jebat-sdk-typescript/1.0.0',
      'Content-Type': 'application/json',
      ...this.config.defaultHeaders,
    };
    if (this.config.apiKey) {
      this.baseHeaders[this.config.authHeader] = `${this.config.authScheme} ${this.config.apiKey}`;
    }
  }

  private generateRequestId(): string {
    this.requestCounter++;
    return `req_${Date.now()}_${this.requestCounter}`;
  }

  private buildUrl(path: string): string {
    const base = this.config.baseUrl.replace(/\/$/, '');
    const cleanPath = path.replace(/^\//, '');
    return `${base}/${cleanPath}`;
  }

  private checkCircuitBreaker(): void {
    if (!this.config.circuitBreaker.enabled) return;

    if (this.circuitBreaker.state === 'open') {
      if (Date.now() - this.circuitBreaker.lastFailureTime >= this.config.circuitBreaker.timeout) {
        this.circuitBreaker.state = 'half-open';
        this.circuitBreaker.successCount = 0;
      } else {
        throw new CircuitBreakerOpenError('Circuit breaker is open');
      }
    }
  }

  private recordSuccess(): void {
    if (this.circuitBreaker.state === 'half-open') {
      this.circuitBreaker.successCount++;
      if (this.circuitBreaker.successCount >= this.config.circuitBreaker.successThreshold) {
        this.circuitBreaker.state = 'closed';
        this.circuitBreaker.failureCount = 0;
      }
    } else if (this.circuitBreaker.state === 'closed') {
      this.circuitBreaker.failureCount = 0;
    }
  }

  private recordFailure(): void {
    this.circuitBreaker.failureCount++;
    this.circuitBreaker.lastFailureTime = Date.now();

    if (this.circuitBreaker.state === 'half-open') {
      this.circuitBreaker.state = 'open';
    } else if (this.circuitBreaker.failureCount >= this.config.circuitBreaker.failureThreshold) {
      this.circuitBreaker.state = 'open';
    }
  }

  private getRetryDelay(attempt: number, statusCode?: number): number {
    const { backoff, initialDelay, maxDelay } = this.config.retry;
    let delay: number;

    switch (this.config.retry.backoff) {
      case 'fixed':
        delay = initialDelay;
        break;
      case 'exponential':
        delay = initialDelay * Math.pow(2, attempt - 1);
        break;
      case 'jitter':
        delay = initialDelay * Math.pow(2, attempt - 1) * (0.5 + Math.random() * 0.5);
        break;
    }
    return Math.min(delay, maxDelay);
  }

  private buildHeaders(extraHeaders?: Record<string, string>): HeadersInit {
    return {
      ...this.baseHeaders,
      'X-Request-ID': `req_${Date.now()}_${++this.requestCounter}`,
      ...extraHeaders,
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    const requestId = response.headers.get('X-Request-ID');

    if (response.ok) {
      const contentType = response.headers.get('Content-Type') || '';
      if (contentType.includes('application/json')) {
        return response.json();
      }
      return response.text() as Promise<T>;
    }

    let message = `HTTP ${response.status}`;
    let details: Record<string, unknown> = {};

    try {
      const errorData = await response.json();
      message = errorData.message || message;
      details = errorData.details || {};
    } catch {
      const text = await response.text();
      message = `${message}: ${text.slice(0, 200)}`;
    }

    const retryAfter = response.headers.get('Retry-After');
    const retryAfterMs = retryAfter ? parseInt(retryAfter, 10) * 1000 : undefined;

    throw createError(
      response.status,
      message,
      {
        responseBody: await response.text(),
        requestId: requestId || undefined,
        retryAfter: retryAfterMs,
        details,
      }
    );
  }

  private async request<T>(
    method: string,
    path: string,
    options: {
      params?: Record<string, string | number | boolean>;
      body?: unknown;
      headers?: Record<string, string>;
      stream?: boolean;
    } = {}
  ): Promise<T> {
    this.checkCircuitBreaker();

    const url = new URL(this.buildUrl(path));
    if (options.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        url.searchParams.set(key, String(value));
      });
    }

    const headers = this.buildHeaders(options.headers);
    const requestId = headers['X-Request-ID'];

    let attempt = 0;
    let lastError: Error | null = null;

    while (attempt <= this.config.retry.maxAttempts) {
      attempt++;
      try {
        const response = await fetch(url.toString(), {
          method,
          headers,
          body: options.body ? JSON.stringify(options.body) : undefined,
          signal: AbortSignal.timeout(this.config.timeout),
        });

        if (options.stream) {
          this.recordSuccess();
          return response as Promise<T>;
        }

        const result = await this.handleResponse<T>(response);
        this.recordSuccess();
        return result;
      } catch (error) {
        if (error instanceof RateLimitError) {
          this.recordFailure();
          lastError = error;
          if (attempt <= this.config.retry.maxAttempts) {
            const delay = error.retryAfter ?? this.getRetryDelay(attempt, 429);
            await new Promise(resolve => setTimeout(resolve, delay));
            continue;
          }
          throw error;
        }

        if (
          error instanceof ServerError ||
          error instanceof TimeoutError ||
          error instanceof ConnectionError
        ) {
          this.recordFailure();
          lastError = error;
          if (attempt < this.config.retry.maxAttempts && isRetryableError(error)) {
            const delay = this.getRetryDelay(attempt, error.statusCode ?? undefined);
            await new Promise(resolve => setTimeout(resolve, delay));
            continue;
          }
          throw error;
        }

        if (error instanceof JebatError) {
          this.recordFailure();
          throw error;
        }

        this.recordFailure();
        lastError = error instanceof Error ? error : new Error(String(error));
        if (attempt < this.config.retry.maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, this.getRetryDelay(attempt)));
          continue;
        }
        throw lastError;
      }
    }

    throw lastError || new Error('Max retries exceeded');
  }

  // ─── HTTP Methods ────────────────────────────────────────────────

  get<T>(path: string, params?: Record<string, string | number | boolean>): Promise<T> {
    return this.request<T>('GET', path, { params });
  }

  post<T>(path: string, body?: unknown, options?: { headers?: Record<string, string> }): Promise<T> {
    return this.request<T>('POST', path, { body, headers: options?.headers });
  }

  put<T>(path: string, body?: unknown, options?: { headers?: Record<string, string> }): Promise<T> {
    return this.request<T>('PUT', path, { body, headers: options?.headers });
  }

  patch<T>(path: string, body?: unknown, options?: { headers?: Record<string, string> }): Promise<T> {
    return this.request<T>('PATCH', path, { body, headers: options?.headers });
  }

  delete<T>(path: string, params?: Record<string, string | number | boolean>): Promise<T> {
    return this.request<T>('DELETE', path, { params });
  }

  // ─── Streaming ───────────────────────────────────────────────────

  async *stream<T>(path: string, body?: unknown): AsyncGenerator<T> {
    this.checkCircuitBreaker();

    const url = new URL(this.buildUrl(path));
    const headers = this.buildHeaders();

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(this.config.timeout),
    });

    if (!response.ok) {
      await this.handleResponse<void>(response);
    }

    if (!response.body) {
      throw new Error('No response body for streaming');
    }

    this.recordSuccess();

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim()) {
            yield JSON.parse(line) as T;
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  // ─── Resource Methods ────────────────────────────────────────────

  // Chat
  async chat(messages: ChatMessage[], options: {
    model?: string;
    mode?: ThinkingMode;
    temperature?: number;
    maxTokens?: number;
    tools?: ToolDefinition[];
    stream?: boolean;
  } = {}): Promise<ChatCompleteResponse> {
    const request = {
      messages,
      model: options.model || 'jebat-core-v8.2',
      mode: options.mode || 'deliberate',
      temperature: options.temperature ?? 0.7,
      max_tokens: options.maxTokens ?? 4096,
      tools: options.tools,
      stream: options.stream ?? false,
    };
    return this.post<ChatCompleteResponse>('/api/v1/chat', request);
  }

  async *chatStream(messages: ChatMessage[], options: {
    model?: string;
    mode?: ThinkingMode;
    temperature?: number;
    maxTokens?: number;
    tools?: ToolDefinition[];
  } = {}): AsyncGenerator<ChatStreamChunk> {
    const request = {
      messages,
      model: options.model || 'jebat-core-v8.2',
      mode: options.mode || 'deliberate',
      temperature: options.temperature ?? 0.7,
      max_tokens: options.maxTokens ?? 4096,
      tools: options.tools,
      stream: true,
    };

    for await (const chunk of this.stream<ChatStreamChunk>('/api/v1/chat', request)) {
      yield chunk;
    }
  }

  // Thinking Modes
  listThinkingModes(): ThinkingMode[] {
    return Object.values(ThinkingMode);
  }

  // Memory
  async memoryQuery(request: MemoryQueryRequest): Promise<MemoryQueryResponse> {
    return this.post('/api/v1/memory/query', request);
  }

  async memoryAdd(request: MemoryAddRequest): Promise<MemoryAddResponse> {
    return this.post('/api/v1/memory', request);
  }

  // Agents
  async agentCreate(request: AgentCreateRequest): Promise<AgentCreateResponse> {
    return this.post('/api/v1/agents', request);
  }

  async agentRun(agentId: string, request: AgentRunRequest): Promise<AgentRunResponse> {
    return this.post(`/api/v1/agents/${agentId}/run`, request);
  }

  async *agentRunStream(agentId: string, request: AgentRunRequest): AsyncGenerator<AgentRunResponse> {
    for await (const chunk of this.stream<AgentRunResponse>(`/api/v1/agents/${agentId}/run/stream`, request)) {
      yield chunk;
    }
  }

  // Tools
  async toolCall(name: string, arguments_: Record<string, unknown>): Promise<ToolCallResponse> {
    return this.post('/api/v1/tools/call', { name, arguments: arguments_ });
  }

  async toolList(): Promise<ToolDefinition[]> {
    return this.get('/api/v1/tools');
  }

  // Sentinel
  async sentinelScan(request: ScanRequest): Promise<ScanResponse> {
    return this.post('/api/v1/sentinel/scan', request);
  }

  async sentinelGetScan(scanId: string): Promise<ScanResponse> {
    return this.get(`/api/v1/sentinel/scan/${scanId}`);
  }

  async sentinelWait(scanId: string, timeout = 300000, pollInterval = 5000): Promise<ScanReport> {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      const scan = await this.sentinelGetScan(scanId);
      if (['completed', 'failed', 'cancelled'].includes(scan.status)) {
        return this.sentinelGetReport(scanId);
      }
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
    throw new TimeoutError(`Scan ${scanId} timed out`);
  }

  async sentinelGetReport(scanId: string): Promise<ScanReport> {
    return this.get(`/api/v1/sentinel/scan/${scanId}/report`);
  }

  async sentinelListCves(severity?: string, limit = 20): Promise<CVEResult[]> {
    const params: Record<string, string | number> = { limit };
    if (severity) params.severity = severity;
    return this.get('/api/v1/sentinel/cves', params);
  }

  // DevSuite
  async generateCode(request: GenerateRequest): Promise<GenerateResponse> {
    return this.post('/api/v1/dev/generate', request);
  }

  async reviewCode(request: ReviewRequest): Promise<ReviewResponse> {
    return this.post('/api/v1/dev/review', request);
  }

  async sandboxRun(request: SandboxRunRequest): Promise<SandboxRunResponse> {
    return this.post('/api/v1/dev/sandbox', request);
  }

  async getIdeConfig(editor: string, workspacePath: string): Promise<IDEConfigResponse> {
    return this.post('/api/v1/dev/ide-config', { editor, workspace_path: workspacePath });
  }

  // Companion
  async companionChat(request: CompanionChatRequest): Promise<CompanionChatResponse> {
    return this.post('/api/v1/companion/chat', request);
  }

  async companionBriefing(request: BriefingRequest): Promise<BriefingResponse> {
    return this.post('/api/v1/companion/briefing', request);
  }

  async companionMeetingSummarize(request: MeetingSummarizeRequest): Promise<MeetingSummarizeResponse> {
    return this.post('/api/v1/companion/meeting', request);
  }

  async companionTasks(request: TaskListRequest): Promise<TaskListResponse> {
    return this.get('/api/v1/companion/tasks', request);
  }

  // Nexus
  async botCreate(request: BotCreateRequest): Promise<BotCreateResponse> {
    return this.post('/api/v1/nexus/bots', request);
  }

  async botBroadcast(request: BroadcastRequest): Promise<BroadcastResponse> {
    return this.post('/api/v1/nexus/broadcast', request);
  }

  async channelList(): Promise<ChannelListResponse> {
    return this.get('/api/v1/nexus/channels');
  }

  // MCP
  async mcpToolCall(name: string, arguments_: Record<string, unknown>): Promise<MCPToolCallResponse> {
    return this.post('/api/v1/mcp/tools/call', { name, arguments: arguments_ });
  }

  async mcpToolsList(): Promise<MCPToolListResponse> {
    return this.get('/api/v1/mcp/tools');
  }

  // Admin
  async healthCheck(): Promise<HealthResponse> {
    return this.get('/api/v1/admin/health');
  }

  async apiKeyCreate(request: APIKeyCreateRequest): Promise<APIKeyCreateResponse> {
    return this.post('/api/v1/admin/keys', request);
  }

  async apiKeyList(): Promise<APIKeyListResponse> {
    return this.get('/api/v1/admin/keys');
  }

  // RBAC
  async orgCreate(request: OrgCreateRequest): Promise<OrgCreateResponse> {
    return this.post('/api/v1/admin/orgs', request);
  }

  async teamCreate(orgId: string, request: TeamCreateRequest): Promise<TeamCreateResponse> {
    return this.post(`/api/v1/admin/orgs/${orgId}/teams`, request);
  }

  async projectCreate(orgId: string, request: ProjectCreateRequest): Promise<ProjectCreateResponse> {
    return this.post(`/api/v1/admin/orgs/${orgId}/projects`, request);
  }

  async roleAssign(request: RoleAssignRequest): Promise<void> {
    await this.post('/api/v1/admin/roles/assign', request);
  }

  async auditList(orgId: string, limit = 100, filters: Record<string, string | number | boolean> = {}): Promise<AuditLogEntry[]> {
    return this.get(`/api/v1/admin/orgs/${orgId}/audit`, { limit, ...filters });
  }

  async serviceAccountCreate(orgId: string, request: ServiceAccountCreateRequest): Promise<ServiceAccountCreateResponse> {
    return this.post(`/api/v1/admin/orgs/${orgId}/service-accounts`, request);
  }

  async serviceAccountKeyCreate(saId: string, request: ServiceAccountKeyCreateRequest): Promise<ServiceAccountKeyCreateResponse> {
    return this.post(`/api/v1/admin/service-accounts/${saId}/keys`, request);
  }
}

// Factory function
export function createJebatClient(config?: Partial<ClientConfig>): JebatClient {
  return new JebatClient(config);
}
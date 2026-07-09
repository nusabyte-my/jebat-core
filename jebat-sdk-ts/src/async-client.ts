/**
 * Asynchronous JEBAT API client with full streaming support.
 */

import { HttpClient, type RequestOptions } from './http-client';
import { JebatWebSocketClient, type StreamChunk as WSStreamChunk } from './websocket';
import type { ClientOptions, ThinkingMode, MemoryLayer, SwarmExecutionMode } from './types';
import type {
  // Auth
  TokenRequest, TokenResponse, RefreshTokenRequest,
  APIKeyCreateRequest, APIKeyResponse, UserResponse,
  // Chat
  ChatRequest, ChatResponse, Message, OpenAIChatRequest, OpenAIChatResponse,
  // Memories
  MemoryItem, MemoryListResponse, MemoryCreateRequest, MemorySearchRequest,
  // Agents
  AgentInfo, AgentListResponse, AgentExecuteRequest, AgentExecuteResponse,
  // Channels
  ChannelInfo, ChannelConfig, ChannelListResponse,
  // Monitoring
  HealthResponse, StatusResponse, MetricsResponse,
  // Swarm
  SwarmTaskRequest, SwarmTaskResponse, SwarmPlanResponse,
} from './models';

/**
 * Stream chunk for SSE streaming.
 */
export interface StreamChunk {
  type: 'content' | 'thinking' | 'complete' | 'error';
  content: string;
  data?: unknown;
}

/**
 * Async JEBAT API client with full streaming support.
 *
 * @example
 * ```typescript
 * const client = new AsyncJebatClient({ baseUrl: 'http://localhost:8000' });
 * await client.login('username', 'password');
 *
 * // Streaming chat
 * for await (const chunk of client.chatStream('Hello!')) {
 *   process.stdout.write(chunk.content);
 * }
 *
 * // Parallel requests
 * const [health, agents] = await Promise.all([
 *   client.getHealth(),
 *   client.listAgents(),
 * ]);
 * ```
 */
export class AsyncJebatClient {
  private http: HttpClient;
  private wsClient: JebatWebSocketClient | null = null;

  constructor(options: ClientOptions) {
    this.http = new HttpClient(options);
  }

  // ==================== Delegated Properties ====================

  get baseUrl(): string {
    return (this.http as any).baseUrl;
  }

  get token(): string | null {
    return this.http.getToken();
  }

  get refreshToken(): string | null {
    return this.http.getRefreshToken();
  }

  setToken(accessToken: string, refreshToken?: string): void {
    this.http.setToken(accessToken, refreshToken);
  }

  clearTokens(): void {
    this.http.clearTokens();
  }

  isAuthenticated(): boolean {
    return this.http.isAuthenticated();
  }

  // ==================== Context Manager ====================

  async [Symbol.asyncDispose](): Promise<void> {
    await this.close();
  }

  async close(): Promise<void> {
    if (this.wsClient) {
      await this.wsClient.disconnect();
      this.wsClient = null;
    }
  }

  // ==================== Authentication ====================

  /**
   * Authenticate user and get tokens.
   */
  async login(username: string, password: string): Promise<TokenResponse> {
    const response = await this.http.post<TokenResponse>('/api/v1/auth/login', { username, password });
    this.http.setToken(response.access_token, response.refresh_token);
    return response;
  }

  /**
   * Refresh access token.
   */
  async refreshAccessToken(refreshToken?: string): Promise<TokenResponse> {
    const token = refreshToken ?? this.http.getRefreshToken();
    if (!token) {
      throw new Error('No refresh token available');
    }
    const response = await this.http.post<TokenResponse>('/api/v1/auth/refresh', { refresh_token: token });
    this.http.setToken(response.access_token, response.refresh_token);
    return response;
  }

  /**
   * Logout by revoking refresh token.
   */
  async logout(refreshToken?: string): Promise<{ message: string }> {
    const token = refreshToken ?? this.http.getRefreshToken();
    if (token) {
      await this.http.post('/api/v1/auth/logout', { refresh_token: token });
    }
    this.http.clearTokens();
    return { message: 'Logged out' };
  }

  // ==================== API Keys ====================

  async createApiKey(name: string, expiresInDays?: number): Promise<APIKeyResponse> {
    return this.http.post<APIKeyResponse>('/api/v1/auth/api-keys', { name, expires_in_days: expiresInDays });
  }

  async listApiKeys(): Promise<APIKeyResponse[]> {
    return this.http.get<APIKeyResponse[]>('/api/v1/auth/api-keys');
  }

  async revokeApiKey(prefix: string): Promise<{ message: string }> {
    await this.http.delete(`/api/v1/auth/api-keys/${prefix}`);
    return { message: 'API key revoked' };
  }

  // ==================== User Profile ====================

  async getProfile(): Promise<UserResponse> {
    return this.http.get<UserResponse>('/api/v1/auth/me');
  }

  async getUser(userId: string): Promise<UserResponse> {
    return this.http.get<UserResponse>(`/api/v1/auth/users/${userId}`);
  }

  // ==================== Chat ====================

  /**
   * Send a chat message (blocking).
   */
  async chat(
    message: string,
    options: {
      userId?: string;
      mode?: ThinkingMode;
      timeout?: number;
    } = {}
  ): Promise<ChatResponse> {
    return this.http.post<ChatResponse>('/api/v1/chat', {
      message,
      user_id: options.userId,
      mode: options.mode ?? 'deliberate',
      timeout: options.timeout ?? 30,
    });
  }

  /**
   * Stream chat response via Server-Sent Events.
   */
  async *chatStream(
    message: string,
    options: {
      userId?: string;
      mode?: ThinkingMode;
      timeout?: number;
      signal?: AbortSignal;
    } = {}
  ): AsyncGenerator<StreamChunk, void, unknown> {
    const url = new URL('/api/v1/chat', this.baseUrl);
    const payload = {
      message,
      user_id: options.userId,
      mode: options.mode ?? 'deliberate',
      timeout: options.timeout ?? 30,
      stream: true,
    };

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {}),
      },
      body: JSON.stringify(payload),
      signal: options.signal,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

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
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') {
              yield { type: 'complete', content: '' };
              return;
            }
            yield { type: 'content', content: data };
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Stream chat via WebSocket (lower latency, bidirectional).
   */
  async connectWebSocket(): Promise<JebatWebSocketClient> {
    if (this.wsClient?.isConnected) {
      return this.wsClient;
    }

    const wsUrl = this.baseUrl.replace('http', 'ws') + '/ws/chat';
    this.wsClient = new JebatWebSocketClient(wsUrl, this.token!);
    await this.wsClient.connect();
    return this.wsClient;
  }

  /**
   * Stream chat using WebSocket.
   */
  async *chatWebSocket(
    message: string,
    mode: ThinkingMode = 'deliberate'
  ): AsyncGenerator<WSStreamChunk, void, unknown> {
    const ws = await this.connectWebSocket();
    yield* ws.stream({ message, mode });
  }

  // ==================== Memories ====================

  async listMemories(options: {
    userId?: string;
    query?: string;
    layer?: MemoryLayer;
    limit?: number;
    offset?: number;
  } = {}): Promise<MemoryListResponse> {
    const params: Record<string, unknown> = {
      limit: options.limit ?? 20,
      offset: options.offset ?? 0,
    };
    if (options.userId) params['user_id'] = options.userId;
    if (options.query) params['query'] = options.query;
    if (options.layer) params['layer'] = options.layer;

    return this.http.get<MemoryListResponse>('/api/v1/memories', params);
  }

  async createMemory(
    content: string,
    userId: string,
    layer: MemoryLayer = 'M1_EPISODIC',
    metadata?: Record<string, unknown>
  ): Promise<MemoryItem> {
    return this.http.post<MemoryItem>('/api/v1/memories', {
      content,
      user_id: userId,
      layer,
      metadata,
    });
  }

  async searchMemories(options: MemorySearchRequest): Promise<MemoryListResponse> {
    return this.listMemories(options);
  }

  // ==================== Agents ====================

  async listAgents(): Promise<AgentListResponse> {
    return this.http.get<AgentListResponse>('/api/v1/agents');
  }

  async getAgent(agentId: string): Promise<AgentInfo> {
    return this.http.get<AgentInfo>(`/api/v1/agents/${agentId}`);
  }

  async executeAgent(task: string, options: {
    agentId?: string;
    mode?: ThinkingMode;
    timeout?: number;
  } = {}): Promise<AgentExecuteResponse> {
    return this.http.post<AgentExecuteResponse>('/api/v1/agents/execute', {
      task,
      agent_id: options.agentId,
      mode: options.mode ?? 'deliberate',
      timeout: options.timeout ?? 30,
    });
  }

  // ==================== Channels ====================

  async listChannels(): Promise<ChannelInfo[]> {
    return this.http.get<ChannelInfo[]>('/api/v1/channels');
  }

  async getChannel(channelId: string): Promise<ChannelInfo> {
    return this.http.get<ChannelInfo>(`/api/v1/channels/${channelId}`);
  }

  async updateChannelConfig(channelId: string, config: Record<string, unknown>): Promise<ChannelInfo> {
    return this.http.put<ChannelInfo>(`/api/v1/channels/${channelId}`, { config });
  }

  async connectChannel(channelId: string): Promise<{ message: string }> {
    return this.http.post(`/api/v1/channels/${channelId}/connect`);
  }

  async disconnectChannel(channelId: string): Promise<{ message: string }> {
    return this.http.post(`/api/v1/channels/${channelId}/disconnect`);
  }

  // ==================== Monitoring ====================

  async getHealth(): Promise<HealthResponse> {
    return this.http.get<HealthResponse>('/api/v1/health');
  }

  async getStatus(): Promise<StatusResponse> {
    return this.http.get<StatusResponse>('/api/v1/status');
  }

  async getMetrics(): Promise<MetricsResponse> {
    return this.http.get<MetricsResponse>('/api/v1/metrics');
  }

  // ==================== Swarm ====================

  async executeSwarm(
    description: string,
    options: {
      userId?: string;
      executionMode?: SwarmExecutionMode;
      requiredCapabilities?: string[];
      enableSearch?: boolean;
      searchQueries?: string[];
      maxAgents?: number;
    } = {}
  ): Promise<SwarmTaskResponse> {
    return this.http.post<SwarmTaskResponse>('/api/v1/swarm/execute', {
      description,
      user_id: options.userId,
      execution_mode: options.executionMode ?? 'consensus',
      required_capabilities: options.requiredCapabilities,
      enable_search: options.enableSearch ?? true,
      search_queries: options.searchQueries,
      max_agents: options.maxAgents ?? 5,
    });
  }

  async planSwarm(
    description: string,
    options: {
      executionMode?: SwarmExecutionMode;
      requiredCapabilities?: string[];
      maxAgents?: number;
    } = {}
  ): Promise<SwarmPlanResponse> {
    return this.http.post<SwarmPlanResponse>('/api/v1/swarm/plan', {
      description,
      execution_mode: options.executionMode ?? 'consensus',
      required_capabilities: options.requiredCapabilities,
      max_agents: options.maxAgents ?? 5,
    });
  }

  // ==================== Utility ====================

  /**
   * Execute multiple requests in parallel.
   */
  async parallel<T extends Promise<unknown>[]>(
    requests: { [K in keyof T]: () => T[K] }
  ): Promise<{ [K in keyof T]: Awaited<T[K]> }> {
    return Promise.all(requests.map(fn => fn())) as Promise<{ [K in keyof T]: Awaited<T[K]> }>;
  }
}
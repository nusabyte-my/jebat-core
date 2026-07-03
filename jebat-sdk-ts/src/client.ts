/**
 * Main synchronous JEBAT API client.
 * Provides a clean interface to the JEBAT REST API.
 */

import { HttpClient } from './http-client';
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
 * Synchronous JEBAT API client.
 *
 * @example
 * ```typescript
 * const client = new JebatClient({ baseUrl: 'http://localhost:8000' });
 * const tokens = client.login('username', 'password');
 * client.setToken(tokens.access_token, tokens.refresh_token);
 * const response = client.chat('Hello, JEBAT!');
 * console.log(response.response);
 * ```
 */
export class JebatClient {
  private http: HttpClient;

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

  // ==================== Authentication ====================

  /**
   * Authenticate user and get tokens.
   */
  async login(username: string, password: string): Promise<TokenResponse> {
    return this.http.post<TokenResponse>('/api/v1/auth/login', { username, password });
  }

  /**
   * Refresh access token.
   */
  async refreshAccessToken(refreshToken?: string): Promise<TokenResponse> {
    const token = refreshToken ?? this.http.getRefreshToken();
    if (!token) {
      throw new Error('No refresh token available');
    }
    return this.http.post<TokenResponse>('/api/v1/auth/refresh', { refresh_token: token });
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

  /**
   * Create a new API key.
   */
  async createApiKey(name: string, expiresInDays?: number): Promise<APIKeyResponse> {
    return this.http.post<APIKeyResponse>('/api/v1/auth/api-keys', { name, expires_in_days: expiresInDays });
  }

  /**
   * List all API keys for current user.
   */
  async listApiKeys(): Promise<APIKeyResponse[]> {
    return this.http.get<APIKeyResponse[]>('/api/v1/auth/api-keys');
  }

  /**
   * Revoke an API key by prefix.
   */
  async revokeApiKey(prefix: string): Promise<{ message: string }> {
    await this.http.delete(`/api/v1/auth/api-keys/${prefix}`);
    return { message: 'API key revoked' };
  }

  // ==================== User Profile ====================

  /**
   * Get current user profile.
   */
  async getProfile(): Promise<UserResponse> {
    return this.http.get<UserResponse>('/api/v1/auth/me');
  }

  /**
   * Get user by ID (admin only).
   */
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
      stream?: boolean;
    } = {}
  ): Promise<ChatResponse> {
    return this.http.post<ChatResponse>('/api/v1/chat', {
      message,
      user_id: options.userId,
      mode: options.mode ?? 'deliberate',
      timeout: options.timeout ?? 30,
      stream: options.stream ?? false,
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
    } = {}
  ): AsyncGenerator<StreamChunk, void, unknown> {
    // Note: This is a simplified implementation
    // Full streaming requires async iteration
    const response = await this.chat(message, { ...options, stream: false });
    yield { type: 'content', content: response.response };
    yield { type: 'complete', content: '' };
  }

  // ==================== Memories ====================

  /**
   * List memories with optional filtering.
   */
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

  /**
   * Create a new memory.
   */
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

  /**
   * Search memories.
   */
  async searchMemories(options: MemorySearchRequest): Promise<MemoryListResponse> {
    return this.listMemories(options);
  }

  // ==================== Agents ====================

  /**
   * List all agents.
   */
  async listAgents(): Promise<AgentListResponse> {
    return this.http.get<AgentListResponse>('/api/v1/agents');
  }

  /**
   * Get agent by ID.
   */
  async getAgent(agentId: string): Promise<AgentInfo> {
    return this.http.get<AgentInfo>(`/api/v1/agents/${agentId}`);
  }

  /**
   * Execute an agent task.
   */
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

  /**
   * List all channel configurations.
   */
  async listChannels(): Promise<ChannelInfo[]> {
    return this.http.get<ChannelInfo[]>('/api/v1/channels');
  }

  /**
   * Get channel by ID.
   */
  async getChannel(channelId: string): Promise<ChannelInfo> {
    return this.http.get<ChannelInfo>(`/api/v1/channels/${channelId}`);
  }

  /**
   * Update channel configuration.
   */
  async updateChannelConfig(channelId: string, config: Record<string, unknown>): Promise<ChannelInfo> {
    return this.http.put<ChannelInfo>(`/api/v1/channels/${channelId}`, { config });
  }

  /**
   * Connect a channel.
   */
  async connectChannel(channelId: string): Promise<{ message: string }> {
    return this.http.post<{ message: string }>(`/api/v1/channels/${channelId}/connect`);
  }

  /**
   * Disconnect a channel.
   */
  async disconnectChannel(channelId: string): Promise<{ message: string }> {
    return this.http.post<{ message: string }>(`/api/v1/channels/${channelId}/disconnect`);
  }

  // ==================== Monitoring ====================

  /**
   * Get system health.
   */
  async getHealth(): Promise<HealthResponse> {
    return this.http.get<HealthResponse>('/api/v1/health');
  }

  /**
   * Get system status.
   */
  async getStatus(): Promise<StatusResponse> {
    return this.http.get<StatusResponse>('/api/v1/status');
  }

  /**
   * Get system metrics.
   */
  async getMetrics(): Promise<MetricsResponse> {
    return this.http.get<MetricsResponse>('/api/v1/metrics');
  }

  // ==================== Swarm ====================

  /**
   * Execute a task through the swarm orchestrator.
   */
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

  /**
   * Get swarm execution plan without executing.
   */
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
}
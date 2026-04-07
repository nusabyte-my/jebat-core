/**
 * JEBAT JavaScript/TypeScript SDK
 *
 * TypeScript client library for JEBAT AI Assistant REST API.
 *
 * Installation:
 *   npm install @jebat/sdk
 *
 * Usage:
 *   import { JEBATClient } from '@jebat/sdk';
 *
 *   const client = new JEBATClient({ baseURL: 'http://localhost:8000' });
 *
 *   // Chat with JEBAT
 *   const response = await client.chat('What is AI?');
 *   console.log(response.response);
 *
 *   // Store memory
 *   const memory = await client.storeMemory('I prefer TypeScript', { userId: 'user1' });
 *
 *   // Search memories
 *   const memories = await client.searchMemories('TypeScript', { userId: 'user1' });
 */

export interface ChatRequest {
  message: string;
  userId?: string;
  mode?: 'fast' | 'deliberate' | 'deep' | 'strategic' | 'creative' | 'critical';
  timeout?: number;
}

export interface ChatResponse {
  response: string;
  confidence: number;
  thinkingSteps: number;
  executionTime: number;
  userId?: string;
}

export interface Memory {
  id: string;
  content: string;
  layer: string;
  userId: string;
  createdAt: string;
  heatScore: number;
}

export interface MemoryStoreRequest {
  content: string;
  userId: string;
  layer?: string;
}

export interface SystemStatus {
  status: string;
  version: string;
  timestamp: string;
  components: Record<string, string>;
}

export interface Metrics {
  ultraLoop: Record<string, any>;
  ultraThink: Record<string, any>;
  memory: Record<string, any>;
  timestamp: string;
}

export interface JEBATClientConfig {
  baseURL?: string;
  apiKey?: string;
  timeout?: number;
}

export class JEBATClient {
  private baseURL: string;
  private apiKey?: string;
  private timeout: number;
  private headers: HeadersInit;

  constructor(config: JEBATClientConfig = {}) {
    this.baseURL = config.baseURL?.replace(/\/$/, '') || 'http://localhost:8000';
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000;

    this.headers = {
      'Content-Type': 'application/json',
      ...(config.apiKey ? { Authorization: `Bearer ${config.apiKey}` } : {}),
    };
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers: {
          ...this.headers,
          ...options?.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: response.statusText }));
        throw new Error(`API Error: ${error.message || response.status}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Request timeout after ${this.timeout}ms`);
      }
      throw error;
    }
  }

  /**
   * Check API health
   */
  async health(): Promise<{ healthy: boolean; database: boolean; redis: boolean; timestamp: string }> {
    return this.request('/api/v1/health');
  }

  /**
   * Get system status
   */
  async status(): Promise<SystemStatus> {
    return this.request('/api/v1/status');
  }

  /**
   * Get system metrics
   */
  async metrics(): Promise<Metrics> {
    return this.request('/api/v1/metrics');
  }

  /**
   * Chat with JEBAT
   */
  async chat(message: string, options?: Omit<ChatRequest, 'message'>): Promise<ChatResponse> {
    const payload: ChatRequest = {
      message,
      userId: options?.userId,
      mode: options?.mode || 'deliberate',
      timeout: options?.timeout || 30,
    };

    const data = await this.request<ChatResponse>('/api/v1/chat/completions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    // Map snake_case to camelCase
    return {
      ...data,
      thinkingSteps: data.thinking_steps,
      executionTime: data.execution_time,
      userId: data.user_id,
    };
  }

  /**
   * Store a memory
   */
  async storeMemory(content: string, options: { userId: string; layer?: string }): Promise<Memory> {
    const payload: MemoryStoreRequest = {
      content,
      userId: options.userId,
      layer: options.layer || 'M1_EPISODIC',
    };

    const data = await this.request<Memory>('/api/v1/memories', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    // Map snake_case to camelCase
    return {
      ...data,
      heatScore: data.heat_score,
      userId: data.user_id,
      createdAt: data.created_at,
    };
  }

  /**
   * List memories
   */
  async listMemories(options: { userId: string; limit?: number }): Promise<Memory[]> {
    const params = new URLSearchParams({
      user_id: options.userId,
      limit: (options.limit || 10).toString(),
    });

    const data = await this.request<any[]>(`/api/v1/memories?${params}`);

    // Map snake_case to camelCase
    return data.map((m) => ({
      ...m,
      heatScore: m.heat_score,
      userId: m.user_id,
      createdAt: m.created_at,
    }));
  }

  /**
   * Search memories
   */
  async searchMemories(query: string, options: { userId: string; limit?: number }): Promise<Memory[]> {
    const params = new URLSearchParams({
      query,
      user_id: options.userId,
      limit: (options.limit || 10).toString(),
    });

    const data = await this.request<any[]>(`/api/v1/memories?${params}`);

    // Map snake_case to camelCase
    return data.map((m) => ({
      ...m,
      heatScore: m.heat_score,
      userId: m.user_id,
      createdAt: m.created_at,
    }));
  }

  /**
   * List agents
   */
  async listAgents(): Promise<{ agents: any[]; total: number; status: string }> {
    return this.request('/api/v1/agents');
  }
}

/**
 * Create JEBAT client
 */
export function createClient(config?: JEBATClientConfig): JEBATClient {
  return new JEBATClient(config);
}

// Default export
export default JEBATClient;

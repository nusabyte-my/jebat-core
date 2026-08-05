/**
 * JEBAT SDK — Testing Utilities
 */

import { ChatCompleteResponse, ChatStreamChunk, MemoryQueryResponse, ScanResponse, CVEResult, ScanReport, HealthResponse } from '../models/index.js';

export interface MockChatResponseOptions {
  content?: string;
  model?: string;
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
}

export interface MockStreamOptions {
  chunks?: string[];
}

export interface MockMemoryOptions {
  results?: Array<{
    id: string;
    text: string;
    score: number;
    layer: string;
    metadata?: Record<string, unknown>;
  }>;
  queryTimeMs?: number;
}

export interface MockSentinelOptions {
  scanId?: string;
  status?: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  target?: string;
}

export function createMockClient() {
  const mockResponses = new Map<string, unknown[]>();
  const callLog: Array<{ method: string; path: string; body?: unknown; timestamp: number }> = [];

  function addMock(method: string, path: string, response: unknown) {
    const key = `${method}:${path}`;
    if (!mockResponses.has(key)) mockResponses.set(key, []);
    mockResponses.get(key)!.push(response);
  }

  function mockChatComplete(options: MockChatResponseOptions = {}) {
    addMock('POST', '/api/v1/chat', {
      id: `chat_${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: options.model || 'jebat-core-v8.2',
      choices: [{
        index: 0,
        message: { role: 'assistant', content: options.content || 'Hello! How can I help you?' },
        finish_reason: 'stop',
      }],
      usage: options.usage || { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
      system_fingerprint: 'fp_123',
    });
    return mockClient;
  }

  function mockChatStream(options: MockStreamOptions = {}) {
    const chunks = options.chunks || ['Hello', ' ', 'world', '!'];
    const streamData = chunks.map((chunk, i) => ({
      id: `chat_${Date.now()}_${i}`,
      object: 'chat.completion.chunk',
      created: Math.floor(Date.now() / 1000),
      model: 'jebat-core-v8.2',
      choices: [{
        index: 0,
        delta: { content: chunk },
        finish_reason: i === chunks.length - 1 ? 'stop' : null,
      }],
    }));

    const streamText = streamData.map(d => JSON.stringify(d)).join('\n');

    addMock('POST', '/api/v1/chat', {
      // This simulates a streaming response
      _stream: true,
      data: streamData,
    });
    return mockClient;
  }

  function mockMemoryQuery(options: MockMemoryOptions = {}) {
    addMock('POST', '/api/v1/memory/query', {
      results: options.results || [{
        id: 'doc_1',
        text: 'Test document content',
        score: 0.95,
        layer: 'M2',
        metadata: { source: 'test' },
      }],
      total: options.results?.length || 1,
      query_time_ms: options.queryTimeMs || 1.5,
    });
    return mockClient;
  }

  function mockMemoryAdd(docId = 'doc_123') {
    addMock('POST', '/api/v1/memory', {
      id: docId,
      layer: 'M2',
      created_at: new Date().toISOString(),
    });
    return mockClient;
  }

  function mockAgentCreate(agentId = 'agent_123') {
    addMock('POST', '/api/v1/agents', {
      id: agentId,
      name: 'test-agent',
      status: 'pending',
      created_at: new Date().toISOString(),
    });
    return mockClient;
  }

  function mockAgentRun(output = 'Task completed', status = 'completed') {
    addMock('POST', '/api/v1/agents/agent_123/run', {
      run_id: `run_${Date.now()}`,
      agent_id: 'agent_123',
      status,
      output,
      steps: [{ step: 1, action: 'think', result: output }],
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      usage: { prompt_tokens: 100, completion_tokens: 50 },
    });
    return mockClient;
  }

  function mockToolCall(result = 'OK') {
    addMock('POST', '/api/v1/tools/call', { result, error: null, is_error: false });
    return mockClient;
  }

  function mockSentinelScan(scanId = 'scan_123') {
    addMock('POST', '/api/v1/sentinel/scan', {
      scan_id: scanId,
      status: 'queued',
      target: 'example.com',
      profile: 'standard',
      created_at: new Date().toISOString(),
    });
    return mockClient;
  }

  function mockSentinelStatus(scanId = 'scan_123', status = 'completed') {
    addMock('GET', `/api/v1/sentinel/scan/${scanId}`, {
      scan_id: scanId,
      status,
      target: 'example.com',
    });
    return mockClient;
  }

  function mockHealth(status = 'healthy') {
    addMock('GET', '/api/v1/admin/health', {
      status,
      version: '1.0.0',
      uptime_seconds: 3600,
      components: { api: 'healthy', db: 'healthy', mcp: 'healthy' },
    });
    return mockClient;
  }

  const mockClient = {
    // Response registration
    mockChatComplete,
    mockChatStream,
    mockMemoryQuery,
    mockMemoryAdd,
    mockAgentCreate,
    mockAgentRun,
    mockToolCall,
    mockSentinelScan,
    mockSentinelStatus,
    mockHealth,

    // Call log
    callLog: [] as Array<{ method: string; path: string; body?: unknown; timestamp: number }>,

    // HTTP method handlers
    get: async (path: string) => handleRequest('GET', path),
    post: async (path: string, body?: unknown) => handleRequest('POST', path, body),
    put: async (path: string, body?: unknown) => handleRequest('PUT', path, body),
    delete: async (path: string) => handleRequest('DELETE', path),

    // Streaming
    async *stream(path: string) {
      const key = `POST:${path}`;
      const responses = mockResponses.get(key) || [];
      const response = responses.shift();

      if (response && (response as any)._stream) {
        for (const chunk of (response as any).data) {
          yield chunk;
        }
      }
    },

    // Helpers
    getCallLog: () => callLog,
    reset: () => {
      mockResponses.clear();
      callLog.length = 0;
    },

    // Cleanup
    close: () => {},
    async close() {},
  };

  async function handleRequest(method: string, path: string, body?: unknown) {
    callLog.push({ method, path, body, timestamp: Date.now() });

    const key = `${method}:${path}`;
    const responses = mockResponses.get(key);

    if (responses && responses.length > 0) {
      const response = responses.shift()!;
      if ((response as any)._stream) {
        // Return a readable stream for streaming
        return new Response(JSON.stringify((response as any).data), {
          headers: { 'Content-Type': 'application/x-ndjson' },
        });
      }
      return response;
    }

    // Default responses for unmocked endpoints
    return getDefaultResponse(method, path);
  }

  function getDefaultResponse(method: string, path: string) {
    if (path.includes('/health')) {
      return { status: 'healthy', version: '1.0.0', uptime_seconds: 3600 };
    }
    return { mock: true, path, method };
  }

  return mockClient;
}

// Type-safe mock client
export type MockClient = ReturnType<typeof createMockClient>;

// Quick factory functions
export function mockChatResponse(content = 'Hello!', options: { model?: string; usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number } } = {}) {
  const client = createMockClient();
  return client.mockChatComplete({ content, ...options });
}

export function mockStreamResponse(chunks: string[]) {
  const client = createMockClient();
  return client.mockChatStream({ chunks });
}

export function mockMemoryResults(results: Array<{ id: string; text: string; score: number; layer: string; metadata?: Record<string, unknown> }>) {
  const client = createMockClient();
  return client.mockMemoryQuery({ results });
}

export function mockSentinelScan(scanId = 'scan_123') {
  const client = createMockClient();
  return client.mockSentinelScan(scanId);
}

// Test helper: create a fully configured mock
export function createTestClient() {
  const client = createMockClient();
  client.mockHealth();
  client.mockChatComplete();
  client.mockMemoryQuery();
  return client;
}

// Async version
export async function createAsyncTestClient() {
  return createTestClient();
}

// Type-safe mock for use in tests
export function mockJebatClient() {
  return createMockClient();
}

// Pytest-style fixtures (for Vitest/Jest)
export const testFixtures = {
  mockClient: () => createMockClient(),
  mockChat: () => mockChatResponse('Test response'),
  mockStream: () => mockStreamResponse(['Hello', ' ', 'World', '!']),
  mockMemory: () => mockMemoryResults([{ id: 'doc_1', text: 'Test doc', score: 0.9, layer: 'M2', metadata: {} }]),
  mockSentinel: () => mockSentinelScan('scan_123'),
};
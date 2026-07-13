/**
 * JEBAT SDK — Configuration
 */

export interface RetryConfig {
  maxAttempts: number;
  backoff: 'fixed' | 'exponential' | 'jitter';
  initialDelay: number;
  maxDelay: number;
  retryableStatuses: Set<number>;
  shouldRetry?: (error: Error) => boolean;
}

export interface CircuitBreakerConfig {
  enabled: boolean;
  failureThreshold: number;
  successThreshold: number;
  timeout: number;
  halfOpenMaxCalls: number;
}

export interface ClientConfig {
  // Connection
  baseUrl: string;
  apiKey?: string;
  apiKeyEnv?: string;
  timeout: number;
  connectTimeout: number;
  maxConnections: number;
  keepaliveTimeout: number;

  // Transport
  transport: 'http' | 'websocket' | 'mcp';
  mcpCommand: string;
  mcpTransport: 'stdio' | 'http' | 'streamable-http';
  websocketPath: string;

  // Auth
  authHeader: string;
  authScheme: string;

  // Retry
  retry: RetryConfig;

  // Circuit breaker
  circuitBreaker: CircuitBreakerConfig;

  // Defaults
  defaultHeaders: Record<string, string>;
  defaultParams: Record<string, string>;

  // Observability
  enableTracing: boolean;
  tracingSampleRate: number;

  // Callbacks
  onRequest?: (request: Request) => Promise<Request> | Request;
  onResponse?: (response: Response) => Promise<Response> | Response;
  onError?: (error: Error) => Promise<Error> | Error;
}

export const DEFAULT_CONFIG: ClientConfig = {
  baseUrl: 'https://api.jebat.ai',
  apiKeyEnv: 'JEBAT_API_KEY',
  timeout: 30000,
  connectTimeout: 10000,
  maxConnections: 100,
  keepaliveTimeout: 15000,
  transport: 'http',
  mcpCommand: 'npx @nusabyte/jebat mcp serve',
  mcpTransport: 'stdio',
  websocketPath: '/ws',
  authHeader: 'Authorization',
  authScheme: 'Bearer',
  retry: {
    maxAttempts: 3,
    backoff: 'exponential',
    initialDelay: 1000,
    maxDelay: 30000,
    retryableStatuses: new Set([429, 500, 502, 503, 504]),
  },
  circuitBreaker: {
    enabled: true,
    failureThreshold: 5,
    successThreshold: 2,
    timeout: 60000,
    halfOpenMaxCalls: 3,
  },
  defaultHeaders: {},
  defaultParams: {},
  enableTracing: false,
  tracingSampleRate: 0.1,
};

export function createConfig(overrides: Partial<ClientConfig> = {}): ClientConfig {
  return { ...DEFAULT_CONFIG, ...overrides };
}

export function configFromEnv(): ClientConfig {
  return createConfig({
    baseUrl: import.meta.env?.JEBAT_BASE_URL || 'https://api.jebat.ai',
    apiKey: import.meta.env?.JEBAT_API_KEY,
    timeout: parseInt(import.meta.env?.JEBAT_TIMEOUT || '30000', 10),
    transport: (import.meta.env?.JEBAT_TRANSPORT as ClientConfig['transport']) || 'http',
    mcpCommand: import.meta.env?.JEBAT_MCP_COMMAND,
  });
}
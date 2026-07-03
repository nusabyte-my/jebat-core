/**
 * Core HTTP client for JEBAT SDK.
 * Provides low-level request handling with retry logic.
 */

import type { ClientOptions, HttpMethod } from './types';
import { mapHttpError, JebatError, isRetryableError } from './exceptions';
import { retry, DEFAULT_RETRY_CONFIG, calculateWaitTime } from './retry';
import type { RetryConfig } from './retry';

/**
 * Internal request options.
 */
export interface RequestOptions {
  method: HttpMethod;
  path: string;
  body?: unknown;
  query?: Record<string, unknown>;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  retryConfig?: RetryConfig;
}

/**
 * Core HTTP client.
 */
export class HttpClient {
  private baseUrl: string;
  private defaultTimeout: number;
  private defaultHeaders: Record<string, string>;
  private defaultRetryConfig: Required<RetryConfig>;
  private authToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(options: ClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.defaultTimeout = options.timeout ?? 30000;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers,
    };
    this.defaultRetryConfig = { ...DEFAULT_RETRY_CONFIG, ...options.maxRetries ? { maxAttempts: options.maxRetries } : {} };
  }

  /**
   * Set authentication tokens.
   */
  setToken(accessToken: string, refreshToken?: string): void {
    this.authToken = accessToken;
    if (refreshToken) {
      this.refreshToken = refreshToken;
    }
    this.defaultHeaders['Authorization'] = `Bearer ${accessToken}`;
  }

  /**
   * Clear authentication tokens.
   */
  clearTokens(): void {
    this.authToken = null;
    this.refreshToken = null;
    delete this.defaultHeaders['Authorization'];
  }

  /**
   * Get current access token.
   */
  getToken(): string | null {
    return this.authToken;
  }

  /**
   * Get current refresh token.
   */
  getRefreshToken(): string | null {
    return this.refreshToken;
  }

  /**
   * Check if authenticated.
   */
  isAuthenticated(): boolean {
    return this.authToken !== null;
  }

  /**
   * Build full URL with query params.
   */
  private buildUrl(path: string, query?: Record<string, unknown>): string {
    const url = new URL(path, this.baseUrl);
    if (query) {
      Object.entries(query).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.set(key, String(value));
        }
      });
    }
    return url.toString();
  }

  /**
   * Make HTTP request with retry logic.
   */
  async request<T = unknown>(options: RequestOptions): Promise<T> {
    const {
      method,
      path,
      body,
      query,
      headers = {},
      signal,
      retryConfig = {},
    } = options;

    const url = this.buildUrl(path, query);
    const mergedRetryConfig = { ...this.defaultRetryConfig, ...retryConfig };

    const requestHeaders = {
      ...this.defaultHeaders,
      ...headers,
    };

    const makeRequest = async (): Promise<T> => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.defaultTimeout);

      // Handle external signal
      const abortHandler = () => controller.abort();
      signal?.addEventListener('abort', abortHandler);

      try {
        const response = await fetch(url, {
          method,
          headers: requestHeaders,
          body: body !== undefined ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);
        signal?.removeEventListener('abort', abortHandler);

        // Handle rate limiting
        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After');
          const error = mapHttpError(429, 'Rate limit exceeded', {
            detail: 'Rate limit exceeded',
            status_code: 429,
          });
          (error as any).retryAfter = retryAfter ? parseInt(retryAfter, 10) : null;
          throw error;
        }

        // Handle other HTTP errors
        if (!response.ok) {
          let errorData: any = { detail: `HTTP ${response.status}` };
          try {
            errorData = await response.json();
          } catch {
            errorData.detail = await response.text() || `HTTP ${response.status}`;
          }
          throw mapHttpError(response.status, errorData.detail || `HTTP ${response.status}`, errorData);
        }

        // Handle empty responses
        if (response.status === 204) {
          return undefined as T;
        }

        return await response.json() as T;
      } catch (error) {
        clearTimeout(timeoutId);
        signal?.removeEventListener('abort', abortHandler);

        // Re-throw JebatError directly
        if (error instanceof JebatError) {
          throw error;
        }

        // Network/timeout errors
        if (error instanceof DOMException && error.name === 'AbortError') {
          throw new (await import('./exceptions')).TimeoutError('Request timeout');
        }

        if (error instanceof TypeError && error.message.includes('fetch')) {
          throw new (await import('./exceptions')).ConnectionError('Network error');
        }

        throw error;
      }
    };

    // Apply retry logic
    return retry(makeRequest, mergedRetryConfig);
  }

  // Convenience methods
  get<T = unknown>(path: string, query?: Record<string, unknown>, options?: Partial<RequestOptions>): Promise<T> {
    return this.request<T>({ method: 'GET', path, query, ...options });
  }

  post<T = unknown>(path: string, body?: unknown, options?: Partial<RequestOptions>): Promise<T> {
    return this.request<T>({ method: 'POST', path, body, ...options });
  }

  put<T = unknown>(path: string, body?: unknown, options?: Partial<RequestOptions>): Promise<T> {
    return this.request<T>({ method: 'PUT', path, body, ...options });
  }

  patch<T = unknown>(path: string, body?: unknown, options?: Partial<RequestOptions>): Promise<T> {
    return this.request<T>({ method: 'PATCH', path, body, ...options });
  }

  delete<T = unknown>(path: string, options?: Partial<RequestOptions>): Promise<T> {
    return this.request<T>({ method: 'DELETE', path, ...options });
  }
}
/**
 * Retry logic with exponential backoff for JEBAT SDK.
 */

import type { RetryConfig } from './types';
import { isRetryableError, JebatError } from './exceptions';

/**
 * Default retry configuration.
 */
export const DEFAULT_RETRY_CONFIG: Required<RetryConfig> = {
  maxAttempts: 3,
  minWait: 1000,   // 1 second
  maxWait: 10000,  // 10 seconds
  multiplier: 2,
};

/**
 * Calculate wait time with exponential backoff and jitter.
 */
export function calculateWaitTime(
  attempt: number,
  config: Required<RetryConfig>
): number {
  const exponentialWait = config.minWait * Math.pow(config.multiplier, attempt);
  const cappedWait = Math.min(exponentialWait, config.maxWait);
  // Add jitter (±25%)
  const jitter = cappedWait * 0.25 * (Math.random() * 2 - 1);
  return Math.max(config.minWait, Math.round(cappedWait + jitter));
}

/**
 * Sleep utility.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry decorator for async functions.
 */
export function withRetry<T extends (...args: unknown[]) => Promise<unknown>>(
  fn: T,
  config: RetryConfig = {}
): T {
  const mergedConfig = { ...DEFAULT_RETRY_CONFIG, ...config };

  return (async (...args: unknown[]) => {
    let lastError: unknown;

    for (let attempt = 0; attempt < mergedConfig.maxAttempts; attempt++) {
      try {
        return await fn(...args);
      } catch (error) {
        lastError = error;

        // Don't retry on last attempt
        if (attempt === mergedConfig.maxAttempts - 1) {
          break;
        }

        // Check if error is retryable
        if (!isRetryableError(error)) {
          throw error;
        }

        // Special handling for rate limit with retry-after
        if (error instanceof JebatError && 'retryAfter' in error) {
          const rateLimitError = error as { retryAfter: number | null };
          if (rateLimitError.retryAfter) {
            await sleep(rateLimitError.retryAfter * 1000);
            continue;
          }
        }

        // Wait before retry
        const waitTime = calculateWaitTime(attempt, mergedConfig);
        await sleep(waitTime);
      }
    }

    throw lastError;
  }) as T;
}

/**
 * Async retry helper function.
 */
export async function retry<T>(
  fn: () => Promise<T>,
  config: RetryConfig = {}
): Promise<T> {
  const mergedConfig = { ...DEFAULT_RETRY_CONFIG, ...config };
  let lastError: unknown;

  for (let attempt = 0; attempt < mergedConfig.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (attempt === mergedConfig.maxAttempts - 1) {
        break;
      }

      if (!isRetryableError(error)) {
        throw error;
      }

      if (error instanceof JebatError && 'retryAfter' in error) {
        const rateLimitError = error as { retryAfter: number | null };
        if (rateLimitError.retryAfter) {
          await sleep(rateLimitError.retryAfter * 1000);
          continue;
        }
      }

      const waitTime = calculateWaitTime(attempt, mergedConfig);
      await sleep(waitTime);
    }
  }

  throw lastError;
}

/**
 * Create a retryable fetch wrapper.
 */
export function createRetryableFetch(config: RetryConfig = {}) {
  return async (url: string | URL, init?: RequestInit): Promise<Response> => {
    return retry(async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), (init as any)?.signal ? 0 : 30000);

      try {
        const response = await fetch(url, {
          ...init,
          signal: controller.signal,
        });

        // Don't throw on HTTP errors, let caller handle
        return response;
      } finally {
        clearTimeout(timeoutId);
      }
    }, config);
  };
}

/**
 * Pre-configured retry configs for common use cases.
 */
export const RetryPresets = {
  /** Quick retry for transient errors (2 attempts, fast) */
  quick: { maxAttempts: 2, minWait: 500, maxWait: 2000, multiplier: 1 },

  /** Standard retry for API calls (3 attempts, moderate) */
  standard: { maxAttempts: 3, minWait: 1000, maxWait: 10000, multiplier: 2 },

  /** Aggressive retry for critical operations (5 attempts, slow) */
  aggressive: { maxAttempts: 5, minWait: 2000, maxWait: 30000, multiplier: 2 },

  /** Rate limit aware retry (respects retry-after header) */
  rateLimitAware: { maxAttempts: 5, minWait: 1000, maxWait: 60000, multiplier: 2 },
} as const satisfies Record<string, RetryConfig>;

// Re-export RetryConfig from types for convenience
export type { RetryConfig } from './types';
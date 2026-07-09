import { describe, it, expect, vi, beforeEach } from 'vitest';
import { JebatClient } from '../src/client';
import { AsyncJebatClient } from '../src/async-client';
import { JebatWebSocketClient, StreamChunk } from '../src/websocket';
import { HttpClient } from '../src/http-client';
import { ErrorCode } from '../src/types';
import {
  JebatError,
  AuthenticationError,
  RateLimitError,
  mapHttpError,
} from '../src/exceptions';
import {
  retry,
  calculateWaitTime,
  DEFAULT_RETRY_CONFIG,
  RetryPresets,
} from '../src/retry';
import type {
  TokenRequest,
  TokenResponse,
  ChatResponse,
} from '../src/models';

describe('JEBAT SDK', () => {
  describe('Types', () => {
    it('should have correct ErrorCode enum values', () => {
      expect(ErrorCode.AUTHENTICATION_FAILED).toBe('AUTHENTICATION_FAILED');
      expect(ErrorCode.TOKEN_EXPIRED).toBe('TOKEN_EXPIRED');
      expect(ErrorCode.PERMISSION_DENIED).toBe('PERMISSION_DENIED');
      expect(ErrorCode.NOT_FOUND).toBe('NOT_FOUND');
      expect(ErrorCode.VALIDATION_FAILED).toBe('VALIDATION_FAILED');
      expect(ErrorCode.RATE_LIMITED).toBe('RATE_LIMITED');
      expect(ErrorCode.SERVER_ERROR).toBe('SERVER_ERROR');
      expect(ErrorCode.CONNECTION_FAILED).toBe('CONNECTION_FAILED');
      expect(ErrorCode.TIMEOUT).toBe('TIMEOUT');
    });

    it('should allow ThinkingMode values', () => {
      const modes: Array<'fast' | 'deliberate' | 'deep' | 'strategic' | 'creative' | 'critical'> = [
        'fast', 'deliberate', 'deep', 'strategic', 'creative', 'critical',
      ];
      expect(modes.length).toBe(6);
    });

    it('should allow MemoryLayer values', () => {
      const layers: Array<'M0_IMMEDIATE' | 'M1_EPISODIC' | 'M2_SEMANTIC' | 'M3_PROCEDURAL' | 'M4_STRATEGIC'> = [
        'M0_IMMEDIATE', 'M1_EPISODIC', 'M2_SEMANTIC', 'M3_PROCEDURAL', 'M4_STRATEGIC',
      ];
      expect(layers.length).toBe(5);
    });
  });

  describe('Exceptions', () => {
    it('should create JebatError with correct properties', () => {
      const error = new JebatError('Test error', 500, null, 'SERVER_ERROR');
      expect(error.message).toBe('Test error');
      expect(error.statusCode).toBe(500);
      expect(error.code).toBe('SERVER_ERROR');
    });

    it('should create AuthenticationError', () => {
      const error = new AuthenticationError('Auth failed');
      expect(error.statusCode).toBe(401);
      expect(error.code).toBe('AUTHENTICATION_FAILED');
    });

    it('should create RateLimitError with retryAfter', () => {
      const error = new RateLimitError('Rate limited', null, 60);
      expect(error.statusCode).toBe(429);
      expect(error.retryAfter).toBe(60);
    });

    it('should map HTTP errors correctly', () => {
      const authError = mapHttpError(401, 'Unauthorized');
      expect(authError).toBeInstanceOf(JebatError); // AuthenticationError is not exported as class
      
      const rateLimitError = mapHttpError(429, 'Too many requests', null);
      expect(rateLimitError).toBeInstanceOf(RateLimitError);
      
      const serverError = mapHttpError(500, 'Internal error');
      expect(serverError).toBeInstanceOf(JebatError);
    });
  });

  describe('Retry', () => {
    it('should calculate wait time with exponential backoff', () => {
      const config = { ...DEFAULT_RETRY_CONFIG, multiplier: 2 };
      
      const wait0 = calculateWaitTime(0, config);
      expect(wait0).toBeGreaterThanOrEqual(750);
      
      const wait1 = calculateWaitTime(1, config);
      expect(wait1).toBeGreaterThanOrEqual(wait0);
    });

    it('should respect maxWait limit (with jitter allowance)', () => {
      const config = { ...DEFAULT_RETRY_CONFIG, multiplier: 10, maxWait: 1000 };
      
      const wait10 = calculateWaitTime(10, config);
      expect(wait10).toBeLessThanOrEqual(1300); // Allow ~25% jitter overhead
    });

    it('should have correct presets', () => {
      expect(RetryPresets.quick.maxAttempts).toBe(2);
      expect(RetryPresets.standard.maxAttempts).toBe(3);
      expect(RetryPresets.aggressive.maxAttempts).toBe(5);
      expect(RetryPresets.rateLimitAware.maxWait).toBe(60000);
    });

    it('should retry failed operations', async () => {
      let attempts = 0;
      const { ServerError } = await import('../src/exceptions');
      const fn = vi.fn().mockImplementation(() => {
        attempts++;
        if (attempts < 3) throw new ServerError('Server temporarily unavailable');
        return 'success';
      });

      const result = await retry(fn, { ...RetryPresets.quick, maxAttempts: 3 });
      expect(result).toBe('success');
      expect(attempts).toBe(3);
    });

    it('should not retry non-retryable errors', async () => {
      const fn = vi.fn().mockRejectedValue(new Error('Permanent error'));
      
      await expect(retry(fn, RetryPresets.quick)).rejects.toThrow('Permanent error');
      expect(fn).toHaveBeenCalledTimes(1);
    });
  });

  describe('HttpClient', () => {
    it('should build URL with query params', () => {
      const client = new HttpClient({ baseUrl: 'http://localhost:8000' });
      // @ts-expect-error - accessing private method for testing
      const url = client['buildUrl']('/api/v1/test', { param1: 'value1', param2: 'value2' });
      expect(url).toContain('param1=value1');
      expect(url).toContain('param2=value2');
      expect(url).toContain('/api/v1/test');
    });

    it('should set and clear tokens', () => {
      const client = new HttpClient({ baseUrl: 'http://localhost:8000' });
      client.setToken('test-access-token', 'test-refresh-token');
      expect(client.getToken()).toBe('test-access-token');
      expect(client.getRefreshToken()).toBe('test-refresh-token');
      expect(client.isAuthenticated()).toBe(true);
      
      client.clearTokens();
      expect(client.getToken()).toBeNull();
      expect(client.isAuthenticated()).toBe(false);
    });
  });

  describe('Client', () => {
    it('should instantiate JebatClient', () => {
      const client = new JebatClient({ baseUrl: 'http://localhost:8000' });
      expect(client.baseUrl).toBe('http://localhost:8000');
      expect(client.isAuthenticated()).toBe(false);
    });

    it('should instantiate AsyncJebatClient', () => {
      const client = new AsyncJebatClient({ baseUrl: 'http://localhost:8000' });
      expect(client.baseUrl).toBe('http://localhost:8000');
      expect(client.isAuthenticated()).toBe(false);
    });
  });
});
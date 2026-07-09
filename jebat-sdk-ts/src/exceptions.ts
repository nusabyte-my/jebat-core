/**
 * JEBAT SDK Exceptions
 * Custom exception classes for the JEBAT TypeScript SDK.
 */

import { ErrorCode } from './types';
import type { ErrorResponse } from './types';

/**
 * Base exception for all JEBAT SDK errors.
 */
export class JebatError extends Error {
  public readonly statusCode: number;
  public readonly responseData: ErrorResponse | null;
  public readonly code: ErrorCode | 'UNKNOWN';

  constructor(
    message: string,
    statusCode: number = 0,
    responseData: ErrorResponse | null = null,
    code: ErrorCode | 'UNKNOWN' = 'UNKNOWN'
  ) {
    super(message);
    this.name = 'JebatError';
    this.statusCode = statusCode;
    this.responseData = responseData;
    this.code = code;

    // Maintain proper stack trace in V8
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, JebatError);
    }
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      statusCode: this.statusCode,
      code: this.code,
      responseData: this.responseData,
    };
  }
}

/**
 * Raised when authentication fails (401).
 */
export class AuthenticationError extends JebatError {
  constructor(message: string = 'Authentication failed', responseData: ErrorResponse | null = null) {
    super(message, 401, responseData, ErrorCode.AUTHENTICATION_FAILED);
    this.name = 'AuthenticationError';
  }
}

/**
 * Raised when token is expired (401).
 */
export class TokenExpiredError extends JebatError {
  constructor(message: string = 'Token has expired', responseData: ErrorResponse | null = null) {
    super(message, 401, responseData, ErrorCode.TOKEN_EXPIRED);
    this.name = 'TokenExpiredError';
  }
}

/**
 * Raised when token is invalid (401).
 */
export class TokenInvalidError extends JebatError {
  constructor(message: string = 'Token is invalid', responseData: ErrorResponse | null = null) {
    super(message, 401, responseData, ErrorCode.TOKEN_INVALID);
    this.name = 'TokenInvalidError';
  }
}

/**
 * Raised when access is denied (403).
 */
export class PermissionDeniedError extends JebatError {
  constructor(message: string = 'Permission denied', responseData: ErrorResponse | null = null) {
    super(message, 403, responseData, ErrorCode.PERMISSION_DENIED);
    this.name = 'PermissionDeniedError';
  }
}

/**
 * Raised when a resource is not found (404).
 */
export class NotFoundError extends JebatError {
  constructor(message: string = 'Resource not found', responseData: ErrorResponse | null = null) {
    super(message, 404, responseData, ErrorCode.NOT_FOUND);
    this.name = 'NotFoundError';
  }
}

/**
 * Raised when request validation fails (422).
 */
export class ValidationError extends JebatError {
  public readonly errors: ReadonlyArray<{ field?: string; message: string; code?: string }>;

  constructor(
    message: string = 'Validation failed',
    responseData: ErrorResponse | null = null,
    errors: Array<{ field?: string; message: string; code?: string }> = []
  ) {
    super(message, 422, responseData, ErrorCode.VALIDATION_FAILED);
    this.name = 'ValidationError';
    this.errors = errors;
  }
}

/**
 * Raised when rate limit is exceeded (429).
 */
export class RateLimitError extends JebatError {
  public readonly retryAfter: number | null;

  constructor(
    message: string = 'Rate limit exceeded',
    responseData: ErrorResponse | null = null,
    retryAfter: number | null = null
  ) {
    super(message, 429, responseData, ErrorCode.RATE_LIMITED);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

/**
 * Raised when server returns 5xx error.
 */
export class ServerError extends JebatError {
  constructor(message: string = 'Server error', responseData: ErrorResponse | null = null, statusCode: number = 500) {
    super(message, statusCode, responseData, ErrorCode.SERVER_ERROR);
    this.name = 'ServerError';
  }
}

/**
 * Raised when request times out.
 */
export class TimeoutError extends JebatError {
  constructor(message: string = 'Request timeout', responseData: ErrorResponse | null = null) {
    super(message, 408, responseData, ErrorCode.TIMEOUT);
    this.name = 'TimeoutError';
  }
}

/**
 * Raised when connection fails.
 */
export class ConnectionError extends JebatError {
  constructor(message: string = 'Connection failed', responseData: ErrorResponse | null = null) {
    super(message, 0, responseData, ErrorCode.CONNECTION_FAILED);
    this.name = 'ConnectionError';
  }
}

/**
 * Map HTTP status code to appropriate exception.
 */
export function mapHttpError(
  statusCode: number,
  message: string,
  responseData: ErrorResponse | null = null
): JebatError {
  switch (statusCode) {
    case 400:
      return new ValidationError(message, responseData, responseData?.errors ?? []);
    case 401:
      if (responseData?.detail?.includes('expired')) {
        return new TokenExpiredError(message, responseData);
      }
      if (responseData?.detail?.includes('invalid')) {
        return new TokenInvalidError(message, responseData);
      }
      return new AuthenticationError(message, responseData);
    case 403:
      return new PermissionDeniedError(message, responseData);
    case 404:
      return new NotFoundError(message, responseData);
    case 422:
      return new ValidationError(message, responseData, responseData?.errors ?? []);
    case 429:
      const retryAfter = responseData?.detail?.match(/retry.?after.?(\d+)/i)?.[1];
      return new RateLimitError(message, responseData, retryAfter ? parseInt(retryAfter, 10) : null);
    case 408:
      return new TimeoutError(message, responseData);
    case 500:
    case 502:
    case 503:
    case 504:
      return new ServerError(message, responseData, statusCode);
    default:
      if (statusCode >= 500) {
        return new ServerError(message, responseData, statusCode);
      }
      return new JebatError(message, statusCode, responseData);
  }
}

/**
 * Check if an error is retryable.
 */
export function isRetryableError(error: unknown): boolean {
  if (!(error instanceof JebatError)) {
    return error instanceof Error && (
      error.name === 'TypeError' || // Network errors
      error.name === 'AbortError' || // Timeout
      error.message.includes('network') ||
      error.message.includes('timeout') ||
      error.message.includes('connection')
    );
  }

  // Retry on network/connection errors
  if (error instanceof ConnectionError || error instanceof TimeoutError) {
    return true;
  }

  // Retry on server errors (5xx)
  if (error instanceof ServerError) {
    return true;
  }

  // Retry on rate limit with retry-after
  if (error instanceof RateLimitError && error.retryAfter !== null) {
    return true;
  }

  // Don't retry on client errors (4xx except 429)
  return false;
}

/**
 * Error codes enum for easy checking.
 */
export const ErrorCodes = {
  AUTHENTICATION_FAILED: 'AUTHENTICATION_FAILED',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  TOKEN_INVALID: 'TOKEN_INVALID',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_FAILED: 'VALIDATION_FAILED',
  RATE_LIMITED: 'RATE_LIMITED',
  SERVER_ERROR: 'SERVER_ERROR',
  CONNECTION_FAILED: 'CONNECTION_FAILED',
  TIMEOUT: 'TIMEOUT',
} as const;
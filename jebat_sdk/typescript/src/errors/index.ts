/**
 * JEBAT SDK — Error Classes
 */

export class JebatError extends Error {
  public readonly statusCode: number | null;
  public readonly responseBody: string | null;
  public readonly requestId: string | null;
  public readonly retryAfter: number | null;
  public readonly details: Record<string, unknown>;

  constructor(
    message: string,
    options: {
      statusCode?: number;
      responseBody?: string;
      requestId?: string;
      retryAfter?: number;
      details?: Record<string, unknown>;
    } = {}
  ) {
    super(message);
    this.name = 'JebatError';
    this.statusCode = options.statusCode ?? null;
    this.responseBody = options.responseBody ?? null;
    this.requestId = options.requestId ?? null;
    this.retryAfter = options.retryAfter ?? null;
    this.details = options.details ?? {};
  }

  toJSON(): Record<string, unknown> {
    return {
      error: this.name,
      message: this.message,
      statusCode: this.statusCode,
      requestId: this.requestId,
      details: this.details,
    };
  }
}

export class AuthenticationError extends JebatError {
  constructor(message = 'Authentication failed', options: Record<string, unknown> = {}) {
    super(message, { ...options, statusCode: 401 });
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends JebatError {
  constructor(message = 'Rate limit exceeded', options: { retryAfter?: number } & Record<string, unknown> = {}) {
    super(message, { ...options, statusCode: 429, retryAfter: options.retryAfter });
    this.name = 'RateLimitError';
  }
}

export class ValidationError extends JebatError {
  public readonly errors: Record<string, unknown>[];

  constructor(
    message = 'Validation failed',
    options: { errors?: Record<string, unknown>[] } & Record<string, unknown> = {}
  ) {
    super(message, { ...options, statusCode: 400 });
    this.name = 'ValidationError';
    this.errors = options.errors ?? [];
  }
}

export class NotFoundError extends JebatError {
  constructor(message = 'Resource not found', options: Record<string, unknown> = {}) {
    super(message, { ...options, statusCode: 404 });
    this.name = 'NotFoundError';
  }
}

export class ServerError extends JebatError {
  constructor(message = 'Server error', options: { statusCode?: number } & Record<string, unknown> = {}) {
    super(message, { ...options, statusCode: options.statusCode ?? 500 });
    this.name = 'ServerError';
  }
}

export class ConflictError extends JebatError {
  constructor(message = 'Resource already exists', options: Record<string, unknown> = {}) {
    super(message, { ...options, statusCode: 409 });
    this.name = 'ConflictError';
  }
}

export class ForbiddenError extends JebatError {
  constructor(message = 'Insufficient permissions', options: Record<string, unknown> = {}) {
    super(message, { ...options, statusCode: 403 });
    this.name = 'ForbiddenError';
  }
}

export class TimeoutError extends JebatError {
  constructor(message = 'Request timed out', options: Record<string, unknown> = {}) {
    super(message, options);
    this.name = 'TimeoutError';
  }
}

export class ConnectionError extends JebatError {
  constructor(message = 'Connection failed', options: Record<string, unknown> = {}) {
    super(message, options);
    this.name = 'ConnectionError';
  }
}

export class WebSocketError extends JebatError {
  constructor(message = 'WebSocket error', options: Record<string, unknown> = {}) {
    super(message, options);
    this.name = 'WebSocketError';
  }
}

export class MCPError extends JebatError {
  public readonly mcpErrorCode: string | null;

  constructor(message = 'MCP error', options: { mcpErrorCode?: string } & Record<string, unknown> = {}) {
    super(message, options);
    this.name = 'MCPError';
    this.mcpErrorCode = options.mcpErrorCode ?? null;
  }
}

export class CircuitBreakerOpenError extends JebatError {
  constructor(message = 'Circuit breaker open', options: Record<string, unknown> = {}) {
    super(message, options);
    this.name = 'CircuitBreakerOpenError';
  }
}

// Status code to error class mapping
const STATUS_CODE_MAP: Map<number, new (message: string, options?: Record<string, unknown>) => JebatError> = new Map([
  [400, ValidationError],
  [401, AuthenticationError],
  [403, ForbiddenError],
  [404, NotFoundError],
  [409, ConflictError],
  [429, RateLimitError],
  [500, ServerError],
  [502, ServerError],
  [503, ServerError],
  [504, ServerError],
]);

export function createError(
  statusCode: number,
  message: string,
  options: Record<string, unknown> = {}
): JebatError {
  const ErrorClass = STATUS_CODE_MAP.get(statusCode) ?? JebatError;

  if (ErrorClass === RateLimitError) {
    return new ErrorClass(message, { ...options, retryAfter: options.retryAfter });
  }
  if (ErrorClass === ValidationError) {
    return new ErrorClass(message, { ...options, errors: options.errors });
  }
  if (ErrorClass === ServerError) {
    return new ErrorClass(message, { ...options, statusCode });
  }

  return new ErrorClass(message, options);
}

export function isJebatError(error: unknown): error is JebatError {
  return error instanceof JebatError;
}

export function isRetryableError(error: unknown): boolean {
  if (!isJebatError(error)) return false;
  if (error.statusCode !== null && [429, 500, 502, 503, 504].includes(error.statusCode)) return true;
  if (error instanceof TimeoutError || error instanceof ConnectionError) return true;
  return false;
}
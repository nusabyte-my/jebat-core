"""JEBAT SDK — Error classes."""

from __future__ import annotations

from typing import Any


class JebatError(Exception):
    """Base exception for all JEBAT SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: str | None = None,
        request_id: str | None = None,
        retry_after: float | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        self.request_id = request_id
        self.retry_after = retry_after

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"status={self.status_code}")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        return " | ".join(parts)


class AuthenticationError(JebatError):
    """401 Unauthorized — Invalid or expired API key."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class RateLimitError(JebatError):
    """429 Too Many Requests — Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: float | None = None,
        **kwargs
    ):
        super().__init__(message, status_code=429, retry_after=retry_after, **kwargs)


class ValidationError(JebatError):
    """400 Bad Request — Request validation failed."""

    def __init__(
        self,
        message: str = "Validation failed",
        *,
        errors: list[dict[str, Any]] | None = None,
        **kwargs
    ):
        super().__init__(message, status_code=400, **kwargs)
        self.errors = errors or []


class NotFoundError(JebatError):
    """404 Not Found — Resource not found."""

    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(message, status_code=404, **kwargs)


class ServerError(JebatError):
    """5xx Server Error — Internal server error."""

    def __init__(self, message: str = "Server error", **kwargs):
        super().__init__(message, status_code=kwargs.get("status_code", 500), **kwargs)


class ConflictError(JebatError):
    """409 Conflict — Resource already exists."""

    def __init__(self, message: str = "Resource already exists", **kwargs):
        super().__init__(message, status_code=409, **kwargs)


class ForbiddenError(JebatError):
    """403 Forbidden — Insufficient permissions."""

    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(message, status_code=403, **kwargs)


class TimeoutError(JebatError):
    """Request timeout."""

    def __init__(self, message: str = "Request timed out", **kwargs):
        super().__init__(message, **kwargs)


class ConnectionError(JebatError):
    """Network connection error."""

    def __init__(self, message: str = "Connection failed", **kwargs):
        super().__init__(message, **kwargs)


class WebSocketError(JebatError):
    """WebSocket connection error."""

    def __init__(self, message: str = "WebSocket error", **kwargs):
        super().__init__(message, **kwargs)


class MCPError(JebatError):
    """MCP protocol error."""

    def __init__(self, message: str = "MCP error", *, mcp_error_code: str | None = None, **kwargs):
        super().__init__(message, **kwargs)
        self.mcp_error_code = mcp_error_code


class CircuitBreakerOpenError(JebatError):
    """Circuit breaker is open, requests blocked."""

    def __init__(self, message: str = "Circuit breaker open", **kwargs):
        super().__init__(message, **kwargs)


# ─── Error mapping ──────────────────────────────────────────────────

_STATUS_CODE_MAP: dict[int, type[JebatError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: ForbiddenError,
    404: NotFoundError,
    409: ConflictError,
    429: RateLimitError,
    500: ServerError,
    502: ServerError,
    503: ServerError,
    504: ServerError,
}


def create_error(
    status_code: int,
    message: str,
    **kwargs
) -> JebatError:
    """Create appropriate error from HTTP status code."""
    error_class = _STATUS_CODE_MAP.get(status_code, JebatError)
    return error_class(message, status_code=status_code, **kwargs)


def is_jebat_error(exc: BaseException) -> bool:
    """Check if exception is a JEBAT SDK error."""
    return isinstance(exc, JebatError)


def is_retryable_error(exc: BaseException) -> bool:
    """Check if error is retryable."""
    if not isinstance(exc, JebatError):
        return False
    if exc.status_code in {429, 500, 502, 503, 504}:
        return True
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    return False
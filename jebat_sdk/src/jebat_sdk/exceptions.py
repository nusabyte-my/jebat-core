"""
JEBAT SDK Exceptions

Custom exception classes for the JEBAT SDK.
"""

from typing import Any, Dict, Optional


class JebatError(Exception):
    """Base exception for all JEBAT SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self) -> str:
        return f"{self.message} (status: {self.status_code})"


class AuthenticationError(JebatError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = 401,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, response_data)


class PermissionDeniedError(JebatError):
    """Raised when access is denied."""

    def __init__(
        self,
        message: str = "Permission denied",
        status_code: int = 403,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, response_data)


class NotFoundError(JebatError):
    """Raised when a resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        status_code: int = 404,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, response_data)


class RateLimitError(JebatError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: int = 429,
        response_data: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message, status_code, response_data)
        self.retry_after = retry_after


class ValidationError(JebatError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        status_code: int = 422,
        response_data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, response_data)
        self.errors = errors


class ServerError(JebatError):
    """Raised when server returns 5xx error."""

    def __init__(
        self,
        message: str = "Server error",
        status_code: int = 500,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, response_data)


class TimeoutError(JebatError):
    """Raised when request times out."""

    def __init__(
        self,
        message: str = "Request timeout",
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=408, response_data=response_data)


class ConnectionError(JebatError):
    """Raised when connection fails."""

    def __init__(
        self,
        message: str = "Connection failed",
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=0, response_data=response_data)


def map_http_error(
    status_code: int,
    message: str,
    response_data: Optional[Dict[str, Any]] = None,
) -> JebatError:
    """Map HTTP status code to appropriate exception."""
    if status_code == 400:
        return ValidationError(message, status_code, response_data)
    elif status_code == 401:
        return AuthenticationError(message, status_code, response_data)
    elif status_code == 403:
        return PermissionDeniedError(message, status_code, response_data)
    elif status_code == 404:
        return NotFoundError(message, status_code, response_data)
    elif status_code == 422:
        return ValidationError(message, status_code, response_data)
    elif status_code == 429:
        retry_after = response_data.get("retry_after") if response_data else None
        return RateLimitError(message, status_code, response_data, retry_after)
    elif status_code >= 500:
        return ServerError(message, status_code, response_data)
    else:
        return JebatError(message, status_code, response_data)
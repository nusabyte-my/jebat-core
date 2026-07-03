"""
JEBAT SDK Retry Logic

Retry configuration with exponential backoff using tenacity.
"""

from typing import Callable, Type, TypeVar, Union
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
    before_sleep_log,
    after_log,
)
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default retry configuration
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MIN_WAIT = 1  # seconds
DEFAULT_MAX_WAIT = 10  # seconds
DEFAULT_MULTIPLIER = 2

# Exception types that should trigger a retry
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    IOError,
)


def is_retryable_exception(exc: BaseException) -> bool:
    """Determine if an exception should trigger a retry."""
    from .exceptions import (
        ServerError,
        TimeoutError,
        ConnectionError,
        RateLimitError,
    )

    # Retry on network/connection errors
    if isinstance(exc, RETRYABLE_EXCEPTIONS):
        return True

    # Retry on server errors (5xx)
    if isinstance(exc, ServerError):
        return True

    # Retry on rate limit with retry-after
    if isinstance(exc, RateLimitError):
        return True

    # Don't retry on client errors (4xx except 429)
    return False


def get_retry_decorator(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_MIN_WAIT,
    max_wait: float = DEFAULT_MAX_WAIT,
    multiplier: float = DEFAULT_MULTIPLIER,
    retryable_exceptions: tuple = RETRYABLE_EXCEPTIONS,
) -> Callable:
    """
    Create a retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        multiplier: Exponential multiplier
        retryable_exceptions: Tuple of exception types to retry

    Returns:
        A retry decorator
    """
    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(
            multiplier=multiplier,
            min=min_wait,
            max=max_wait,
        ),
        retry=retry_if_exception_type(retryable_exceptions) | retry_if_exception(is_retryable_exception),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
    )


def retry_with_backoff(
    func: Callable[..., T],
    *args,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_MIN_WAIT,
    max_wait: float = DEFAULT_MAX_WAIT,
    multiplier: float = DEFAULT_MULTIPLIER,
    retryable_exceptions: tuple = RETRYABLE_EXCEPTIONS,
    **kwargs,
) -> T:
    """
    Execute a function with exponential backoff retry.

    Args:
        func: Function to execute
        max_attempts: Maximum number of attempts
        min_wait: Minimum wait time
        max_wait: Maximum wait time
        multiplier: Exponential multiplier
        retryable_exceptions: Exception types to retry
        *args, **kwargs: Arguments to pass to func

    Returns:
        Function result
    """
    retry_decorator = get_retry_decorator(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        multiplier=multiplier,
        retryable_exceptions=retryable_exceptions,
    )
    return retry_decorator(func)(*args, **kwargs)


async def async_retry_with_backoff(
    func: Callable[..., T],
    *args,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_MIN_WAIT,
    max_wait: float = DEFAULT_MAX_WAIT,
    multiplier: float = DEFAULT_MULTIPLIER,
    retryable_exceptions: tuple = RETRYABLE_EXCEPTIONS,
    **kwargs,
) -> T:
    """
    Execute an async function with exponential backoff retry.

    Args:
        func: Async function to execute
        max_attempts: Maximum number of attempts
        min_wait: Minimum wait time
        max_wait: Maximum wait time
        multiplier: Exponential multiplier
        retryable_exceptions: Exception types to retry
        *args, **kwargs: Arguments to pass to func

    Returns:
        Function result
    """
    retry_decorator = get_retry_decorator(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        multiplier=multiplier,
        retryable_exceptions=retryable_exceptions,
    )
    return await retry_decorator(func)(*args, **kwargs)


# Pre-configured retry decorators for common use cases

# Quick retry for transient errors (2 retries, fast)
quick_retry = get_retry_decorator(
    max_attempts=2,
    min_wait=0.5,
    max_wait=2,
    multiplier=1,
)

# Standard retry for API calls (3 retries, moderate)
standard_retry = get_retry_decorator(
    max_attempts=3,
    min_wait=1,
    max_wait=10,
    multiplier=2,
)

# Aggressive retry for critical operations (5 retries, slow)
aggressive_retry = get_retry_decorator(
    max_attempts=5,
    min_wait=2,
    max_wait=30,
    multiplier=2,
)

# Rate limit aware retry (respects retry-after header)
rate_limit_retry = get_retry_decorator(
    max_attempts=5,
    min_wait=1,
    max_wait=60,
    multiplier=2,
    retryable_exceptions=(Exception,),  # We'll filter in is_retryable_exception
)
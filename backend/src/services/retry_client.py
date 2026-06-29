"""Retry decorator with exponential backoff for API calls."""

import functools
import random
import time
from typing import Callable, ParamSpec, TypeVar

from observability.logging import log_failure, logger

from config import get_settings

P = ParamSpec("P")
T = TypeVar("T")


class RetryableError(Exception):
    """Exception that should trigger a retry."""

    pass


class NonRetryableError(Exception):
    """Exception that should not trigger a retry."""

    pass


def retry_with_backoff(
    max_attempts: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
    retryable_exceptions: tuple[type[Exception], ...] = (RetryableError,),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for retrying API calls with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of retry attempts (default from settings)
        base_delay: Initial delay between retries in seconds (default from settings)
        max_delay: Maximum delay between retries in seconds (default from settings)
        retryable_exceptions: Tuple of exception types that should trigger retry
    """
    settings = get_settings()
    attempts = max_attempts or settings.api_retry_attempts
    base = base_delay or settings.api_retry_backoff_base
    max_wait = max_delay or settings.api_retry_max_wait

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None

            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except NonRetryableError:
                    raise
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < attempts - 1:
                        # Exponential backoff with full jitter
                        delay = min(base * (2**attempt), max_wait)
                        jittered_delay = random.uniform(0, delay)
                        logger.warning(
                            "api.retry",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=attempts,
                            delay=jittered_delay,
                            error=str(e),
                        )
                        time.sleep(jittered_delay)
                except Exception as e:
                    # Check if this unexpected exception is actually retryable
                    if is_retryable_error(e) and attempt < attempts - 1:
                        last_exception = e
                        delay = min(base * (2**attempt), max_wait)
                        jittered_delay = random.uniform(0, delay)
                        logger.warning(
                            "api.retry_unexpected",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=attempts,
                            delay=jittered_delay,
                            error=str(e),
                        )
                        time.sleep(jittered_delay)
                    else:
                        # Non-retryable unexpected exception, log and raise
                        log_failure("api.unexpected_error", error=str(e), function=func.__name__)
                        raise

            # All retries exhausted
            log_failure(
                "api.max_retries_exceeded",
                function=func.__name__,
                attempts=attempts,
                error=str(last_exception) if last_exception else "Unknown",
            )
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Max retries exceeded for {func.__name__}")

        return wrapper

    return decorator


def is_rate_limit_error(error: Exception) -> bool:
    """Check if an exception is a rate limit error from Google APIs."""
    error_str = str(error).lower()
    rate_limit_indicators = [
        "rate limit",
        "rate_limit",
        "429",
        "too many requests",
        "quota exceeded",
        "user rate limit",
        "resource exhausted",
    ]
    return any(indicator in error_str for indicator in rate_limit_indicators)


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable (network, rate limit, server error)."""
    error_str = str(error).lower()
    retryable_indicators = [
        "timeout",
        "connection",
        "temporary",
        "unavailable",
        "503",
        "502",
        "500",
        "internal server error",
        "deadline exceeded",
    ]
    return is_rate_limit_error(error) or any(
        indicator in error_str for indicator in retryable_indicators
    )

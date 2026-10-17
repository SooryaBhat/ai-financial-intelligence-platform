"""
Resilient Supabase/PostgREST Query Execution.
Provides bounded retries with exponential backoff for transient connection errors
(e.g. RemoteProtocolError: Server disconnected, ConnectError, ReadTimeout).
Preserves multi-tenant isolation, RLS, and security constraints.
"""
import time
from typing import Any, Callable

import httpx

from app.core.logging import logger

TRANSIENT_NETWORK_ERRORS = (
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
    httpx.ConnectTimeout,
    httpx.PoolTimeout,
)


def execute_with_retry(
    query_or_func: Any,
    max_retries: int = 3,
    initial_delay: float = 0.2,
) -> Any:
    """
    Safely execute a PostgREST query or callable with bounded retries.
    Only retries on transient transport/connection failures.
    Does not swallow application errors or bypass authentication/authorization.
    """
    delay = initial_delay
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            if hasattr(query_or_func, "execute"):
                return query_or_func.execute()
            elif callable(query_or_func):
                return query_or_func()
            else:
                raise TypeError(f"Expected PostgREST query builder or callable, got {type(query_or_func)}")
        except TRANSIENT_NETWORK_ERRORS as exc:
            last_error = exc
            if attempt >= max_retries:
                logger.error(
                    "[DB Retry] Exhausted {} retries due to transient connection failure: {}",
                    max_retries,
                    exc,
                )
                raise
            logger.warning(
                "[DB Retry] Transient connection failure (attempt {}/{}): {}. Retrying in {:.2f}s...",
                attempt,
                max_retries,
                exc,
                delay,
            )
            time.sleep(delay)
            delay *= 2
    if last_error:
        raise last_error

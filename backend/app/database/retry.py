"""
Resilient Supabase/PostgREST Query Execution.
Provides bounded retries with exponential backoff for transient connection errors
(e.g. RemoteProtocolError: Server disconnected, ConnectError, ReadTimeout).
Preserves multi-tenant isolation, RLS, and security constraints.
"""
import socket
import time
from typing import Any, Callable

import httpx

from app.core.logging import logger
from app.exceptions.http_exceptions import DatabaseConnectionError

TRANSIENT_NETWORK_ERRORS = (
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
    httpx.ConnectTimeout,
    httpx.PoolTimeout,
    socket.gaierror,
    socket.timeout,
)


def _is_transient_error(exc: Exception) -> bool:
    """Check if exception is a transient network/DNS failure."""
    if isinstance(exc, TRANSIENT_NETWORK_ERRORS):
        return True
    err_str = str(exc)
    return any(term in err_str for term in ("11001", "getaddrinfo failed", "ConnectError", "RemoteProtocolError", "Connection refused"))


def execute_with_retry(
    query_or_func: Any,
    max_retries: int = 4,
    initial_delay: float = 0.4,
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
        except Exception as exc:
            if not _is_transient_error(exc):
                # Application/validation/schema error — do not retry
                raise exc

            last_error = exc
            clean_err = str(exc)
            if "11001" in clean_err or "getaddrinfo" in clean_err:
                clean_msg = "DNS lookup interrupted (WSAHOST_NOT_FOUND 11001)"
            else:
                clean_msg = type(exc).__name__

            if attempt >= max_retries:
                logger.error(
                    "[DB Retry] Exhausted {} retries due to transient connection failure: {}. Raising DatabaseConnectionError.",
                    max_retries,
                    clean_msg,
                )
                raise DatabaseConnectionError(
                    "Database service is temporarily unreachable. Please check network connectivity or try again shortly."
                ) from exc

            logger.warning(
                "[DB Retry] Transient connection failure (attempt {}/{}): {}. Retrying in {:.2f}s...",
                attempt,
                max_retries,
                clean_msg,
                delay,
            )
            time.sleep(delay)
            delay = min(delay * 2.0, 3.0)

    if last_error:
        raise DatabaseConnectionError("Database connection failed after retries.") from last_error

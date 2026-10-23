"""
FastAPI exception handlers.
Registered in main.py via app.add_exception_handler().
Converts all AppException subclasses into structured JSON responses.
"""
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.logging import logger
from app.exceptions.base import AppException


def _error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Any = None,
) -> JSONResponse:
    """Build a consistent error JSON envelope."""
    body = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
        },
    }
    if details:
        body["error"]["details"] = details  # type: ignore[index]
    return JSONResponse(status_code=status_code, content=body)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle all AppException subclasses."""
    logger.warning(
        "AppException | {} {} -> {} {}",
        request.method,
        request.url.path,
        exc.status_code,
        exc.error_code,
    )
    return _error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details if exc.details else None,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic request body / query param validation errors."""
    errors = exc.errors()
    logger.warning(
        "ValidationError | {} {} | {} error(s)",
        request.method,
        request.url.path,
        len(errors),
    )
    # Simplify pydantic v2 error list to something API-friendly
    details = [
        {
            "field": " -> ".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in errors
    ]
    return _error_response(
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Request validation failed.",
        details=details,
    )


async def transport_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle transient network, DNS, and HTTP transport connection failures."""
    err_msg = str(exc)
    if "11001" in err_msg or "getaddrinfo" in err_msg:
        clean_msg = "Database DNS lookup interrupted (temporary network/name resolution failure)."
    elif "ConnectError" in type(exc).__name__:
        clean_msg = "Unable to connect to database host (temporary network connection failure)."
    else:
        clean_msg = "Database network transport failure."

    logger.warning(
        "[DB Connectivity] {} {} -> 503 DATABASE_UNAVAILABLE | {}",
        request.method,
        request.url.path,
        clean_msg,
    )
    return _error_response(
        status_code=503,
        error_code="DATABASE_UNAVAILABLE",
        message="Database service is temporarily unreachable. Please check network connectivity or try again shortly.",
        details={"path": request.url.path, "retry_after": 2},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions."""
    err_str = str(exc)
    # Check if a transport/connection error was wrapped in another exception
    if any(k in err_str for k in ("ConnectError", "getaddrinfo failed", "11001", "RemoteProtocolError")):
        return await transport_exception_handler(request, exc)

    logger.exception(
        "UnhandledException | {} {} | {}",
        request.method,
        request.url.path,
        str(exc),
    )
    return _error_response(
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""
    import httpx
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(httpx.TransportError, transport_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

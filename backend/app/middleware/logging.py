"""
Request/Response logging middleware.
Logs every request with method, path, status code, and response time.
"""
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with timing and status code."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Attach request_id to request state for downstream use
        request.state.request_id = request_id

        logger.info(
            "-> {} {} | id={}",
            request.method,
            request.url.path,
            request_id,
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception(
                "[FAIL] {} {} | id={} | Unhandled: {}",
                request.method,
                request.url.path,
                request_id,
                str(exc),
            )
            from fastapi.responses import JSONResponse
            from app.core.config import settings
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": str(exc) if settings.debug else "An unexpected error occurred. Please try again later.",
                        "details": str(exc),
                    },
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Response-Time": f"{duration_ms}ms",
                },
            )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "<- {} {} | id={} | status={} | {}ms",
            request.method,
            request.url.path,
            request_id,
            response.status_code,
            duration_ms,
        )

        # Inject useful headers into the response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response

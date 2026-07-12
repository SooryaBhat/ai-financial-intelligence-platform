"""
HTTP-mapped exception classes.
Raise these from services / repositories — the registered handler in
handlers.py will convert them to proper JSON HTTP responses.
"""
from typing import Any, Dict, Optional

from app.exceptions.base import AppException


class NotFoundError(AppException):
    """Resource does not exist or was soft-deleted."""

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        id_part = f" '{resource_id}'" if resource_id else ""
        super().__init__(
            message=f"{resource}{id_part} not found.",
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class UnauthorizedError(AppException):
    """No valid authentication credentials provided."""

    def __init__(
        self,
        message: str = "Authentication required.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
            details=details,
        )


class ForbiddenError(AppException):
    """Authenticated user lacks the required permission."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
            details=details,
        )


class ConflictError(AppException):
    """Unique constraint or business rule conflict."""

    def __init__(
        self,
        message: str = "A conflict occurred.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


class ValidationError(AppException):
    """Business-level validation failed (distinct from Pydantic schema errors)."""

    def __init__(
        self,
        message: str = "Validation failed.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class BadRequestError(AppException):
    """Malformed request that cannot be processed."""

    def __init__(
        self,
        message: str = "Bad request.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=400,
            error_code="BAD_REQUEST",
            details=details,
        )


class DatabaseError(AppException):
    """Unexpected database error."""

    def __init__(
        self,
        message: str = "A database error occurred.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details,
        )


class ExternalServiceError(AppException):
    """Third-party service (Supabase, payment gateway, etc.) returned an error."""

    def __init__(
        self,
        service: str = "External service",
        message: str = "An external service error occurred.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=f"{service}: {message}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
        )

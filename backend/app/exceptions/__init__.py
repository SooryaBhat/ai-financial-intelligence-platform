"""Exceptions package."""
from app.exceptions.base import AppException
from app.exceptions.http_exceptions import (
    BadRequestError,
    ConflictError,
    DatabaseError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)

__all__ = [
    "AppException",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "ConflictError",
    "ValidationError",
    "BadRequestError",
    "DatabaseError",
    "ExternalServiceError",
]

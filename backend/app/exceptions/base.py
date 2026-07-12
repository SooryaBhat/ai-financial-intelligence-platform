"""
Base application exception hierarchy.
All domain exceptions extend AppException so they can be caught uniformly
in the FastAPI exception handler.
"""
from typing import Any, Dict, Optional


class AppException(Exception):
    """
    Base exception for all application-level errors.
    Carries an HTTP status code and a machine-readable error code
    that is returned in API responses.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"status={self.status_code}, "
            f"code={self.error_code}, "
            f"message={self.message!r})"
        )

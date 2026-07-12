"""
Common / shared Pydantic v2 schemas.
Used as base classes and response wrappers throughout all modules.
"""
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ── Base model ────────────────────────────────────────────────

class AppBaseModel(BaseModel):
    """
    Base model for all schemas.
    - Validates assignment for safety.
    - Uses from_attributes to allow ORM / dict-mode construction.
    - Strips whitespace from str fields via validators in subclasses.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ── Timestamp mixin ───────────────────────────────────────────

class TimestampMixin(AppBaseModel):
    """Read-only timestamp fields returned on all persisted resources.
    
    Note: When using TimestampMixin, do NOT also list AppBaseModel as a base.
    Use MySchema(TimestampMixin) not MySchema(TimestampMixin).
    TimestampMixin already extends AppBaseModel.
    """
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Pagination ────────────────────────────────────────────────

T = TypeVar("T")


class PaginationParams(AppBaseModel):
    """Standard query params for list endpoints."""
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(AppBaseModel, Generic[T]):
    """Uniform list response envelope with pagination metadata."""
    success: bool = True
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        data: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        import math
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if page_size else 1,
        )


# ── Standard response wrappers ────────────────────────────────

class SuccessResponse(AppBaseModel, Generic[T]):
    """Single-resource success envelope."""
    success: bool = True
    data: T


class MessageResponse(AppBaseModel):
    """Simple message-only response (e.g., delete confirmation)."""
    success: bool = True
    message: str


class ErrorDetail(AppBaseModel):
    field: Optional[str] = None
    message: str
    type: Optional[str] = None


class ErrorResponse(AppBaseModel):
    success: bool = False
    error: dict[str, Any]

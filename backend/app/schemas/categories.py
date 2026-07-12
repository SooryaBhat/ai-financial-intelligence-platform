"""Categories schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import CategoryType
from app.schemas.common import AppBaseModel, TimestampMixin


class CategoryBase(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: CategoryType
    parent_id: Optional[UUID] = None
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[UUID] = None
    description: Optional[str] = None


class CategoryResponse(CategoryBase, TimestampMixin):
    id: UUID
    company_id: UUID
    deleted_at: Optional[datetime] = None

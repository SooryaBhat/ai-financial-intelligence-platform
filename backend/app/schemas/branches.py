"""Branches schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import AppBaseModel, TimestampMixin


class BranchBase(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True


class BranchCreate(BranchBase):
    pass


class BranchUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class BranchResponse(BranchBase, TimestampMixin):
    id: UUID
    company_id: UUID
    deleted_at: Optional[datetime] = None

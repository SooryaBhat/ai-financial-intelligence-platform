"""Warehouses schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import AppBaseModel, TimestampMixin


class WarehouseBase(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    branch_id: Optional[UUID] = None
    address: Optional[str] = None
    is_active: bool = True


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    branch_id: Optional[UUID] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase, TimestampMixin):
    id: UUID
    company_id: UUID
    deleted_at: Optional[datetime] = None

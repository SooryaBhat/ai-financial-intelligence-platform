"""Sales and sale items schemas."""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import SaleStatus
from app.schemas.common import AppBaseModel, TimestampMixin


# ── Sale Items ────────────────────────────────────────────────

class SaleItemCreate(AppBaseModel):
    product_id: UUID
    warehouse_id: Optional[UUID] = None
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    discount_pct: float = Field(default=0, ge=0, le=100)
    tax_rate: float = Field(default=0, ge=0, le=100)
    line_total: float = Field(..., ge=0)


class SaleItemResponse(AppBaseModel):
    id: UUID
    sale_id: UUID
    product_id: UUID
    warehouse_id: Optional[UUID] = None
    quantity: float
    unit_price: float
    discount_pct: float
    tax_rate: float
    line_total: float
    created_at: datetime


# ── Sales ─────────────────────────────────────────────────────

class SaleBase(AppBaseModel):
    customer_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    sale_number: str = Field(..., min_length=1, max_length=100)
    sale_date: date = Field(default_factory=date.today)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: Optional[str] = None


class SaleCreate(SaleBase):
    items: List[SaleItemCreate] = Field(..., min_length=1)
    subtotal: float = Field(..., ge=0)
    discount_amount: float = Field(default=0, ge=0)
    tax_amount: float = Field(default=0, ge=0)
    total_amount: float = Field(..., ge=0)


class SaleUpdate(AppBaseModel):
    status: Optional[SaleStatus] = None
    notes: Optional[str] = None


class SaleResponse(SaleBase, TimestampMixin):
    id: UUID
    company_id: UUID
    status: SaleStatus
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    created_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    items: Optional[List[SaleItemResponse]] = None

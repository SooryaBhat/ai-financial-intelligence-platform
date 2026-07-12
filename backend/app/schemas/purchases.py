"""Purchases and purchase items schemas."""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import PurchaseStatus
from app.schemas.common import AppBaseModel, TimestampMixin


# ── Purchase Items ────────────────────────────────────────────

class PurchaseItemCreate(AppBaseModel):
    product_id: UUID
    warehouse_id: Optional[UUID] = None
    quantity: float = Field(..., gt=0)
    unit_cost: float = Field(..., ge=0)
    tax_rate: float = Field(default=0, ge=0, le=100)
    line_total: float = Field(..., ge=0)
    received_qty: float = Field(default=0, ge=0)


class PurchaseItemResponse(AppBaseModel):
    id: UUID
    purchase_id: UUID
    product_id: UUID
    warehouse_id: Optional[UUID] = None
    quantity: float
    unit_cost: float
    tax_rate: float
    line_total: float
    received_qty: float
    created_at: datetime


# ── Purchases ─────────────────────────────────────────────────

class PurchaseBase(AppBaseModel):
    supplier_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    purchase_number: str = Field(..., min_length=1, max_length=100)
    purchase_date: date = Field(default_factory=date.today)
    expected_delivery: Optional[date] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: Optional[str] = None


class PurchaseCreate(PurchaseBase):
    items: List[PurchaseItemCreate] = Field(..., min_length=1)
    subtotal: float = Field(..., ge=0)
    tax_amount: float = Field(default=0, ge=0)
    total_amount: float = Field(..., ge=0)


class PurchaseUpdate(AppBaseModel):
    status: Optional[PurchaseStatus] = None
    expected_delivery: Optional[date] = None
    notes: Optional[str] = None


class PurchaseResponse(PurchaseBase, TimestampMixin):
    id: UUID
    company_id: UUID
    status: PurchaseStatus
    subtotal: float
    tax_amount: float
    total_amount: float
    created_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    items: Optional[List[PurchaseItemResponse]] = None

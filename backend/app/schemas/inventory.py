"""Inventory and stock movement schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import StockMovementType, StockReferenceType
from app.schemas.common import AppBaseModel, TimestampMixin


# ── Inventory ─────────────────────────────────────────────────

class InventoryResponse(AppBaseModel):
    """Current stock level per product per warehouse."""
    id: UUID
    company_id: UUID
    product_id: UUID
    warehouse_id: UUID
    quantity: float
    reorder_level: float
    updated_at: datetime


class InventoryUpdate(AppBaseModel):
    reorder_level: Optional[float] = Field(None, ge=0)


class AdjustInventoryRequest(AppBaseModel):
    """Manual inventory adjustment request."""
    product_id: UUID
    warehouse_id: UUID
    quantity_delta: float = Field(..., description="Positive = add stock, negative = remove stock")
    notes: Optional[str] = None


# ── Stock Movements ───────────────────────────────────────────

class StockMovementCreate(AppBaseModel):
    product_id: UUID
    warehouse_id: UUID
    movement_type: StockMovementType
    quantity: float = Field(..., description="Positive = in, Negative = out")
    reference_type: Optional[StockReferenceType] = None
    reference_id: Optional[UUID] = None
    notes: Optional[str] = None


class StockMovementResponse(AppBaseModel):
    id: UUID
    company_id: UUID
    product_id: UUID
    warehouse_id: UUID
    movement_type: StockMovementType
    quantity: float
    reference_type: Optional[StockReferenceType] = None
    reference_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime

"""Payments schemas."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import PaymentMethod
from app.schemas.common import AppBaseModel, TimestampMixin


class PaymentBase(AppBaseModel):
    invoice_id: UUID
    payment_date: date = Field(default_factory=date.today)
    amount: float = Field(..., gt=0)
    payment_method: Optional[PaymentMethod] = None
    reference: Optional[str] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    exchange_rate: float = Field(default=1.0, gt=0)
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(AppBaseModel):
    payment_date: Optional[date] = None
    amount: Optional[float] = Field(None, gt=0)
    payment_method: Optional[PaymentMethod] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(PaymentBase, TimestampMixin):
    id: UUID
    company_id: UUID
    created_by: Optional[UUID] = None

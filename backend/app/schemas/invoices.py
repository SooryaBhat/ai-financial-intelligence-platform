"""Invoices schemas."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, model_validator

from app.core.constants import InvoiceStatus, InvoiceType
from app.schemas.common import AppBaseModel, TimestampMixin


class InvoiceBase(AppBaseModel):
    invoice_type: InvoiceType
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_date: date = Field(default_factory=date.today)
    due_date: Optional[date] = None
    customer_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    sale_id: Optional[UUID] = None
    purchase_id: Optional[UUID] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_counterparty(self) -> "InvoiceBase":
        if self.invoice_type == InvoiceType.RECEIVABLE and not self.customer_id and not self.sale_id:
            pass  # Walk-in allowed
        if self.invoice_type == InvoiceType.PAYABLE and not self.supplier_id and not self.purchase_id:
            pass  # Direct expense allowed
        return self


class InvoiceCreate(InvoiceBase):
    subtotal: float = Field(..., ge=0)
    tax_amount: float = Field(default=0, ge=0)
    total_amount: float = Field(..., ge=0)


class InvoiceUpdate(AppBaseModel):
    status: Optional[InvoiceStatus] = None
    due_date: Optional[date] = None
    amount_paid: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase, TimestampMixin):
    id: UUID
    company_id: UUID
    status: InvoiceStatus
    subtotal: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    amount_due: float  # Generated column in DB
    deleted_at: Optional[datetime] = None

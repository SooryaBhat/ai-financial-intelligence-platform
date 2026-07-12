"""Expenses schemas."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import ExpenseStatus, PaymentMethod
from app.schemas.common import AppBaseModel, TimestampMixin


class ExpenseBase(AppBaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: float = Field(..., gt=0)
    expense_date: date = Field(default_factory=date.today)
    category_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    payment_method: Optional[PaymentMethod] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(AppBaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount: Optional[float] = Field(None, gt=0)
    expense_date: Optional[date] = None
    category_id: Optional[UUID] = None
    payment_method: Optional[PaymentMethod] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class ExpenseApproveRequest(AppBaseModel):
    status: ExpenseStatus  # approved or rejected
    notes: Optional[str] = None


class ExpenseResponse(ExpenseBase, TimestampMixin):
    id: UUID
    company_id: UUID
    status: ExpenseStatus
    approved_by: Optional[UUID] = None
    created_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None

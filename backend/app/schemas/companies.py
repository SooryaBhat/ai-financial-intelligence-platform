"""Companies schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.core.constants import SubscriptionStatus
from app.schemas.common import AppBaseModel, TimestampMixin


class CompanyBase(AppBaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    timezone: str = Field(default="UTC")
    logo_url: Optional[str] = None


class CompanyCreate(CompanyBase):
    plan_id: Optional[UUID] = None


class CompanyUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    timezone: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase, TimestampMixin):
    id: UUID
    plan_id: Optional[UUID] = None
    subscription_status: SubscriptionStatus
    trial_ends_at: Optional[datetime] = None
    is_active: bool
    deleted_at: Optional[datetime] = None

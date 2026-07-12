"""Plans and subscriptions schemas."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import BillingCycle, SubscriptionStatus
from app.schemas.common import AppBaseModel, TimestampMixin


class PlanResponse(TimestampMixin):
    id: UUID
    name: str
    description: Optional[str] = None
    price_monthly: float
    price_yearly: float
    max_users: Optional[int] = None
    max_branches: Optional[int] = None
    features: Dict[str, Any] = {}
    is_active: bool


class SubscriptionBase(AppBaseModel):
    plan_id: UUID
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    amount: float = Field(..., ge=0)


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionResponse(SubscriptionBase, TimestampMixin):
    id: UUID
    company_id: UUID
    status: SubscriptionStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    external_subscription_id: Optional[str] = None

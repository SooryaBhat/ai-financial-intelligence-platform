"""Integrations schemas."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import IntegrationProvider, IntegrationStatus, SyncFrequency
from app.schemas.common import AppBaseModel, TimestampMixin


class IntegrationBase(AppBaseModel):
    provider: IntegrationProvider
    name: str = Field(..., min_length=1, max_length=255)
    sync_frequency: SyncFrequency = SyncFrequency.MANUAL
    config: Dict[str, Any] = Field(
        default={},
        description="Connection config. Credentials must be encrypted at the application layer."
    )


class IntegrationCreate(IntegrationBase):
    pass


class IntegrationUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[IntegrationStatus] = None
    sync_frequency: Optional[SyncFrequency] = None
    config: Optional[Dict[str, Any]] = None


class IntegrationResponse(IntegrationBase, TimestampMixin):
    id: UUID
    company_id: UUID
    status: IntegrationStatus
    last_synced_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None

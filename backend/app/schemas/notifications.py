"""Notifications schemas."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import NotificationType
from app.schemas.common import AppBaseModel


class NotificationCreate(AppBaseModel):
    user_id: UUID
    type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    message: Optional[str] = None
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


class NotificationResponse(AppBaseModel):
    id: UUID
    company_id: UUID
    user_id: UUID
    type: NotificationType
    title: str
    message: Optional[str] = None
    is_read: bool
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime


class MarkReadRequest(AppBaseModel):
    notification_ids: list[UUID]

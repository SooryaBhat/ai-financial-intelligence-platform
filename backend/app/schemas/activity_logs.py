"""Activity logs schemas (read-only)."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from app.schemas.common import AppBaseModel


class ActivityLogCreate(AppBaseModel):
    """Internal use only."""
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    metadata: Dict[str, Any] = {}


class ActivityLogResponse(AppBaseModel):
    id: UUID
    company_id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime

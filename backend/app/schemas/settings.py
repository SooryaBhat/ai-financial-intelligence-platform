"""Settings schemas."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import AppBaseModel, TimestampMixin


class SettingUpsert(AppBaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: Any
    description: Optional[str] = None


class SettingResponse(TimestampMixin):
    id: UUID
    company_id: UUID
    key: str
    value: Any
    description: Optional[str] = None
    updated_by: Optional[UUID] = None

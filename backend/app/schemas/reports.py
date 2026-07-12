"""Reports schemas."""
from datetime import date, datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import ReportStatus, ReportType
from app.schemas.common import AppBaseModel, TimestampMixin


class ReportCreate(AppBaseModel):
    report_type: ReportType
    title: str = Field(..., min_length=1, max_length=255)
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class ReportUpdate(AppBaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    data: Optional[Dict[str, Any]] = None
    file_url: Optional[str] = None
    status: Optional[ReportStatus] = None


class ReportResponse(TimestampMixin):
    id: UUID
    company_id: UUID
    user_id: Optional[UUID] = None
    report_type: ReportType
    title: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    data: Dict[str, Any] = {}
    file_url: Optional[str] = None
    status: ReportStatus
    deleted_at: Optional[datetime] = None

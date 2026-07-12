"""Audit logs schemas (read-only, append-only)."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.constants import AuditAction
from app.schemas.common import AppBaseModel


class AuditLogCreate(AppBaseModel):
    """Internal use only — created by the audit service, never by API callers."""
    user_id: Optional[UUID] = None
    action: AuditAction
    resource_type: str
    resource_id: Optional[UUID] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(AppBaseModel):
    id: UUID
    company_id: UUID
    user_id: Optional[UUID] = None
    action: AuditAction
    resource_type: str
    resource_id: Optional[UUID] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

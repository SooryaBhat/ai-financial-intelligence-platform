"""Roles and permissions schemas."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import AppBaseModel, TimestampMixin


# ── Permissions ───────────────────────────────────────────────

class PermissionResponse(AppBaseModel):
    id: UUID
    resource: str
    action: str
    description: Optional[str] = None
    created_at: datetime


# ── Roles ─────────────────────────────────────────────────────

class RoleBase(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: Optional[List[UUID]] = None


class RoleUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class RoleResponse(RoleBase, TimestampMixin):
    id: UUID
    company_id: Optional[UUID] = None
    is_system: bool
    permissions: Optional[List[PermissionResponse]] = None


class AssignPermissionsRequest(AppBaseModel):
    permission_ids: List[UUID]

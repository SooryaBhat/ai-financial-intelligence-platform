"""Users and company_users schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.common import AppBaseModel, TimestampMixin


class UserBase(AppBaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None


class UserUpdate(AppBaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase, TimestampMixin):
    id: UUID
    is_active: bool
    deleted_at: Optional[datetime] = None


# ── Company-User membership ───────────────────────────────────

class CompanyUserBase(AppBaseModel):
    user_id: UUID
    role_id: UUID
    branch_id: Optional[UUID] = None
    is_active: bool = True


class CompanyUserCreate(CompanyUserBase):
    pass


class CompanyUserUpdate(AppBaseModel):
    role_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class CompanyUserResponse(CompanyUserBase, TimestampMixin):
    id: UUID
    company_id: UUID
    invited_at: Optional[datetime] = None
    joined_at: Optional[datetime] = None


class InviteUserRequest(AppBaseModel):
    email: EmailStr
    role_id: UUID
    branch_id: Optional[UUID] = None

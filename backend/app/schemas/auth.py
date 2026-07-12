"""Auth schemas — signup, login, onboarding, token responses."""
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import AppBaseModel


class SignupRequest(AppBaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class LoginRequest(AppBaseModel):
    email: EmailStr
    password: str


class OnboardRequest(AppBaseModel):
    """Sent after signup to create the user's first company."""
    company_name: str = Field(..., min_length=2, max_length=255)
    company_slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    timezone: str = Field(default="UTC")


class TokenResponse(AppBaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class AuthUserResponse(AppBaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool


class MeResponse(AppBaseModel):
    user: AuthUserResponse
    companies: list  # list of CompanyMembership — avoid circular import


class RefreshRequest(AppBaseModel):
    refresh_token: str

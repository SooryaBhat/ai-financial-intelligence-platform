"""
Authentication service.
Orchestrates Supabase Auth for signup, login, logout, token refresh,
and the company onboarding flow (create company + assign owner role).
"""
from typing import Any, Dict, Optional
from uuid import UUID

from supabase import Client
from gotrue.errors import AuthApiError

from app.core.logging import logger
from app.database.client import get_admin_client, get_anon_client
from app.exceptions import ConflictError, ExternalServiceError, NotFoundError, UnauthorizedError
from app.repositories.companies import CompanyRepository
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, OnboardRequest, SignupRequest


class AuthService:
    """
    Handles all Supabase Auth operations plus the post-signup onboarding flow.
    """

    def signup(self, data: SignupRequest) -> Dict[str, Any]:
        """
        1. Create auth.users record via Supabase Auth.
        2. Create the public.users profile row via admin client.
        3. Return auth session.
        """
        client = get_anon_client()
        try:
            resp = client.auth.sign_up({
                "email": data.email,
                "password": data.password,
                "options": {
                    "data": {
                        "full_name": data.full_name,
                        "phone": data.phone or "",
                    }
                }
            })
        except AuthApiError as exc:
            if "already registered" in str(exc).lower() or "User already registered" in str(exc):
                raise ConflictError("An account with this email already exists.")
            raise ExternalServiceError("Supabase Auth", str(exc))

        if not resp.user:
            raise ExternalServiceError("Supabase Auth", "No user returned after signup.")

        # Create users profile row via admin client (bypasses RLS for the profile insert)
        admin = get_admin_client()
        try:
            admin.table("users").insert({
                "id": resp.user.id,
                "email": data.email,
                "full_name": data.full_name,
                "phone": data.phone,
            }).execute()
        except Exception as exc:
            logger.warning("Failed to create users profile row: {}", str(exc))

        session = resp.session
        return {
            "access_token": session.access_token if session else "",
            "refresh_token": session.refresh_token if session else "",
            "token_type": "bearer",
            "expires_in": session.expires_in if session else None,
            "user": {
                "id": resp.user.id,
                "email": data.email,
                "full_name": data.full_name,
            },
        }

    def login(self, data: LoginRequest) -> Dict[str, Any]:
        """Authenticate with email + password and return JWT tokens."""
        client = get_anon_client()
        try:
            resp = client.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password,
            })
        except AuthApiError as exc:
            raise UnauthorizedError("Invalid email or password.")

        session = resp.session
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "expires_in": session.expires_in,
        }

    def logout(self, jwt: str) -> None:
        """Invalidate the user's session on Supabase."""
        from app.database.client import get_user_client
        try:
            client = get_user_client(jwt)
            client.auth.sign_out()
        except Exception as exc:
            logger.warning("Logout error (non-critical): {}", str(exc))

    def refresh(self, refresh_token: str) -> Dict[str, Any]:
        """Exchange a refresh token for new tokens."""
        client = get_anon_client()
        try:
            resp = client.auth.refresh_session(refresh_token)
        except AuthApiError as exc:
            raise UnauthorizedError("Invalid or expired refresh token.")
        session = resp.session
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "expires_in": session.expires_in,
        }

    def verify_token(self, jwt: str) -> Dict[str, Any]:
        """
        Verify a JWT and return the decoded user payload.
        Uses Supabase's get_user() call which validates against the auth server.
        """
        from app.database.client import get_user_client
        try:
            client = get_user_client(jwt)
            resp = client.auth.get_user(jwt)
            if not resp.user:
                raise UnauthorizedError("Token is invalid or expired.")
            return {"id": resp.user.id, "email": resp.user.email}
        except UnauthorizedError:
            raise
        except Exception as exc:
            logger.warning("Token verification failed: {}", str(exc))
            raise UnauthorizedError("Token verification failed.")

    def onboard(self, data: OnboardRequest, user_id: str) -> Dict[str, Any]:
        """
        After signup, the user creates their first company.
        Steps:
          1. Create the company row.
          2. Find or create the 'Owner' system role.
          3. Create the company_users record linking user → company → owner role.
        """
        admin = get_admin_client()
        company_repo = CompanyRepository(admin)
        role_repo = RoleRepository(admin)
        user_repo = UserRepository(admin)

        # Check slug uniqueness
        if company_repo.get_by_slug(data.company_slug):
            raise ConflictError(f"Company slug '{data.company_slug}' is already taken.")

        # Create company
        company = company_repo.create({
            "name": data.company_name,
            "slug": data.company_slug,
            "industry": data.industry,
            "country": data.country,
            "currency": data.currency,
            "timezone": data.timezone,
        })
        company_id = company["id"]

        # Find the system 'Admin' role (is_system=true, company_id IS NULL)
        roles = role_repo.list_for_company(company_id)
        owner_role = next(
            (r for r in roles if r["name"].lower() == "admin" and r["is_system"]),
            None,
        )
        if not owner_role:
            # Fallback: create a company-specific Owner role
            owner_role = role_repo.create({
                "company_id": company_id,
                "name": "Owner",
                "description": "Company owner with full access",
                "is_system": False,
            })

        # Link user to company
        user_repo.create_company_user({
            "company_id": company_id,
            "user_id": user_id,
            "role_id": owner_role["id"],
            "is_active": True,
            "joined_at": "now()",
        })

        logger.info("Onboarding complete | user={} company={}", user_id, company_id)
        return company


auth_service = AuthService()

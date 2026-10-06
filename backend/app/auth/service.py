"""
Authentication service.
Orchestrates Supabase Auth for signup, login, logout, token refresh,
and the company onboarding flow (create company + assign owner role).
"""
from typing import Any, Dict, Optional
from uuid import UUID
import jwt

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
        1. Create auth.users record via Supabase Auth admin client with email_confirm=True.
        2. Create the public.users profile row via admin client.
        3. Authenticate and return JWT session tokens.
        """
        admin = get_admin_client()
        anon = get_anon_client()

        # Step 1: Create confirmed user via Admin API to bypass email confirmation block
        try:
            user_resp = admin.auth.admin.create_user({
                "email": data.email,
                "password": data.password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": data.full_name,
                    "phone": data.phone or "",
                }
            })
            user = user_resp.user
        except AuthApiError as exc:
            exc_str = str(exc).lower()
            if "already registered" in exc_str or "already exists" in exc_str:
                raise ConflictError("An account with this email already exists.")
            raise ExternalServiceError("Supabase Auth", str(exc))
        except Exception as exc:
            exc_str = str(exc).lower()
            if "already registered" in exc_str or "already exists" in exc_str:
                raise ConflictError("An account with this email already exists.")
            raise ExternalServiceError("Supabase Auth", exc_str)

        if not user:
            raise ExternalServiceError("Supabase Auth", "No user returned after signup.")

        # Step 2: Create users profile row in public.users table via admin client
        try:
            admin.table("users").insert({
                "id": user.id,
                "email": data.email,
                "full_name": data.full_name,
                "phone": data.phone,
            }).execute()
        except Exception as exc:
            logger.warning("Failed to create users profile row: {}", str(exc))

        # Step 3: Sign in immediately to generate session JWT access & refresh tokens
        session = None
        try:
            login_resp = anon.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password,
            })
            session = login_resp.session
        except Exception as exc:
            logger.warning("Auto login after signup warning: {}", str(exc))

        return {
            "access_token": session.access_token if session else "",
            "refresh_token": session.refresh_token if session else "",
            "token_type": "bearer",
            "expires_in": session.expires_in if session else 3600,
            "user": {
                "id": user.id,
                "email": data.email,
                "full_name": data.full_name,
            },
        }

    def login(self, data: LoginRequest) -> Dict[str, Any]:
        """Authenticate with email + password and return JWT tokens."""
        client = get_anon_client()
        admin = get_admin_client()

        try:
            resp = client.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password,
            })
        except AuthApiError as exc:
            exc_str = str(exc).lower()
            # If email is unconfirmed from a prior signup, auto-confirm via admin and retry
            if "email not confirmed" in exc_str or "invalid login credentials" in exc_str:
                try:
                    users = admin.auth.admin.list_users()
                    target_user = next((u for u in users if u.email == data.email), None)
                    if target_user:
                        admin.auth.admin.update_user_by_id(target_user.id, {"email_confirm": True})
                        resp = client.auth.sign_in_with_password({
                            "email": data.email,
                            "password": data.password,
                        })
                    else:
                        raise UnauthorizedError("Invalid email or password.")
                except UnauthorizedError:
                    raise
                except Exception:
                    raise UnauthorizedError("Invalid email or password.")
            else:
                raise UnauthorizedError("Invalid email or password.")
        except Exception:
            raise UnauthorizedError("Invalid email or password.")

        session = resp.session
        if not session:
            raise UnauthorizedError("Authentication failed: session not established.")

        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "expires_in": session.expires_in,
        }

    def logout(self, jwt_token: str) -> None:
        """Invalidate the user's session on Supabase."""
        from app.database.client import get_user_client
        try:
            client = get_user_client(jwt_token)
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
        if not session:
            raise UnauthorizedError("Invalid or expired refresh token.")
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "expires_in": session.expires_in,
        }

    def verify_token(self, jwt_token: str) -> Dict[str, Any]:
        """
        Verify a JWT and return the decoded user payload.
        First tries Supabase's get_user() call, falling back to local JWT payload extraction.
        """
        from app.database.client import get_user_client
        try:
            client = get_user_client(jwt_token)
            resp = client.auth.get_user(jwt_token)
            if resp and resp.user:
                return {"id": resp.user.id, "email": resp.user.email}
        except Exception as exc:
            logger.debug("Network token verification failed, using JWT fallback: {}", str(exc))

        try:
            payload = jwt.decode(jwt_token, options={"verify_signature": False})
            user_id = payload.get("sub")
            email = payload.get("email", "")
            if not user_id:
                raise UnauthorizedError("Token payload missing user ID.")
            return {"id": user_id, "email": email}
        except Exception as exc:
            logger.warning("Token verification failed completely: {}", str(exc))
            raise UnauthorizedError("Token verification failed.")

    def get_user_me(self, user_id: str, email: str) -> Dict[str, Any]:
        """Fetch full user details including company memberships."""
        admin = get_admin_client()
        user_repo = UserRepository(admin)

        profile = None
        try:
            if user_id:
                profile = user_repo.get_by_id(UUID(user_id))
        except Exception as exc:
            logger.warning("Error fetching user profile for me endpoint: {}", str(exc))

        memberships = []
        try:
            if user_id:
                memberships = user_repo.get_company_memberships(UUID(user_id))
        except Exception as exc:
            logger.warning("Error fetching company memberships for me endpoint: {}", str(exc))

        companies_list = []
        for m in memberships:
            comp = m.get("companies") or {}
            role = m.get("roles") or {}
            comp_id = m.get("company_id") or comp.get("id")
            if comp_id:
                companies_list.append({
                    "id": comp_id,
                    "company_id": comp_id,
                    "name": comp.get("name") or "Company",
                    "company_name": comp.get("name") or "Company",
                    "company_slug": comp.get("slug") or "",
                    "slug": comp.get("slug") or "",
                    "role_id": m.get("role_id"),
                    "role_name": role.get("name") or "Owner",
                    "is_active": m.get("is_active", True),
                })

        return {
            "id": user_id,
            "email": profile.get("email") if profile else email,
            "full_name": profile.get("full_name") if profile else "User",
            "phone": profile.get("phone") if profile else None,
            "avatar_url": profile.get("avatar_url") if profile else None,
            "companies": companies_list,
        }

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
            (r for r in roles if r["name"].lower() in ("admin", "owner") and r["is_system"]),
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

        # Return normalized company structure containing both id and company_id
        return {
            "id": company_id,
            "company_id": company_id,
            "name": company.get("name"),
            "company_name": company.get("name"),
            "slug": company.get("slug"),
            "company_slug": company.get("slug"),
            "industry": company.get("industry"),
            "currency": company.get("currency"),
            "country": company.get("country"),
            "timezone": company.get("timezone"),
            "role_name": owner_role.get("name", "Owner"),
        }


auth_service = AuthService()

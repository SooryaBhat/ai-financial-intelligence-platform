"""
FastAPI dependency: authentication.

Provides two dependencies:
  1. get_current_user_raw(request) → raw dict from JWT verification
  2. get_request_context(request) → full RequestContext with company scoping

All protected routes depend on one of these.
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.service import auth_service
from app.core.logging import logger
from app.database.client import get_admin_client, get_user_client
from app.exceptions import ForbiddenError, UnauthorizedError
from app.repositories.users import UserRepository
from app.repositories.roles import RoleRepository
from app.services.context import RequestContext

# HTTPBearer reads the Authorization header and returns the token
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_raw(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """
    Verify the Bearer JWT and return the raw user dict from Supabase.
    Raises UnauthorizedError if no valid token is provided.
    """
    if not credentials or not credentials.credentials:
        raise UnauthorizedError("No authentication token provided.")
    jwt = credentials.credentials
    return auth_service.verify_token(jwt)


def get_request_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
) -> RequestContext:
    """
    Full authenticated context with company scoping.

    Steps:
      1. Verify JWT → get user_id.
      2. Resolve company_id from X-Company-ID header.
      3. Verify user is an active member of that company.
      4. Load user's permissions for RBAC checks.
      5. Return RequestContext.

    Usage:
        @router.get("/")
        def list(ctx: RequestContext = Depends(get_request_context)):
            ...
    """
    if not credentials or not credentials.credentials:
        raise UnauthorizedError("No authentication token provided.")

    jwt = credentials.credentials
    user_data = auth_service.verify_token(jwt)
    user_id = UUID(user_data["id"])

    if not x_company_id:
        raise UnauthorizedError("X-Company-ID header is required.")

    try:
        company_id = UUID(x_company_id)
    except ValueError:
        raise UnauthorizedError("X-Company-ID must be a valid UUID.")

    # Verify membership via admin client (don't trust user RLS here)
    admin = get_admin_client()
    user_repo = UserRepository(admin)
    membership = user_repo.get_company_user(company_id, user_id)

    if not membership or not membership.get("is_active"):
        raise ForbiddenError("You are not an active member of this company.")

    # Load permissions
    role_repo = RoleRepository(admin)
    permissions = role_repo.get_user_permissions(user_id, company_id)
    permission_keys = [
        f"{p['resource']}:{p['action']}" for p in permissions if p
    ]

    # Build user-scoped client for RLS enforcement
    user_client = get_user_client(jwt)

    return RequestContext(
        user_id=user_id,
        company_id=company_id,
        user_client=user_client,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        role_id=UUID(membership["role_id"]) if membership.get("role_id") else None,
        permissions=permission_keys,
    )

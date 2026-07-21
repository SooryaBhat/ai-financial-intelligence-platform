"""
Users router — /api/v1/users
Manages user profiles and company memberships.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_request_context
from app.dependencies.rbac import require_permission
from app.repositories.users import UserRepository
from app.schemas.common import MessageResponse, PaginatedResponse, SuccessResponse
from app.schemas.users import (
    CompanyUserCreate,
    CompanyUserUpdate,
    InviteUserRequest,
    UserResponse,
    UserUpdate,
)
from app.services.context import RequestContext

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=SuccessResponse,
    summary="List all users in the company",
)
def list_users(ctx: RequestContext = Depends(get_request_context)):
    repo = UserRepository(ctx.user_client)
    data = repo.list_company_users(ctx.company_id)
    return SuccessResponse(data=data)


@router.get(
    "/{user_id}",
    response_model=SuccessResponse,
    summary="Get a user profile",
)
def get_user(user_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = UserRepository(ctx.user_client)
    data = repo.get_by_id(user_id)
    return SuccessResponse(data=data)


@router.patch(
    "/me",
    response_model=SuccessResponse,
    summary="Update my profile",
)
def update_me(payload: UserUpdate, ctx: RequestContext = Depends(get_request_context)):
    repo = UserRepository(ctx.user_client)
    data = repo.update(ctx.user_id, payload.model_dump(exclude_none=True))
    return SuccessResponse(data=data)


@router.patch(
    "/{user_id}/membership",
    response_model=SuccessResponse,
    summary="Update user membership (role, branch, active status)",
)
def update_membership(
    user_id: UUID,
    payload: CompanyUserUpdate,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = UserRepository(ctx.user_client)
    membership = repo.get_company_user(ctx.company_id, user_id)
    if not membership:
        from app.exceptions import NotFoundError
        raise NotFoundError("Company membership", str(user_id))
    data = repo.update_company_user(UUID(membership["id"]), payload.model_dump(exclude_none=True))
    return SuccessResponse(data=data)


@router.post(
    "/invite",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a user to the company",
)
def invite_user(
    payload: InviteUserRequest,
    ctx: RequestContext = Depends(get_request_context),
    _: None = Depends(require_permission("users", "invite")),
):
    """
    Send an email invite via Supabase Auth Admin API and create a pending
    company_users membership record. The invited user can then sign up and
    will be automatically linked to the company.
    """
    from app.core.logging import logger
    from app.database.client import get_admin_client
    from app.exceptions import ConflictError

    admin = get_admin_client()
    user_repo = UserRepository(admin)

    # Check if user already has a membership in this company
    existing_user = user_repo.get_by_email(str(payload.email))
    if existing_user:
        membership = user_repo.get_company_user(ctx.company_id, UUID(existing_user["id"]))
        if membership:
            raise ConflictError(
                f"User '{payload.email}' is already a member of this company."
            )

    # Send invite via Supabase Admin (creates auth user + sends magic link)
    try:
        resp = admin.auth.admin.invite_user_by_email(str(payload.email))
        invited_user_id = resp.user.id if resp.user else None
    except Exception as exc:
        logger.warning("Supabase invite failed (user may already exist): {}", str(exc))
        # If user already exists in auth but not in our users table, find or create profile
        if existing_user:
            invited_user_id = existing_user["id"]
        else:
            raise

    # Create company membership for the invited user
    membership_data = {
        "company_id": str(ctx.company_id),
        "user_id": str(invited_user_id),
        "role_id": str(payload.role_id),
        "is_active": False,  # Becomes active once they accept the invite
        "invited_at": "now()",
    }
    if payload.branch_id:
        membership_data["branch_id"] = str(payload.branch_id)

    membership = user_repo.create_company_user(membership_data)
    logger.info(
        "User invited | email={} company={} role={}",
        payload.email, ctx.company_id, payload.role_id,
    )
    return SuccessResponse(data={
        "invited_email": str(payload.email),
        "membership": membership,
    })


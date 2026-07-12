"""
Users router — /api/v1/users
Manages user profiles and company memberships.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_request_context
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

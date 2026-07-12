"""Roles and permissions router — /api/v1/roles"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_request_context
from app.repositories.roles import RoleRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.roles import AssignPermissionsRequest, RoleCreate, RoleResponse, RoleUpdate
from app.services.context import RequestContext

router = APIRouter(prefix="/roles", tags=["Roles & Permissions"])


@router.get("/", response_model=SuccessResponse, summary="List roles for company")
def list_roles(ctx: RequestContext = Depends(get_request_context)):
    repo = RoleRepository(ctx.user_client)
    data = repo.list_for_company(ctx.company_id)
    return SuccessResponse(data=data)


@router.get("/permissions", response_model=SuccessResponse, summary="List all system permissions")
def list_permissions(ctx: RequestContext = Depends(get_request_context)):
    repo = RoleRepository(ctx.user_client)
    data = repo.get_permissions()
    return SuccessResponse(data=data)


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create a role")
def create_role(payload: RoleCreate, ctx: RequestContext = Depends(get_request_context)):
    repo = RoleRepository(ctx.user_client)
    role_data = {
        "company_id": str(ctx.company_id),
        "name": payload.name,
        "description": payload.description,
        "is_system": False,
    }
    role = repo.create(role_data)
    if payload.permission_ids:
        repo.assign_permissions(UUID(role["id"]), payload.permission_ids)
    return SuccessResponse(data=role)


@router.get("/{role_id}", response_model=SuccessResponse, summary="Get role with permissions")
def get_role(role_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = RoleRepository(ctx.user_client)
    data = repo.get_with_permissions(role_id)
    return SuccessResponse(data=data)


@router.patch("/{role_id}", response_model=SuccessResponse, summary="Update role")
def update_role(role_id: UUID, payload: RoleUpdate, ctx: RequestContext = Depends(get_request_context)):
    repo = RoleRepository(ctx.user_client)
    data = repo.update(role_id, payload.model_dump(exclude_none=True), ctx.company_id)
    return SuccessResponse(data=data)


@router.put("/{role_id}/permissions", response_model=SuccessResponse, summary="Assign permissions to role")
def assign_permissions(role_id: UUID, payload: AssignPermissionsRequest, ctx: RequestContext = Depends(get_request_context)):
    repo = RoleRepository(ctx.user_client)
    repo.assign_permissions(role_id, payload.permission_ids)
    return SuccessResponse(data={"message": "Permissions updated."})


@router.delete("/{role_id}", response_model=MessageResponse, summary="Delete role")
def delete_role(role_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = RoleRepository(ctx.user_client)
    repo.hard_delete(role_id, ctx.company_id)
    return MessageResponse(message="Role deleted.")

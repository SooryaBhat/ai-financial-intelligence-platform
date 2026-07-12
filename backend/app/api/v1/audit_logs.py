"""Audit logs router — /api/v1/audit-logs (read-only)"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_request_context
from app.repositories.audit_logs import AuditLogRepository
from app.schemas.common import SuccessResponse
from app.services.context import RequestContext

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("/", response_model=SuccessResponse, summary="List audit logs")
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resource_type: str = Query(None),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = AuditLogRepository(ctx.user_client)
    filters = {"resource_type": resource_type} if resource_type else None
    data = repo.list(ctx.company_id, filters=filters, limit=page_size, offset=(page - 1) * page_size)
    return SuccessResponse(data=data)


@router.get("/{resource_type}/{resource_id}", response_model=SuccessResponse, summary="Get audit history for a resource")
def get_resource_history(
    resource_type: str,
    resource_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = AuditLogRepository(ctx.user_client)
    data = repo.list_for_resource(ctx.company_id, resource_type, resource_id)
    return SuccessResponse(data=data)

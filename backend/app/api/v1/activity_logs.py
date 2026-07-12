"""Activity logs router — /api/v1/activity-logs (read-only)"""
from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_request_context
from app.repositories.activity_logs import ActivityLogRepository
from app.schemas.common import SuccessResponse
from app.services.context import RequestContext

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get("/", response_model=SuccessResponse, summary="List activity logs")
def list_activity_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = ActivityLogRepository(ctx.user_client)
    data = repo.list(ctx.company_id, limit=page_size, offset=(page - 1) * page_size)
    return SuccessResponse(data=data)


@router.get("/me", response_model=SuccessResponse, summary="Get my activity logs")
def my_activity(ctx: RequestContext = Depends(get_request_context)):
    repo = ActivityLogRepository(ctx.user_client)
    data = repo.list_for_user(ctx.company_id, ctx.user_id)
    return SuccessResponse(data=data)

"""Notifications router — /api/v1/notifications"""
from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_request_context
from app.repositories.notifications import NotificationRepository
from app.schemas.common import SuccessResponse
from app.schemas.notifications import MarkReadRequest
from app.services.context import RequestContext
from app.services.notifications import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _get_service(ctx: RequestContext = Depends(get_request_context)) -> NotificationService:
    return NotificationService(NotificationRepository(ctx.user_client))


@router.get("/", response_model=SuccessResponse, summary="List notifications")
def list_notifications(
    unread_only: bool = Query(False),
    ctx: RequestContext = Depends(get_request_context),
    svc: NotificationService = Depends(_get_service),
):
    return SuccessResponse(data=svc.list_for_user(ctx, unread_only))


@router.get("/unread-count", response_model=SuccessResponse, summary="Get unread notification count")
def unread_count(
    ctx: RequestContext = Depends(get_request_context),
    svc: NotificationService = Depends(_get_service),
):
    return SuccessResponse(data={"count": svc.count_unread(ctx)})


@router.post("/mark-read", response_model=SuccessResponse, summary="Mark notifications as read")
def mark_read(
    payload: MarkReadRequest,
    ctx: RequestContext = Depends(get_request_context),
    svc: NotificationService = Depends(_get_service),
):
    svc.mark_read(payload.notification_ids, ctx)
    return SuccessResponse(data={"message": "Notifications marked as read."})

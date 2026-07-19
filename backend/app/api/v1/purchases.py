"""Purchases router — /api/v1/purchases"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_request_context
from app.repositories.purchases import PurchaseRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.purchases import PurchaseCreate, PurchaseUpdate
from app.services.context import RequestContext
from app.services.purchases import PurchaseService

router = APIRouter(prefix="/purchases", tags=["Purchases"])


def _get_service(ctx: RequestContext = Depends(get_request_context)) -> PurchaseService:
    return PurchaseService(PurchaseRepository(ctx.user_client))


@router.get("/", response_model=SuccessResponse, summary="List purchases")
def list_purchases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: RequestContext = Depends(get_request_context),
    svc: PurchaseService = Depends(_get_service),
):
    data = svc.list(ctx, limit=page_size, offset=(page - 1) * page_size)
    return SuccessResponse(data=data)


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create purchase order")
def create_purchase(
    payload: PurchaseCreate,
    ctx: RequestContext = Depends(get_request_context),
    svc: PurchaseService = Depends(_get_service),
):
    data = svc.create(payload, ctx)
    return SuccessResponse(data=data)


@router.get("/{purchase_id}", response_model=SuccessResponse, summary="Get purchase with items")
def get_purchase(
    purchase_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    svc: PurchaseService = Depends(_get_service),
):
    return SuccessResponse(data=svc.get(purchase_id, ctx))


@router.patch("/{purchase_id}", response_model=SuccessResponse, summary="Update purchase order")
def update_purchase(
    purchase_id: UUID,
    payload: PurchaseUpdate,
    ctx: RequestContext = Depends(get_request_context),
    svc: PurchaseService = Depends(_get_service),
):
    return SuccessResponse(data=svc.update(purchase_id, payload, ctx))


@router.delete("/{purchase_id}", response_model=MessageResponse, summary="Cancel / soft-delete purchase")
def delete_purchase(
    purchase_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    svc: PurchaseService = Depends(_get_service),
):
    svc.delete(purchase_id, ctx)
    return MessageResponse(message="Purchase deleted.")

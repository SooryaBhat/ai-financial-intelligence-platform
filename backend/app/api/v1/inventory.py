"""Inventory router — /api/v1/inventory"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_request_context
from app.repositories.inventory import InventoryRepository, StockMovementRepository
from app.schemas.common import SuccessResponse
from app.schemas.inventory import AdjustInventoryRequest, StockMovementCreate
from app.services.context import RequestContext
from app.services.inventory import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


def _get_service(ctx: RequestContext = Depends(get_request_context)) -> InventoryService:
    return InventoryService(
        InventoryRepository(ctx.user_client),
        StockMovementRepository(ctx.user_client),
    )


@router.get("/", response_model=SuccessResponse, summary="List all inventory")
def list_inventory(
    ctx: RequestContext = Depends(get_request_context),
    svc: InventoryService = Depends(_get_service),
):
    return SuccessResponse(data=svc.list_company_inventory(ctx.company_id))


@router.get("/low-stock", response_model=SuccessResponse, summary="List low stock items")
def low_stock(
    ctx: RequestContext = Depends(get_request_context),
    svc: InventoryService = Depends(_get_service),
):
    return SuccessResponse(data=svc.list_low_stock(ctx.company_id))


@router.post("/adjust", response_model=SuccessResponse, summary="Manual stock adjustment")
def adjust_stock(
    payload: AdjustInventoryRequest,
    ctx: RequestContext = Depends(get_request_context),
    svc: InventoryService = Depends(_get_service),
):
    data = svc.adjust_stock(payload, ctx)
    return SuccessResponse(data=data)


@router.get("/movements", response_model=SuccessResponse, summary="List stock movements")
def list_movements(
    product_id: UUID = Query(None),
    limit: int = Query(50, ge=1, le=200),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = StockMovementRepository(ctx.user_client)
    if product_id:
        data = repo.list_by_product(ctx.company_id, product_id, limit)
    else:
        data = repo.list(ctx.company_id, limit=limit, offset=0)
    return SuccessResponse(data=data)

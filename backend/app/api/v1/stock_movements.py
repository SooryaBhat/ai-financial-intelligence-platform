"""
Stock movements router — /api/v1/stock-movements
Standalone router for browsing the stock movement audit log.
Actual stock adjustments are performed via /api/v1/inventory/adjust.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_request_context
from app.repositories.inventory import StockMovementRepository
from app.schemas.common import SuccessResponse
from app.services.context import RequestContext

router = APIRouter(prefix="/stock-movements", tags=["Stock Movements"])


@router.get("/", response_model=SuccessResponse, summary="List all stock movements")
def list_movements(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    product_id: UUID = Query(None),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = StockMovementRepository(ctx.user_client)
    if product_id:
        data = repo.list_by_product(ctx.company_id, product_id, limit=page_size)
    else:
        data = repo.list(ctx.company_id, limit=page_size, offset=(page - 1) * page_size)
    return SuccessResponse(data=data)


@router.get("/{movement_id}", response_model=SuccessResponse, summary="Get stock movement detail")
def get_movement(movement_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = StockMovementRepository(ctx.user_client)
    return SuccessResponse(data=repo.get_by_id(movement_id, ctx.company_id))

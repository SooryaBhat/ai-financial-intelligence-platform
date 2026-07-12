"""Sales router — /api/v1/sales"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_request_context
from app.repositories.inventory import InventoryRepository, StockMovementRepository
from app.repositories.sales import SaleRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.sales import SaleCreate, SaleUpdate
from app.services.context import RequestContext
from app.services.sales import SaleService

router = APIRouter(prefix="/sales", tags=["Sales"])


def _get_service(ctx: RequestContext = Depends(get_request_context)) -> SaleService:
    return SaleService(
        SaleRepository(ctx.user_client),
        InventoryRepository(ctx.user_client),
        StockMovementRepository(ctx.user_client),
    )


@router.get("/", response_model=SuccessResponse, summary="List sales")
def list_sales(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: RequestContext = Depends(get_request_context),
    svc: SaleService = Depends(_get_service),
):
    data = svc.list(ctx, limit=page_size, offset=(page - 1) * page_size)
    return SuccessResponse(data=data)


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create a sale")
def create_sale(
    payload: SaleCreate,
    ctx: RequestContext = Depends(get_request_context),
    svc: SaleService = Depends(_get_service),
):
    data = svc.create(payload, ctx)
    return SuccessResponse(data=data)


@router.get("/{sale_id}", response_model=SuccessResponse, summary="Get sale with items")
def get_sale(
    sale_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    svc: SaleService = Depends(_get_service),
):
    return SuccessResponse(data=svc.get(sale_id, ctx))


@router.patch("/{sale_id}", response_model=SuccessResponse, summary="Update sale status")
def update_sale(
    sale_id: UUID,
    payload: SaleUpdate,
    ctx: RequestContext = Depends(get_request_context),
    svc: SaleService = Depends(_get_service),
):
    return SuccessResponse(data=svc.update_status(sale_id, payload, ctx))


@router.delete("/{sale_id}", response_model=MessageResponse, summary="Cancel / soft-delete a sale")
def delete_sale(
    sale_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    svc: SaleService = Depends(_get_service),
):
    svc.delete(sale_id, ctx)
    return MessageResponse(message="Sale deleted.")

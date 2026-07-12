"""Purchases router — /api/v1/purchases"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_request_context
from app.repositories.purchases import PurchaseRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.purchases import PurchaseCreate, PurchaseUpdate
from app.services.context import RequestContext
from app.core.constants import PurchaseStatus

router = APIRouter(prefix="/purchases", tags=["Purchases"])


@router.get("/", response_model=SuccessResponse, summary="List purchases")
def list_purchases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = PurchaseRepository(ctx.user_client)
    data = repo.list(ctx.company_id, limit=page_size, offset=(page - 1) * page_size)
    return SuccessResponse(data=data)


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create purchase order")
def create_purchase(payload: PurchaseCreate, ctx: RequestContext = Depends(get_request_context)):
    repo = PurchaseRepository(ctx.user_client)
    if repo.get_by_number(ctx.company_id, payload.purchase_number):
        from app.exceptions import ConflictError
        raise ConflictError(f"Purchase number '{payload.purchase_number}' already exists.")
    purchase_data = {
        "company_id": str(ctx.company_id),
        "supplier_id": str(payload.supplier_id) if payload.supplier_id else None,
        "branch_id": str(payload.branch_id) if payload.branch_id else None,
        "purchase_number": payload.purchase_number,
        "purchase_date": payload.purchase_date.isoformat(),
        "expected_delivery": payload.expected_delivery.isoformat() if payload.expected_delivery else None,
        "status": PurchaseStatus.DRAFT.value,
        "subtotal": payload.subtotal,
        "tax_amount": payload.tax_amount,
        "total_amount": payload.total_amount,
        "currency": payload.currency,
        "notes": payload.notes,
        "created_by": str(ctx.user_id),
    }
    items_data = [
        {
            "product_id": str(item.product_id),
            "warehouse_id": str(item.warehouse_id) if item.warehouse_id else None,
            "quantity": item.quantity,
            "unit_cost": item.unit_cost,
            "tax_rate": item.tax_rate,
            "line_total": item.line_total,
            "received_qty": item.received_qty,
        }
        for item in payload.items
    ]
    data = repo.create_with_items(purchase_data, items_data)
    return SuccessResponse(data=data)


@router.get("/{purchase_id}", response_model=SuccessResponse, summary="Get purchase with items")
def get_purchase(purchase_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = PurchaseRepository(ctx.user_client)
    from app.exceptions import NotFoundError
    data = repo.get_with_items(purchase_id, ctx.company_id)
    if not data:
        raise NotFoundError("Purchase", str(purchase_id))
    return SuccessResponse(data=data)


@router.patch("/{purchase_id}", response_model=SuccessResponse, summary="Update purchase")
def update_purchase(
    purchase_id: UUID,
    payload: PurchaseUpdate,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = PurchaseRepository(ctx.user_client)
    data = repo.update(purchase_id, payload.model_dump(exclude_none=True), ctx.company_id)
    return SuccessResponse(data=data)


@router.delete("/{purchase_id}", response_model=MessageResponse, summary="Delete purchase")
def delete_purchase(purchase_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = PurchaseRepository(ctx.user_client)
    repo.soft_delete(purchase_id, ctx.company_id)
    return MessageResponse(message="Purchase deleted.")

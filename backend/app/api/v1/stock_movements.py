"""
Stock movements router — /api/v1/stock-movements
Provides browsing and creation of stock movement audit entries.
Persists movements to Supabase and keeps inventory.quantity strictly synchronized.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.constants import StockMovementType, StockReferenceType
from app.core.logging import logger
from app.dependencies.auth import get_request_context
from app.repositories.inventory import InventoryRepository, StockMovementRepository
from app.schemas.common import SuccessResponse
from app.schemas.inventory import StockMovementCreate
from app.services.audit import audit_service
from app.services.context import RequestContext

router = APIRouter(prefix="/stock-movements", tags=["Stock Movements"])


@router.get("", response_model=SuccessResponse, summary="List all stock movements")
@router.get("/", response_model=SuccessResponse, summary="List all stock movements", include_in_schema=False)
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


@router.post("", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Log a stock movement")
@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Log a stock movement", include_in_schema=False)
def create_movement(
    payload: StockMovementCreate,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Log an authorized stock movement and update product inventory balance in Supabase.
    Enforces tenant scoping, balance sufficiency, and audit logging.
    """
    m_raw = (payload.movement_type or "").strip().upper()

    # 1. Map movement_type to database check constraint & calculate signed quantity delta
    if m_raw in ("IN", "RECEIPT", "RETURN", "TRANSFER_IN"):
        db_movement_type = StockMovementType.RECEIPT.value if m_raw in ("IN", "RECEIPT") else (
            StockMovementType.RETURN.value if m_raw == "RETURN" else StockMovementType.TRANSFER_IN.value
        )
        qty_delta = abs(payload.quantity)
    elif m_raw in ("OUT", "SALE", "TRANSFER_OUT"):
        db_movement_type = StockMovementType.SALE.value if m_raw in ("OUT", "SALE") else StockMovementType.TRANSFER_OUT.value
        qty_delta = -abs(payload.quantity)
    elif m_raw in ("TRANSFER",):
        db_movement_type = StockMovementType.TRANSFER_OUT.value
        qty_delta = -abs(payload.quantity)
    elif m_raw in ("ADJUSTMENT",):
        db_movement_type = StockMovementType.ADJUSTMENT.value
        qty_delta = payload.quantity
    else:
        try:
            db_movement_type = StockMovementType(payload.movement_type.lower()).value
            qty_delta = abs(payload.quantity) if "in" in db_movement_type or db_movement_type in ("receipt", "return") else -abs(payload.quantity)
        except ValueError:
            db_movement_type = StockMovementType.ADJUSTMENT.value
            qty_delta = payload.quantity

    # 2. Check current stock level and enforce non-negative stock balance
    inv_repo = InventoryRepository(ctx.user_client)
    current_stock = inv_repo.get_stock(payload.product_id, payload.warehouse_id)
    current_qty = float(current_stock.get("quantity") or 0.0) if current_stock else 0.0
    new_qty = current_qty + qty_delta

    if new_qty < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient inventory balance. Current available stock: {current_qty}, requested removal: {abs(qty_delta)} units.",
        )

    # 3. Insert stock movement record into database
    movement_repo = StockMovementRepository(ctx.user_client)
    notes_val = payload.notes or payload.reference or f"Stock movement ({payload.movement_type})"
    ref_type_val = payload.reference_type or StockReferenceType.MANUAL.value
    movement_record = {
        "company_id": str(ctx.company_id),
        "product_id": str(payload.product_id),
        "warehouse_id": str(payload.warehouse_id),
        "movement_type": db_movement_type,
        "quantity": qty_delta,
        "reference_type": ref_type_val,
        "reference_id": str(payload.reference_id) if payload.reference_id else None,
        "notes": notes_val,
        "created_by": str(ctx.user_id),
    }

    created = movement_repo.create(movement_record)
    if not created or not created.get("id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist stock movement to database.",
        )

    # 4. Upsert updated balance into inventory table
    reorder_level = float(current_stock.get("reorder_level") or 0.0) if current_stock else 0.0
    inv_data = {
        "company_id": str(ctx.company_id),
        "product_id": str(payload.product_id),
        "warehouse_id": str(payload.warehouse_id),
        "quantity": new_qty,
        "reorder_level": reorder_level,
    }
    inv_repo.upsert_stock(inv_data)

    # 5. Log audit event
    try:
        audit_service.log_create(
            ctx.company_id,
            "stock_movements",
            created["id"],
            created,
            ctx.user_id,
            ctx.ip_address,
            ctx.user_agent,
        )
    except Exception as audit_err:
        logger.warning("Failed to record audit log for stock movement: {}", audit_err)

    created["reference"] = notes_val
    return SuccessResponse(data=created)


@router.get("/{movement_id}", response_model=SuccessResponse, summary="Get stock movement detail")
def get_movement(movement_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = StockMovementRepository(ctx.user_client)
    return SuccessResponse(data=repo.get_by_id(movement_id, ctx.company_id))

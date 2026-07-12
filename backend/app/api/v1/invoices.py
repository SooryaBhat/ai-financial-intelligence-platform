"""Invoices router — /api/v1/invoices"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_request_context
from app.repositories.invoices import InvoiceRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.invoices import InvoiceCreate, InvoiceUpdate
from app.services.context import RequestContext

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("/", response_model=SuccessResponse, summary="List invoices")
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    invoice_type: str = Query(None),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = InvoiceRepository(ctx.user_client)
    filters = {"invoice_type": invoice_type} if invoice_type else None
    data = repo.list(ctx.company_id, filters=filters, limit=page_size, offset=(page - 1) * page_size)
    return SuccessResponse(data=data)


@router.get("/overdue", response_model=SuccessResponse, summary="List overdue invoices")
def list_overdue(ctx: RequestContext = Depends(get_request_context)):
    repo = InvoiceRepository(ctx.user_client)
    return SuccessResponse(data=repo.list_overdue(ctx.company_id))


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create invoice")
def create_invoice(payload: InvoiceCreate, ctx: RequestContext = Depends(get_request_context)):
    repo = InvoiceRepository(ctx.user_client)
    if repo.get_by_number(ctx.company_id, payload.invoice_number):
        from app.exceptions import ConflictError
        raise ConflictError(f"Invoice number '{payload.invoice_number}' already exists.")
    data = payload.model_dump(exclude_none=True)
    data["company_id"] = str(ctx.company_id)
    for uuid_field in ["customer_id", "supplier_id", "sale_id", "purchase_id"]:
        if data.get(uuid_field):
            data[uuid_field] = str(data[uuid_field])
    result = repo.create(data)
    return SuccessResponse(data=result)


@router.get("/{invoice_id}", response_model=SuccessResponse, summary="Get invoice")
def get_invoice(invoice_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = InvoiceRepository(ctx.user_client)
    data = repo.get_by_id(invoice_id, ctx.company_id)
    return SuccessResponse(data=data)


@router.patch("/{invoice_id}", response_model=SuccessResponse, summary="Update invoice")
def update_invoice(
    invoice_id: UUID,
    payload: InvoiceUpdate,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = InvoiceRepository(ctx.user_client)
    data = repo.update(invoice_id, payload.model_dump(exclude_none=True), ctx.company_id)
    return SuccessResponse(data=data)


@router.delete("/{invoice_id}", response_model=MessageResponse, summary="Delete invoice")
def delete_invoice(invoice_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = InvoiceRepository(ctx.user_client)
    repo.soft_delete(invoice_id, ctx.company_id)
    return MessageResponse(message="Invoice deleted.")

"""Payments router — /api/v1/payments"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_request_context
from app.repositories.invoices import InvoiceRepository
from app.repositories.payments import PaymentRepository
from app.schemas.common import SuccessResponse
from app.schemas.payments import PaymentCreate, PaymentUpdate
from app.services.context import RequestContext
from app.services.payments import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


def _get_service(ctx: RequestContext = Depends(get_request_context)) -> PaymentService:
    return PaymentService(
        PaymentRepository(ctx.user_client),
        InvoiceRepository(ctx.user_client),
    )


@router.get("/", response_model=SuccessResponse, summary="List payments")
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: RequestContext = Depends(get_request_context),
    svc: PaymentService = Depends(_get_service),
):
    data = svc.list(ctx, limit=page_size, offset=(page - 1) * page_size)
    return SuccessResponse(data=data)


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Record a payment")
def create_payment(
    payload: PaymentCreate,
    ctx: RequestContext = Depends(get_request_context),
    svc: PaymentService = Depends(_get_service),
):
    data = svc.create(payload, ctx)
    return SuccessResponse(data=data)


@router.get("/{payment_id}", response_model=SuccessResponse, summary="Get payment")
def get_payment(payment_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = PaymentRepository(ctx.user_client)
    data = repo.get_by_id(payment_id, ctx.company_id)
    return SuccessResponse(data=data)


@router.get("/by-invoice/{invoice_id}", response_model=SuccessResponse, summary="List payments for an invoice")
def payments_by_invoice(
    invoice_id: UUID,
    svc: PaymentService = Depends(_get_service),
):
    return SuccessResponse(data=svc.list_by_invoice(invoice_id))

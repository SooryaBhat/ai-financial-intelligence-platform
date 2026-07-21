"""
Payments service — processes payments against invoices and updates invoice status.
"""
from typing import Any, Dict, List
from uuid import UUID

from app.exceptions import ValidationError
from app.repositories.invoices import InvoiceRepository
from app.repositories.payments import PaymentRepository
from app.schemas.payments import PaymentCreate, PaymentUpdate
from app.services.audit import audit_service
from app.services.context import RequestContext
from app.core.constants import InvoiceStatus


class PaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        invoice_repo: InvoiceRepository,
    ) -> None:
        self._payments = payment_repo
        self._invoices = invoice_repo

    def list(self, ctx: RequestContext, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        return self._payments.list(ctx.company_id, limit=limit, offset=offset)

    def list_by_invoice(self, invoice_id: UUID) -> List[Dict[str, Any]]:
        return self._payments.list_by_invoice(invoice_id)

    def create(self, data: PaymentCreate, ctx: RequestContext) -> Dict[str, Any]:
        # Validate invoice exists and belongs to company
        invoice = self._invoices.get_by_id(data.invoice_id, ctx.company_id)
        if invoice["status"] in (InvoiceStatus.CANCELLED.value, InvoiceStatus.PAID.value):
            raise ValidationError(f"Cannot add payment to invoice with status '{invoice['status']}'.")

        payment_data = {
            "company_id": str(ctx.company_id),
            "invoice_id": str(data.invoice_id),
            "payment_date": data.payment_date.isoformat(),
            "amount": data.amount,
            "payment_method": data.payment_method.value if data.payment_method else None,
            "reference": data.reference,
            "currency": data.currency,
            "exchange_rate": data.exchange_rate,
            "notes": data.notes,
            "created_by": str(ctx.user_id),
        }
        payment = self._payments.create(payment_data)

        # Recalculate total paid and update invoice status
        total_paid = self._payments.sum_payments_for_invoice(data.invoice_id)
        new_status = self._compute_invoice_status(invoice, total_paid)
        self._invoices.update_amount_paid(data.invoice_id, ctx.company_id, total_paid)
        if new_status != invoice["status"]:
            self._invoices.update(data.invoice_id, {"status": new_status}, ctx.company_id)

        audit_service.log_create(ctx.company_id, "payment", UUID(payment["id"]),
                                  payment, ctx.user_id, ctx.ip_address, ctx.user_agent)
        return payment

    def _compute_invoice_status(self, invoice: Dict, total_paid: float) -> str:
        total = invoice["total_amount"]
        if total_paid >= total:
            return InvoiceStatus.PAID.value
        elif total_paid > 0:
            return InvoiceStatus.PARTIAL.value
        return invoice["status"]

    def update(self, payment_id: UUID, data: PaymentUpdate, ctx: RequestContext) -> Dict[str, Any]:
        """Partially update a payment record and write an audit entry."""
        old = self._payments.get_by_id(payment_id, ctx.company_id)
        update_payload = {k: v for k, v in data.model_dump(exclude_none=True).items()}
        # Convert enum values if present
        if "payment_method" in update_payload and hasattr(update_payload["payment_method"], "value"):
            update_payload["payment_method"] = update_payload["payment_method"].value
        updated = self._payments.update(payment_id, update_payload, ctx.company_id)
        audit_service.log_update(
            ctx.company_id, "payment", payment_id,
            old, updated, ctx.user_id, ctx.ip_address, ctx.user_agent,
        )
        return updated


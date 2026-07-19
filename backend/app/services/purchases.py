"""
Purchase service — business logic for creating and managing purchase orders.
Handles: stock receipt, audit logging.
"""
from typing import Any, Dict, List
from uuid import UUID

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.repositories.purchases import PurchaseRepository
from app.schemas.purchases import PurchaseCreate, PurchaseUpdate
from app.services.audit import audit_service
from app.services.context import RequestContext
from app.core.constants import PurchaseStatus
from app.core.logging import logger


class PurchaseService:
    def __init__(self, purchase_repo: PurchaseRepository) -> None:
        self._purchases = purchase_repo

    def get(self, purchase_id: UUID, ctx: RequestContext) -> Dict[str, Any]:
        """Fetch a single purchase with its line items."""
        purchase = self._purchases.get_with_items(purchase_id, ctx.company_id)
        if not purchase:
            raise NotFoundError("Purchase", str(purchase_id))
        return purchase

    def list(self, ctx: RequestContext, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """List all purchases for the company."""
        return self._purchases.list(ctx.company_id, limit=limit, offset=offset)

    def create(self, data: PurchaseCreate, ctx: RequestContext) -> Dict[str, Any]:
        """
        Create a purchase order with line items.
        Validates: no duplicate purchase_number.
        """
        if self._purchases.get_by_number(ctx.company_id, data.purchase_number):
            raise ConflictError(f"Purchase number '{data.purchase_number}' already exists.")

        purchase_data = {
            "company_id": str(ctx.company_id),
            "supplier_id": str(data.supplier_id) if data.supplier_id else None,
            "branch_id": str(data.branch_id) if data.branch_id else None,
            "purchase_number": data.purchase_number,
            "purchase_date": data.purchase_date.isoformat(),
            "expected_delivery": data.expected_delivery.isoformat() if data.expected_delivery else None,
            "status": PurchaseStatus.DRAFT.value,
            "subtotal": data.subtotal,
            "tax_amount": data.tax_amount,
            "total_amount": data.total_amount,
            "currency": data.currency,
            "notes": data.notes,
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
            for item in data.items
        ]

        purchase = self._purchases.create_with_items(purchase_data, items_data)
        logger.info("Purchase created | company={} number={}", ctx.company_id, data.purchase_number)
        audit_service.log_create(
            ctx.company_id, "purchase", UUID(purchase["id"]),
            purchase, ctx.user_id, ctx.ip_address, ctx.user_agent,
        )
        return purchase

    def update(self, purchase_id: UUID, data: PurchaseUpdate, ctx: RequestContext) -> Dict[str, Any]:
        """Update purchase status or metadata. Cannot update a received/cancelled order."""
        old = self._purchases.get_by_id(purchase_id, ctx.company_id)
        if old.get("status") in (PurchaseStatus.RECEIVED.value, PurchaseStatus.CANCELLED.value):
            raise ValidationError(
                f"Cannot update a purchase in '{old['status']}' status."
            )
        update_data = {k: v for k, v in data.model_dump(exclude_none=True).items()}
        # Convert enum values
        if "status" in update_data and hasattr(update_data["status"], "value"):
            update_data["status"] = update_data["status"].value

        updated = self._purchases.update(purchase_id, update_data, ctx.company_id)
        audit_service.log_update(
            ctx.company_id, "purchase", purchase_id,
            old, updated, ctx.user_id, ctx.ip_address, ctx.user_agent,
        )
        return updated

    def delete(self, purchase_id: UUID, ctx: RequestContext) -> bool:
        """Soft-delete a purchase order. Cannot delete received orders."""
        old = self._purchases.get_by_id(purchase_id, ctx.company_id)
        if old.get("status") == PurchaseStatus.RECEIVED.value:
            raise ValidationError("Cannot delete a received purchase order.")
        result = self._purchases.soft_delete(purchase_id, ctx.company_id)
        audit_service.log_delete(
            ctx.company_id, "purchase", purchase_id,
            old, ctx.user_id, ctx.ip_address, ctx.user_agent,
        )
        return result

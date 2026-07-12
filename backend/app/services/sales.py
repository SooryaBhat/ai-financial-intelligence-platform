"""
Sales service — business logic for creating and managing sales.
Handles: stock deduction, invoice auto-creation, audit logging.
"""
from typing import Any, Dict, List
from uuid import UUID

from app.exceptions import ConflictError, ValidationError
from app.repositories.inventory import InventoryRepository, StockMovementRepository
from app.repositories.sales import SaleRepository
from app.schemas.sales import SaleCreate, SaleUpdate
from app.services.audit import audit_service
from app.services.context import RequestContext
from app.core.constants import SaleStatus, StockMovementType, StockReferenceType


class SaleService:
    def __init__(
        self,
        sale_repo: SaleRepository,
        inventory_repo: InventoryRepository,
        movement_repo: StockMovementRepository,
    ) -> None:
        self._sales = sale_repo
        self._inventory = inventory_repo
        self._movements = movement_repo

    def get(self, sale_id: UUID, ctx: RequestContext) -> Dict[str, Any]:
        from app.exceptions import NotFoundError
        sale = self._sales.get_with_items(sale_id, ctx.company_id)
        if not sale:
            raise NotFoundError("Sale", str(sale_id))
        return sale

    def list(self, ctx: RequestContext, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        return self._sales.list(ctx.company_id, limit=limit, offset=offset)

    def create(self, data: SaleCreate, ctx: RequestContext) -> Dict[str, Any]:
        # Check for duplicate sale number
        if self._sales.get_by_number(ctx.company_id, data.sale_number):
            raise ConflictError(f"Sale number '{data.sale_number}' already exists.")

        sale_data = {
            "company_id": str(ctx.company_id),
            "customer_id": str(data.customer_id) if data.customer_id else None,
            "branch_id": str(data.branch_id) if data.branch_id else None,
            "sale_number": data.sale_number,
            "sale_date": data.sale_date.isoformat(),
            "status": SaleStatus.DRAFT.value,
            "subtotal": data.subtotal,
            "discount_amount": data.discount_amount,
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
                "unit_price": item.unit_price,
                "discount_pct": item.discount_pct,
                "tax_rate": item.tax_rate,
                "line_total": item.line_total,
            }
            for item in data.items
        ]
        sale = self._sales.create_with_items(sale_data, items_data)
        audit_service.log_create(ctx.company_id, "sale", UUID(sale["id"]),
                                  sale, ctx.user_id, ctx.ip_address, ctx.user_agent)
        return sale

    def update_status(self, sale_id: UUID, data: SaleUpdate, ctx: RequestContext) -> Dict[str, Any]:
        old = self._sales.get_by_id(sale_id, ctx.company_id)
        updated = self._sales.update(sale_id, data.model_dump(exclude_none=True), ctx.company_id)
        audit_service.log_update(ctx.company_id, "sale", sale_id,
                                  old, updated, ctx.user_id, ctx.ip_address, ctx.user_agent)
        return updated

    def delete(self, sale_id: UUID, ctx: RequestContext) -> bool:
        old = self._sales.get_by_id(sale_id, ctx.company_id)
        if old.get("status") == SaleStatus.DELIVERED.value:
            raise ValidationError("Cannot delete a delivered sale.")
        result = self._sales.soft_delete(sale_id, ctx.company_id)
        audit_service.log_delete(ctx.company_id, "sale", sale_id,
                                  old, ctx.user_id, ctx.ip_address, ctx.user_agent)
        return result

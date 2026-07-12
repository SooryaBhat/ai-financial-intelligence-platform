"""
Inventory service — manages stock levels and stock movements.
Enforces the rule: inventory.quantity is always derived from stock_movements.
"""
from typing import Any, Dict, List
from uuid import UUID

from app.exceptions import ValidationError
from app.repositories.inventory import InventoryRepository, StockMovementRepository
from app.schemas.inventory import AdjustInventoryRequest, StockMovementCreate
from app.services.audit import audit_service
from app.services.context import RequestContext


class InventoryService:
    def __init__(
        self,
        inventory_repo: InventoryRepository,
        movement_repo: StockMovementRepository,
    ) -> None:
        self._inventory = inventory_repo
        self._movements = movement_repo

    def get_stock(self, product_id: UUID, warehouse_id: UUID) -> Dict[str, Any]:
        stock = self._inventory.get_stock(product_id, warehouse_id)
        return stock or {"quantity": 0, "reorder_level": 0}

    def list_company_inventory(self, company_id: UUID) -> List[Dict[str, Any]]:
        return self._inventory.list_by_company(company_id)

    def list_low_stock(self, company_id: UUID) -> List[Dict[str, Any]]:
        return self._inventory.list_low_stock(company_id)

    def adjust_stock(
        self, req: AdjustInventoryRequest, ctx: RequestContext
    ) -> Dict[str, Any]:
        """Create a stock movement and update the inventory balance."""
        # Get current stock
        current = self._inventory.get_stock(req.product_id, req.warehouse_id)
        current_qty = current["quantity"] if current else 0

        new_qty = current_qty + req.quantity_delta
        if new_qty < 0:
            raise ValidationError(
                message=f"Insufficient stock. Current quantity: {current_qty}, requested change: {req.quantity_delta}"
            )

        # Record movement
        from app.core.constants import StockMovementType, StockReferenceType
        movement_type = (
            StockMovementType.ADJUSTMENT
        )
        movement_data = {
            "company_id": str(ctx.company_id),
            "product_id": str(req.product_id),
            "warehouse_id": str(req.warehouse_id),
            "movement_type": movement_type.value,
            "quantity": req.quantity_delta,
            "reference_type": StockReferenceType.MANUAL.value,
            "notes": req.notes,
            "created_by": str(ctx.user_id),
        }
        self._movements.create(movement_data)

        # Update inventory balance
        inventory_data = {
            "company_id": str(ctx.company_id),
            "product_id": str(req.product_id),
            "warehouse_id": str(req.warehouse_id),
            "quantity": new_qty,
            "reorder_level": current["reorder_level"] if current else 0,
        }
        updated = self._inventory.upsert_stock(inventory_data)

        audit_service.log_update(
            ctx.company_id, "inventory", req.product_id,
            {"quantity": current_qty}, {"quantity": new_qty},
            ctx.user_id, ctx.ip_address, ctx.user_agent
        )
        return updated

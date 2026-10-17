"""Inventory and stock movements repository."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.database.retry import execute_with_retry
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "inventory")

    def get_stock(self, product_id: UUID, warehouse_id: UUID) -> Optional[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("product_id", str(product_id))
            .eq("warehouse_id", str(warehouse_id))
            .execute()
        )
        return response.data[0] if response.data else None

    def list_by_company(self, company_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*, products(name, sku, unit), warehouses(name)")
            .eq("company_id", str(company_id))
            .execute()
        )
        return response.data or []

    def list_low_stock(self, company_id: UUID) -> List[Dict[str, Any]]:
        """Return inventory rows where quantity <= reorder_level."""
        response = (
            self._query()
            .select("*, products(name, sku), warehouses(name)")
            .eq("company_id", str(company_id))
            .execute()
        )
        # Filter in Python since PostgREST doesn't support column-to-column comparisons
        data = response.data or []
        return [row for row in data if row["quantity"] <= row["reorder_level"]]

    def upsert_stock(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update the inventory balance for a product-warehouse pair."""
        response = (
            self._query()
            .upsert(data, on_conflict="product_id,warehouse_id")
            .execute()
        )
        return response.data[0] if response.data else {}


class StockMovementRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "stock_movements")

    def list(
        self,
        company_id: Optional[UUID] = None,
        filters: Optional[Dict[str, Any]] = None,
        search_column: Optional[str] = None,
        search_value: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        ascending: bool = False,
        include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        query = (
            self._query()
            .select("*, products(name, sku), warehouses(name)")
            .eq("company_id", str(company_id))
            .order(order_by, desc=not ascending)
            .range(offset, offset + limit - 1)
        )
        res = execute_with_retry(query)
        data = res.data or []
        for row in data:
            if "products" in row and "product" not in row:
                row["product"] = row["products"]
            if "warehouses" in row and "warehouse" not in row:
                row["warehouse"] = row["warehouses"]
            if not row.get("reference") and row.get("notes"):
                row["reference"] = row["notes"]
        return data

    def list_by_product(self, company_id: UUID, product_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        query = (
            self._query()
            .select("*, products(name, sku), warehouses(name)")
            .eq("company_id", str(company_id))
            .eq("product_id", str(product_id))
            .order("created_at", desc=True)
            .limit(limit)
        )
        res = execute_with_retry(query)
        data = res.data or []
        for row in data:
            if "products" in row and "product" not in row:
                row["product"] = row["products"]
            if "warehouses" in row and "warehouse" not in row:
                row["warehouse"] = row["warehouses"]
            if not row.get("reference") and row.get("notes"):
                row["reference"] = row["notes"]
        return data

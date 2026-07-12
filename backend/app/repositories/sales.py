"""Sales repository."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class SaleRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "sales")

    def get_with_items(self, sale_id: UUID, company_id: UUID) -> Optional[Dict[str, Any]]:
        response = (
            self._query()
            .select("*, sale_items(*), customers(name, email)")
            .eq("id", str(sale_id))
            .eq("company_id", str(company_id))
            .is_("deleted_at", "null")
            .single()
            .execute()
        )
        return response.data

    def create_with_items(self, sale_data: Dict[str, Any], items: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Insert sale header
        sale_response = self._query().insert(sale_data).execute()
        sale = sale_response.data[0]
        # Insert line items
        for item in items:
            item["sale_id"] = sale["id"]
        self.client.table("sale_items").insert(items).execute()
        return sale

    def get_by_number(self, company_id: UUID, sale_number: str) -> Optional[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("sale_number", sale_number)
            .execute()
        )
        return response.data[0] if response.data else None

    def list_by_customer(self, company_id: UUID, customer_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("customer_id", str(customer_id))
            .is_("deleted_at", "null")
            .order("sale_date", desc=True)
            .execute()
        )
        return response.data or []

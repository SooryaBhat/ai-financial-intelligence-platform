"""Purchases repository."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class PurchaseRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "purchases")

    def get_with_items(self, purchase_id: UUID, company_id: UUID) -> Optional[Dict[str, Any]]:
        response = (
            self._query()
            .select("*, purchase_items(*), suppliers(name, email)")
            .eq("id", str(purchase_id))
            .eq("company_id", str(company_id))
            .is_("deleted_at", "null")
            .single()
            .execute()
        )
        return response.data

    def create_with_items(self, purchase_data: Dict[str, Any], items: List[Dict[str, Any]]) -> Dict[str, Any]:
        purchase_response = self._query().insert(purchase_data).execute()
        purchase = purchase_response.data[0]
        for item in items:
            item["purchase_id"] = purchase["id"]
        self.client.table("purchase_items").insert(items).execute()
        return purchase

    def get_by_number(self, company_id: UUID, purchase_number: str) -> Optional[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("purchase_number", purchase_number)
            .execute()
        )
        return response.data[0] if response.data else None

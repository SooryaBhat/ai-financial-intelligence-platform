"""Suppliers repository."""
from typing import List, Dict, Any
from supabase import Client
from app.repositories.base import BaseRepository


class SupplierRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "suppliers")

    def search(self, company_id, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .is_("deleted_at", "null")
            .or_(f"name.ilike.%{query}%,email.ilike.%{query}%")
            .limit(limit)
            .execute()
        )
        return response.data or []

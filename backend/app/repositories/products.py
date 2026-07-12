"""Products repository."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from supabase import Client
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "products")

    def get_by_sku(self, company_id: UUID, sku: str) -> Optional[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("sku", sku)
            .is_("deleted_at", "null")
            .execute()
        )
        return response.data[0] if response.data else None

    def search(self, company_id: UUID, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .is_("deleted_at", "null")
            .or_(f"name.ilike.%{query}%,sku.ilike.%{query}%,description.ilike.%{query}%")
            .limit(limit)
            .execute()
        )
        return response.data or []

    def list_active(self, company_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("is_active", True)
            .is_("deleted_at", "null")
            .order("name")
            .execute()
        )
        return response.data or []

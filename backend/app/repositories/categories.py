"""Categories repository."""
from typing import List, Dict, Any
from uuid import UUID
from supabase import Client
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "categories")

    def list_by_type(self, company_id: UUID, category_type: str) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("type", category_type)
            .is_("deleted_at", "null")
            .order("name")
            .execute()
        )
        return response.data or []

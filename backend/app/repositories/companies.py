"""Companies repository."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "companies")

    def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        response = self._query().select("*").eq("slug", slug).is_("deleted_at", "null").execute()
        return response.data[0] if response.data else None

    def get_with_plan(self, company_id: UUID) -> Optional[Dict[str, Any]]:
        try:
            response = (
                self._query()
                .select("*, plans(*)")
                .eq("id", str(company_id))
                .is_("deleted_at", "null")
                .single()
                .execute()
            )
            return response.data
        except Exception as exc:
            # PostgREST PGRST116 = "The result contains 0 rows" (not found)
            if "PGRST116" in str(exc) or "0 rows" in str(exc):
                return None
            raise

    def list_companies(
        self,
        search_column: Optional[str] = None,
        search_value: Optional[str] = None,
        order_by: str = "created_at",
        ascending: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query = self._query().select("*").is_("deleted_at", "null")
        if search_column and search_value:
            query = query.ilike(search_column, f"%{search_value}%")
        query = query.order(order_by, desc=not ascending)
        query = query.range(offset, offset + limit - 1)
        response = query.execute()
        return response.data or []

    def count_companies(
        self,
        search_column: Optional[str] = None,
        search_value: Optional[str] = None,
    ) -> int:
        query = self._query().select("id", count="exact").is_("deleted_at", "null")
        if search_column and search_value:
            query = query.ilike(search_column, f"%{search_value}%")
        response = query.execute()
        return response.count or 0

    def list_all(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Admin: list all companies (bypasses company scoping)."""
        response = (
            self._query()
            .select("*")
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return response.data or []


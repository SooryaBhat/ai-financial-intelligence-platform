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

"""ML Models repository."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class MLModelRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "ml_models")

    def list_available(self, company_id: UUID) -> List[Dict[str, Any]]:
        """Return company-specific + platform-wide (company_id IS NULL) active models."""
        response = (
            self._query()
            .select("*")
            .eq("is_active", True)
            .or_(f"company_id.eq.{company_id},company_id.is.null")
            .execute()
        )
        return response.data or []

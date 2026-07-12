"""Settings repository (key-value per company)."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "settings")

    def get_by_key(self, company_id: UUID, key: str) -> Optional[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("key", key)
            .execute()
        )
        return response.data[0] if response.data else None

    def upsert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = (
            self._query()
            .upsert(data, on_conflict="company_id,key")
            .execute()
        )
        return response.data[0] if response.data else {}

    def list_all(self, company_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .order("key")
            .execute()
        )
        return response.data or []

"""Activity logs repository (append-only)."""
from typing import Any, Dict, List
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class ActivityLogRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "activity_logs")

    def create_log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self._query().insert(data).execute()
        return response.data[0] if response.data else {}

    def list_for_user(self, company_id: UUID, user_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

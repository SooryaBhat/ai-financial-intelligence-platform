"""Plans repository (read-mostly — admin creates plans, companies subscribe)."""
from typing import Any, Dict, List
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "plans")

    def list_active(self) -> List[Dict[str, Any]]:
        response = self._query().select("*").eq("is_active", True).order("price_monthly").execute()
        return response.data or []

    def get_subscriptions(self, company_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self.client.table("subscriptions")
            .select("*, plans(*)")
            .eq("company_id", str(company_id))
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def create_subscription(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.table("subscriptions").insert(data).execute()
        return response.data[0] if response.data else {}

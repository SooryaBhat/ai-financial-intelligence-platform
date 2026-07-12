"""Users repository."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "users")

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        response = self._query().select("*").eq("email", email).is_("deleted_at", "null").execute()
        return response.data[0] if response.data else None

    def get_company_memberships(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Return all company memberships for a user with company and role details."""
        response = (
            self.client.table("company_users")
            .select("*, companies(*), roles(*)")
            .eq("user_id", str(user_id))
            .eq("is_active", True)
            .execute()
        )
        return response.data or []

    def get_company_user(self, company_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        response = (
            self.client.table("company_users")
            .select("*")
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return response.data[0] if response.data else None

    def list_company_users(self, company_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self.client.table("company_users")
            .select("*, users(*), roles(*)")
            .eq("company_id", str(company_id))
            .eq("is_active", True)
            .execute()
        )
        return response.data or []

    def create_company_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.table("company_users").insert(data).execute()
        return response.data[0] if response.data else {}

    def update_company_user(self, cu_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        response = (
            self.client.table("company_users")
            .update({k: v for k, v in data.items() if v is not None})
            .eq("id", str(cu_id))
            .execute()
        )
        return response.data[0] if response.data else {}

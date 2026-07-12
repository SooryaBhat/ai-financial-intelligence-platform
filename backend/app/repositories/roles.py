"""Roles and permissions repository."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "roles")

    def get_with_permissions(self, role_id: UUID) -> Optional[Dict[str, Any]]:
        response = (
            self._query()
            .select("*, role_permissions(permissions(*))")
            .eq("id", str(role_id))
            .single()
            .execute()
        )
        return response.data

    def list_for_company(self, company_id: UUID) -> List[Dict[str, Any]]:
        """Return both system roles (company_id IS NULL) and company-specific roles."""
        response = (
            self._query()
            .select("*")
            .or_(f"company_id.eq.{company_id},company_id.is.null")
            .execute()
        )
        return response.data or []

    def get_permissions(self) -> List[Dict[str, Any]]:
        response = self.client.table("permissions").select("*").order("resource").execute()
        return response.data or []

    def assign_permissions(self, role_id: UUID, permission_ids: List[UUID]) -> None:
        # Remove existing assignments
        self.client.table("role_permissions").delete().eq("role_id", str(role_id)).execute()
        # Insert new ones
        if permission_ids:
            rows = [{"role_id": str(role_id), "permission_id": str(pid)} for pid in permission_ids]
            self.client.table("role_permissions").insert(rows).execute()

    def get_user_permissions(self, user_id: UUID, company_id: UUID) -> List[Dict[str, Any]]:
        """
        Return all permissions for the user's role in the given company.
        Joins: company_users → roles → role_permissions → permissions
        """
        response = (
            self.client.table("company_users")
            .select("roles(role_permissions(permissions(*)))")
            .eq("user_id", str(user_id))
            .eq("company_id", str(company_id))
            .eq("is_active", True)
            .single()
            .execute()
        )
        if not response.data:
            return []
        # Flatten nested structure
        try:
            role_perms = response.data["roles"]["role_permissions"]
            return [rp["permissions"] for rp in role_perms if rp.get("permissions")]
        except (KeyError, TypeError):
            return []

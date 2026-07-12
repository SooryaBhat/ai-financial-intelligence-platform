"""Audit logs repository (append-only)."""
from typing import Any, Dict, List
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "audit_logs")

    def create_log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self._query().insert(data).execute()
        return response.data[0] if response.data else {}

    def list_for_resource(self, company_id: UUID, resource_type: str, resource_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("resource_type", resource_type)
            .eq("resource_id", str(resource_id))
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

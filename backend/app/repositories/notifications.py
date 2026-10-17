"""Notifications repository."""
from typing import Any, Dict, List
from uuid import UUID

from supabase import Client

from app.database.retry import execute_with_retry
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "notifications")

    def list_for_user(self, company_id: UUID, user_id: UUID, unread_only: bool = False) -> List[Dict[str, Any]]:
        query = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
        )
        if unread_only:
            query = query.eq("is_read", False)
        response = execute_with_retry(query)
        return response.data or []

    def mark_read(self, notification_ids: List[UUID], user_id: UUID) -> None:
        execute_with_retry(
            self._query()
            .update({"is_read": True})
            .in_("id", [str(nid) for nid in notification_ids])
            .eq("user_id", str(user_id))
        )

    def count_unread(self, company_id: UUID, user_id: UUID) -> int:
        query = (
            self._query()
            .select("id", count="exact")
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .eq("is_read", False)
        )
        response = execute_with_retry(query)
        return response.count or 0

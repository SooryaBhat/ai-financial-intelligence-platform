"""Notifications repository."""
from typing import Any, Dict, List
from uuid import UUID

from supabase import Client

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
        response = query.execute()
        return response.data or []

    def mark_read(self, notification_ids: List[UUID], user_id: UUID) -> None:
        self._query().update({"is_read": True}).in_(
            "id", [str(nid) for nid in notification_ids]
        ).eq("user_id", str(user_id)).execute()

    def count_unread(self, company_id: UUID, user_id: UUID) -> int:
        response = (
            self._query()
            .select("id", count="exact")
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .eq("is_read", False)
            .execute()
        )
        return response.count or 0

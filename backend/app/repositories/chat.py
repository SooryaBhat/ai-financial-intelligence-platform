"""Chat sessions and messages repository."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "chat_sessions")

    def list_user_sessions(self, company_id: UUID, user_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .is_("deleted_at", "null")
            .order("updated_at", desc=True)
            .execute()
        )
        return response.data or []


class ChatMessageRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "chat_messages")

    def list_session_messages(self, session_id: UUID, limit: int = 100) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("session_id", str(session_id))
            .order("created_at")
            .limit(limit)
            .execute()
        )
        return response.data or []

    def create_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self._query().insert(data).execute()
        return response.data[0] if response.data else {}

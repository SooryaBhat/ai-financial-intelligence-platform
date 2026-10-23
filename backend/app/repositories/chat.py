"""Chat sessions, messages, and cross-conversation AI memory repository."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.core.logging import logger
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "chat_sessions")

    def list_user_sessions(
        self,
        company_id: UUID,
        user_id: UUID,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .is_("deleted_at", "null")
            .order("updated_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        if search and search.strip():
            query = query.ilike("title", f"%{search.strip()}%")

        response = query.execute()
        return response.data or []

    def get_user_session(
        self,
        session_id: Any,
        company_id: UUID,
        user_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("id", str(session_id))
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .is_("deleted_at", "null")
            .execute()
        )
        return response.data[0] if response.data else None

    def update_session(
        self,
        session_id: Any,
        company_id: UUID,
        user_id: UUID,
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        data["updated_at"] = datetime.utcnow().isoformat()
        response = (
            self._query()
            .update(data)
            .eq("id", str(session_id))
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return response.data[0] if response.data else None

    def delete_session(
        self,
        session_id: Any,
        company_id: UUID,
        user_id: UUID,
    ) -> bool:
        # Soft delete session
        now = datetime.utcnow().isoformat()
        response = (
            self._query()
            .update({"deleted_at": now, "is_active": False, "updated_at": now})
            .eq("id", str(session_id))
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return bool(response.data)


class ChatMessageRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "chat_messages")

    def list_session_messages(
        self,
        session_id: Any,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("session_id", str(session_id))
            .order("created_at", desc=False)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return response.data or []

    def get_recent_messages(
        self,
        session_id: Any,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Retrieve latest N messages in chronological order."""
        # Query newest messages descending, then reverse so they are chronological
        response = (
            self._query()
            .select("*")
            .eq("session_id", str(session_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        messages = response.data or []
        messages.reverse()
        return messages

    def count_session_messages(self, session_id: Any) -> int:
        response = (
            self._query()
            .select("id", count="exact")
            .eq("session_id", str(session_id))
            .execute()
        )
        return response.count or len(response.data or [])

    def create_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = self._query().insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception:
            # Fallback if metadata column is omitted in remote DB table
            if "metadata" in data:
                fallback_data = {k: v for k, v in data.items() if k != "metadata"}
                response = self._query().insert(fallback_data).execute()
                return response.data[0] if response.data else {}
            raise


class AIMemoryRepository(BaseRepository):
    """Repository for user/company scoped long-term AI memory records."""

    def __init__(self, client: Client) -> None:
        super().__init__(client, "ai_memories")

    def list_memories(
        self,
        company_id: UUID,
        user_id: UUID,
        active_only: bool = True,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        query = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .limit(limit)
        )
        if active_only:
            query = query.eq("is_active", True)
        if category and category.strip():
            query = query.eq("category", category.strip())
        if search and search.strip():
            query = query.ilike("content", f"%{search.strip()}%")

        response = query.execute()
        return response.data or []

    def get_memory(
        self,
        memory_id: UUID,
        company_id: UUID,
        user_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("id", str(memory_id))
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return response.data[0] if response.data else None

    def create_memory(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        response = self._query().insert(data).execute()
        return response.data[0] if response.data else {}

    def update_memory(
        self,
        memory_id: UUID,
        company_id: UUID,
        user_id: UUID,
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        data["updated_at"] = datetime.utcnow().isoformat()
        response = (
            self._query()
            .update(data)
            .eq("id", str(memory_id))
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return response.data[0] if response.data else None

    def delete_memory(
        self,
        memory_id: UUID,
        company_id: UUID,
        user_id: UUID,
    ) -> bool:
        response = (
            self._query()
            .delete()
            .eq("id", str(memory_id))
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return bool(response.data)

    def clear_all_memories(
        self,
        company_id: UUID,
        user_id: UUID,
    ) -> int:
        response = (
            self._query()
            .delete()
            .eq("company_id", str(company_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return len(response.data or [])

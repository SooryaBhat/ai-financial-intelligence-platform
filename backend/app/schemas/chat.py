"""Chat sessions and messages schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import ChatRole
from app.schemas.common import AppBaseModel, TimestampMixin


# ── Chat Sessions ─────────────────────────────────────────────

class ChatSessionCreate(AppBaseModel):
    title: Optional[str] = None


class ChatSessionUpdate(AppBaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None


class ChatSessionResponse(TimestampMixin):
    id: UUID
    company_id: UUID
    user_id: UUID
    title: Optional[str] = None
    is_active: bool
    deleted_at: Optional[datetime] = None


# ── Chat Messages ─────────────────────────────────────────────

class ChatMessageCreate(AppBaseModel):
    role: ChatRole
    content: str = Field(..., min_length=1)
    tokens_used: Optional[int] = None
    metadata: Dict[str, Any] = {}


class ChatMessageResponse(AppBaseModel):
    id: UUID
    session_id: UUID
    role: ChatRole
    content: str
    tokens_used: Optional[int] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime


class SendMessageRequest(AppBaseModel):
    """User sends a message to the AI assistant."""
    content: str = Field(..., min_length=1, max_length=10000)

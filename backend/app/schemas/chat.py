"""Chat sessions, messages, and cross-conversation AI memory schemas."""
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
    summary: Optional[str] = None
    last_summarized_at: Optional[datetime] = None
    is_active: bool
    deleted_at: Optional[datetime] = None
    message_count: Optional[int] = None


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
    content: Optional[str] = Field(None, max_length=10000)
    message: Optional[str] = Field(None, max_length=10000)
    session_id: Optional[str] = None
    provider: Optional[str] = None


# ── AI Long-Term Memories ──────────────────────────────────────

class AIMemoryCreate(AppBaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    category: str = Field("preference", pattern="^(preference|reporting|business_fact|goal|context)$")
    memory_key: Optional[str] = Field(None, max_length=100)
    confidence: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    session_id: Optional[UUID] = None


class AIMemoryUpdate(AppBaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    category: Optional[str] = Field(None, pattern="^(preference|reporting|business_fact|goal|context)$")
    memory_key: Optional[str] = Field(None, max_length=100)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class AIMemoryResponse(TimestampMixin):
    id: UUID
    company_id: UUID
    user_id: UUID
    session_id: Optional[UUID] = None
    category: str
    memory_key: Optional[str] = None
    content: str
    confidence: float
    is_active: bool
    metadata: Dict[str, Any] = {}

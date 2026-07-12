"""Chat router — /api/v1/chat"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_request_context
from app.repositories.chat import ChatMessageRepository, ChatSessionRepository
from app.schemas.chat import (
    ChatMessageCreate,
    ChatSessionCreate,
    ChatSessionUpdate,
    SendMessageRequest,
)
from app.schemas.common import MessageResponse, SuccessResponse
from app.services.context import RequestContext

router = APIRouter(prefix="/chat", tags=["Chat"])


# ── Sessions ──────────────────────────────────────────────────

@router.get("/sessions", response_model=SuccessResponse, summary="List chat sessions")
def list_sessions(ctx: RequestContext = Depends(get_request_context)):
    repo = ChatSessionRepository(ctx.user_client)
    return SuccessResponse(data=repo.list_user_sessions(ctx.company_id, ctx.user_id))


@router.post("/sessions", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create chat session")
def create_session(payload: ChatSessionCreate, ctx: RequestContext = Depends(get_request_context)):
    repo = ChatSessionRepository(ctx.user_client)
    data = repo.create({
        "company_id": str(ctx.company_id),
        "user_id": str(ctx.user_id),
        "title": payload.title,
    })
    return SuccessResponse(data=data)


@router.get("/sessions/{session_id}", response_model=SuccessResponse, summary="Get chat session")
def get_session(session_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ChatSessionRepository(ctx.user_client)
    return SuccessResponse(data=repo.get_by_id(session_id))


@router.patch("/sessions/{session_id}", response_model=SuccessResponse, summary="Update session title")
def update_session(session_id: UUID, payload: ChatSessionUpdate, ctx: RequestContext = Depends(get_request_context)):
    repo = ChatSessionRepository(ctx.user_client)
    return SuccessResponse(data=repo.update(session_id, payload.model_dump(exclude_none=True)))


@router.delete("/sessions/{session_id}", response_model=MessageResponse, summary="Delete chat session")
def delete_session(session_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ChatSessionRepository(ctx.user_client)
    repo.soft_delete(session_id)
    return MessageResponse(message="Session deleted.")


# ── Messages ──────────────────────────────────────────────────

@router.get("/sessions/{session_id}/messages", response_model=SuccessResponse, summary="List messages in session")
def list_messages(session_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ChatMessageRepository(ctx.user_client)
    return SuccessResponse(data=repo.list_session_messages(session_id))


@router.post("/sessions/{session_id}/messages", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Send a message")
def send_message(
    session_id: UUID,
    payload: SendMessageRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = ChatMessageRepository(ctx.user_client)
    # Store user message
    user_msg = repo.create_message({
        "session_id": str(session_id),
        "role": "user",
        "content": payload.content,
    })
    # NOTE: AI assistant response will be implemented in the ML phase.
    # Return the user message for now.
    return SuccessResponse(data=user_msg)

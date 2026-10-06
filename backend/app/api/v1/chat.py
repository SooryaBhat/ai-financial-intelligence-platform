"""Chat router — /api/v1/chat"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import logger
from app.dependencies.auth import get_request_context
from app.repositories.chat import ChatMessageRepository, ChatSessionRepository
from app.schemas.chat import (
    ChatMessageCreate,
    ChatSessionCreate,
    ChatSessionUpdate,
    SendMessageRequest,
)
from app.schemas.common import MessageResponse, SuccessResponse
from app.services.ai_context_service import AIContextService
from app.services.context import RequestContext

router = APIRouter(prefix="/chat", tags=["Chat"])


def _get_or_create_active_session(
    session_repo: ChatSessionRepository,
    company_id: UUID,
    user_id: UUID,
    provided_session_id: Optional[str] = None,
) -> str:
    """Helper to obtain a valid session_id for persisting chat messages."""
    if provided_session_id:
        try:
            return str(UUID(provided_session_id))
        except ValueError:
            pass

    try:
        active_sessions = session_repo.list_user_sessions(company_id, user_id)
        if active_sessions:
            return str(active_sessions[0]["id"])

        # Create a default session
        new_session = session_repo.create({
            "company_id": str(company_id),
            "user_id": str(user_id),
            "title": "AI Financial Intelligence Chat",
        })
        return str(new_session["id"])
    except Exception as e:
        logger.warning("Error fetching or creating chat session: {}", e)
        return ""


@router.post("/", response_model=SuccessResponse, summary="Send message to AI assistant")
def chat_assistant(payload: dict, ctx: RequestContext = Depends(get_request_context)):
    """
    Database-grounded AI assistant endpoint.
    Retrieves real ERP context for the user's company and generates answers via Gemini.
    """
    msg = payload.get("message") or payload.get("content") or ""
    if not msg.strip():
        return SuccessResponse(data={"message": "Please enter a valid question for the assistant.", "role": "assistant"})

    # Session management for persistence
    session_repo = ChatSessionRepository(ctx.user_client)
    msg_repo = ChatMessageRepository(ctx.user_client)
    session_id_str = _get_or_create_active_session(
        session_repo, ctx.company_id, ctx.user_id, payload.get("session_id")
    )

    if session_id_str:
        try:
            msg_repo.create_message({
                "session_id": session_id_str,
                "role": "user",
                "content": msg,
            })
        except Exception as err:
            logger.warning("Failed to persist user chat message: {}", err)

    # Build database context & query Gemini
    try:
        ai_service = AIContextService(ctx.user_client, ctx.company_id)
        reply = ai_service.answer_question(msg)
    except Exception as e:
        logger.error("Unhandled error in AIContextService: {}", e)
        reply = "AI Assistant is temporarily unavailable. Unable to process request."

    if session_id_str:
        try:
            msg_repo.create_message({
                "session_id": session_id_str,
                "role": "assistant",
                "content": reply,
            })
        except Exception as err:
            logger.warning("Failed to persist assistant chat message: {}", err)

    return SuccessResponse(data={"message": reply, "role": "assistant", "session_id": session_id_str})


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
        "title": payload.title or "AI Financial Intelligence Chat",
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
    # Save user message
    try:
        user_msg = repo.create_message({
            "session_id": str(session_id),
            "role": "user",
            "content": payload.content,
        })
    except Exception as e:
        logger.warning("Could not persist user message: {}", e)

    # Generate Gemini grounded response
    try:
        ai_service = AIContextService(ctx.user_client, ctx.company_id)
        reply = ai_service.answer_question(payload.content)
    except Exception as e:
        logger.error("Error in AIContextService for session message: {}", e)
        reply = "AI Assistant is temporarily unavailable."

    # Save assistant message
    assistant_msg = None
    try:
        assistant_msg = repo.create_message({
            "session_id": str(session_id),
            "role": "assistant",
            "content": reply,
        })
    except Exception as e:
        logger.warning("Could not persist assistant message: {}", e)

    return SuccessResponse(data=assistant_msg or {"role": "assistant", "content": reply, "message": reply})

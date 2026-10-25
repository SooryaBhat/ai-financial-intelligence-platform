"""Voice Assistant router — /api/v1/voice"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger
from app.dependencies.auth import get_request_context
from app.repositories.chat import (
    ChatMessageRepository,
    ChatSessionRepository,
)
from app.schemas.common import SuccessResponse
from app.services.ai_context_service import AIContextService
from app.services.ai_memory_service import AIMemoryService
from app.services.context import RequestContext

router = APIRouter(prefix="/voice", tags=["Voice Assistant"])


class VoiceSessionInitRequest(BaseModel):
    session_id: Optional[str] = None
    title: Optional[str] = "Voice Session with Alladin"


class VoiceTurnRequest(BaseModel):
    session_id: Optional[str] = None
    transcript: str = Field(..., min_length=1, description="Transcribed user speech")
    provider: Optional[str] = None


@router.get("/status", response_model=SuccessResponse, summary="Get voice assistant capabilities and status")
def get_voice_status(ctx: RequestContext = Depends(get_request_context)):
    """
    Returns current voice assistant configuration, supported engines,
    and server-side authorization status for the company.
    """
    active_provider = getattr(settings, "ai_provider", "gemini")
    
    return SuccessResponse(data={
        "status": "ready",
        "company_id": str(ctx.company_id),
        "user_id": str(ctx.user_id),
        "active_provider": active_provider,
        "supported_modes": ["browser_speech_api", "gemini_multimodal_ready"],
        "speech_recognition": {
            "engine": "web_speech_api",
            "fallback": "text_input",
            "languages": ["en-US", "en-IN", "en-GB"],
        },
        "speech_synthesis": {
            "engine": "web_speech_synthesis",
            "character": "Alladin the Financial Genie",
            "default_pitch": 1.05,
            "default_rate": 1.0,
        },
        "capabilities": {
            "erp_tools": True,
            "memory_integration": True,
            "conversation_summaries": True,
            "interruption_support": True,
        },
    })


@router.post("/session", response_model=SuccessResponse, summary="Initialize or resume a voice chat session")
def init_voice_session(
    payload: VoiceSessionInitRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Resolves or creates a persistent chat session for voice mode,
    ensuring all voice turns are saved directly to the user's ERP chat history.
    """
    session_repo = ChatSessionRepository(ctx.user_client)
    
    if payload.session_id:
        try:
            sid = UUID(payload.session_id)
            existing = session_repo.get_user_session(sid, ctx.company_id, ctx.user_id)
            if existing:
                return SuccessResponse(data={
                    "session_id": str(existing["id"]),
                    "title": existing.get("title", "Voice Session"),
                    "is_new": False,
                })
        except ValueError:
            pass

    # Create new dedicated voice session
    new_session = session_repo.create({
        "company_id": str(ctx.company_id),
        "user_id": str(ctx.user_id),
        "title": payload.title or "Voice Session with Alladin",
    })
    
    return SuccessResponse(data={
        "session_id": str(new_session["id"]),
        "title": new_session.get("title", "Voice Session"),
        "is_new": True,
    })


@router.post("/turn", response_model=SuccessResponse, summary="Execute a voice turn with ERP grounding")
def execute_voice_turn(
    payload: VoiceTurnRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Processes a transcribed voice message:
    1. Persists transcript in the session as user turn.
    2. Retrieves conversational context & relevant company memories.
    3. Executes authorized ERP tools (sales, expenses, inventory, forecasting, health).
    4. Persists assistant reply with tool execution metadata.
    5. Returns grounded answer text ready for character animation & speech synthesis.
    """
    transcript = payload.transcript.strip()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript cannot be empty",
        )

    session_repo = ChatSessionRepository(ctx.user_client)
    msg_repo = ChatMessageRepository(ctx.user_client)
    memory_service = AIMemoryService(ctx.user_client, ctx.company_id, ctx.user_id)

    # 1. Resolve session
    session = None
    if payload.session_id:
        try:
            sid = UUID(payload.session_id)
            session = session_repo.get_user_session(sid, ctx.company_id, ctx.user_id)
        except ValueError:
            pass

    if not session:
        title = AIMemoryService.generate_conversation_title(transcript)
        session = session_repo.create({
            "company_id": str(ctx.company_id),
            "user_id": str(ctx.user_id),
            "title": f"Voice: {title}",
        })

    session_id_val = session.get("id")
    session_id_str = str(session_id_val)

    # 2. Persist user voice transcript
    try:
        msg_repo.create_message({
            "session_id": session_id_str,
            "role": "user",
            "content": transcript,
            "metadata": {"input_mode": "voice"},
        })
    except Exception as err:
        logger.warning("[Voice] Failed to persist user transcript: {}", err)

    # 3. Fetch summary and recent history
    summary = None
    try:
        summary = memory_service.summarize_if_needed(session_id_val)
    except Exception as sum_err:
        logger.warning("[Voice] Summary check failed: {}", sum_err)

    history: List[Dict[str, Any]] = []
    try:
        history = msg_repo.get_recent_messages(session_id_val, limit=8)
        if history and history[-1].get("content") == transcript:
            history = history[:-1]
    except Exception as hist_err:
        logger.warning("[Voice] History fetch failed: {}", hist_err)

    # 4. Fetch memories
    memories: List[Dict[str, Any]] = []
    try:
        memories = memory_service.get_relevant_memories(query=transcript, limit=4)
        # Also extract memory if expressed
        memory_service.extract_and_store_memory(transcript, session_id=session_id_val)
    except Exception as mem_err:
        logger.warning("[Voice] Memory handling failed: {}", mem_err)

    # 5. Execute AI tool-calling loop grounded in verified company ERP data
    try:
        ai_service = AIContextService(ctx.user_client, ctx.company_id)
        result = ai_service.answer_with_tools(
            transcript,
            history=history,
            summary=summary,
            memories=memories,
            provider=payload.provider,
        )
        reply = result.get("message") or "Voice analysis complete."
        tools_used = result.get("tools_used") or []
        provider_used = result.get("provider", "gemini")
        model_used = result.get("model", "unknown")
    except Exception as e:
        logger.exception("[Voice] Assistant error: {}", e)
        reply = f"I encountered an error retrieving company records: {str(e)}"
        tools_used = []
        provider_used = "error"
        model_used = "none"

    # 6. Persist assistant reply
    try:
        msg_repo.create_message({
            "session_id": session_id_str,
            "role": "assistant",
            "content": reply,
            "metadata": {
                "input_mode": "voice",
                "tools_used": tools_used,
                "provider": provider_used,
                "model": model_used,
            },
        })
    except Exception as err:
        logger.warning("[Voice] Failed to persist assistant voice reply: {}", err)

    return SuccessResponse(data={
        "session_id": session_id_str,
        "transcript": transcript,
        "reply": reply,
        "tools_used": tools_used,
        "provider": provider_used,
        "model": model_used,
    })

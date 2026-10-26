"""Chat router — /api/v1/chat"""
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.logging import logger
from app.dependencies.auth import get_request_context
from app.repositories.chat import (
    AIMemoryRepository,
    ChatMessageRepository,
    ChatSessionRepository,
)
from app.schemas.chat import (
    AIMemoryCreate,
    AIMemoryResponse,
    AIMemoryUpdate,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
    SendMessageRequest,
)
from app.schemas.common import MessageResponse, SuccessResponse
from app.services.ai_context_service import AIContextService
from app.services.ai_memory_service import AIMemoryService
from app.services.context import RequestContext

router = APIRouter(prefix="/chat", tags=["Chat"])


def _get_or_create_session(
    session_repo: ChatSessionRepository,
    company_id: UUID,
    user_id: UUID,
    provided_session_id: Optional[str] = None,
    initial_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper to obtain or create a valid session record for the user and company."""
    if provided_session_id:
        try:
            sid = UUID(provided_session_id)
            existing = session_repo.get_user_session(sid, company_id, user_id)
            if existing:
                return existing
        except ValueError:
            pass

    # If active sessions exist and no session specified, return newest active
    active_sessions = session_repo.list_user_sessions(company_id, user_id, limit=1)
    if active_sessions and not initial_message:
        return active_sessions[0]

    # Generate a professional title if initial message is provided
    title = (
        AIMemoryService.generate_conversation_title(initial_message)
        if initial_message
        else "AI Financial Intelligence Chat"
    )

    new_session = session_repo.create({
        "company_id": str(company_id),
        "user_id": str(user_id),
        "title": title,
    })
    return new_session


@router.get("/providers", response_model=SuccessResponse, summary="Get available AI LLM providers and connection status")
def get_providers(ctx: RequestContext = Depends(get_request_context)):
    """
    Returns available LLM providers (Local Ollama, Cloud Gemini), configured models,
    live probe status, and the current default provider.
    """
    import httpx
    from app.core.config import settings

    default_provider = getattr(settings, "effective_ai_provider", "ollama") or "ollama"
    ollama_base_url = (getattr(settings, "ollama_base_url", "http://localhost:11434") or "http://localhost:11434").rstrip("/")
    ollama_model = getattr(settings, "ollama_model", "qwen3:4b") or "qwen3:4b"

    # Fast probe for Ollama
    ollama_available = False
    ollama_status = "offline"
    ollama_installed_models: List[str] = []
    try:
        with httpx.Client(timeout=1.0) as client:
            resp = client.get(f"{ollama_base_url}/api/tags")
            if resp.status_code == 200:
                models_data = resp.json().get("models", [])
                ollama_installed_models = [m.get("name", "") for m in models_data if m.get("name")]
                # Match full tag (e.g. "qwen3:4b") or prefix
                model_found = any(
                    ollama_model == m or m.startswith(f"{ollama_model}:") or ollama_model.startswith(f"{m}:")
                    for m in ollama_installed_models
                )
                if model_found:
                    ollama_available = True
                    ollama_status = "connected"
                else:
                    ollama_status = "model_missing"
    except Exception as e:
        ollama_status = "offline"
        logger.debug("Ollama probe failed: {}", e)

    # Gemini probe
    gemini_key = (
        getattr(settings, "gemini_api_key", "")
        or os.getenv("GEMINI_API_KEY", "")
        or os.getenv("GOOGLE_API_KEY", "")
    )
    gemini_available = bool(gemini_key and gemini_key.strip())
    gemini_status = "configured" if gemini_available else "missing_key"

    providers_data = [
        {
            "id": "ollama",
            "name": "Ollama — Local",
            "model": ollama_model,
            "badge": "Local / Private",
            "is_default": default_provider == "ollama",
            "available": ollama_available,
            "status": ollama_status,
            "installed_models": ollama_installed_models,
            "base_url": ollama_base_url,
            "description": f"Runs locally on your machine via Ollama ({ollama_model}) with 100% data locality.",
        },
        {
            "id": "gemini",
            "name": "Gemini — Cloud",
            "model": "gemini-2.5-flash",
            "badge": "Cloud / High Accuracy",
            "is_default": default_provider == "gemini",
            "available": gemini_available,
            "status": gemini_status,
            "description": "Google Gemini 2.5 Flash cloud model for advanced reasoning and financial synthesis.",
        },
    ]

    return SuccessResponse(data={
        "default_provider": default_provider,
        "active_provider": default_provider,
        "providers": providers_data,
    })


@router.post("", response_model=SuccessResponse, summary="Send message to AI assistant")
@router.post("/", response_model=SuccessResponse, summary="Send message to AI assistant", include_in_schema=False)
def chat_assistant(payload: dict, ctx: RequestContext = Depends(get_request_context)):
    """
    Database-grounded AI assistant endpoint.
    Maintains persistent short-term conversational context, long-conversation summaries,
    and cross-conversation long-term memory.
    """
    msg = (payload.get("message") or payload.get("content") or "").strip()
    if not msg:
        return SuccessResponse(data={"message": "Please enter a valid question for the assistant.", "role": "assistant"})

    requested_provider = payload.get("provider")

    session_repo = ChatSessionRepository(ctx.user_client)
    msg_repo = ChatMessageRepository(ctx.user_client)
    memory_service = AIMemoryService(ctx.user_client, ctx.company_id, ctx.user_id)

    # Resolve or create conversation session
    session = _get_or_create_session(
        session_repo,
        ctx.company_id,
        ctx.user_id,
        payload.get("session_id"),
        initial_message=msg,
    )
    session_id_val = session.get("id") or "default"
    session_id_str = str(session_id_val)

    # If existing session has a placeholder title and this is an early message, give it a smart title
    current_title = session.get("title") or ""
    if current_title in ("AI Financial Intelligence Chat", "New Conversation", ""):
        smart_title = AIMemoryService.generate_conversation_title(msg)
        session_repo.update_session(session_id_val, ctx.company_id, ctx.user_id, {"title": smart_title})

    # Save incoming user message to database
    try:
        msg_repo.create_message({
            "session_id": session_id_str,
            "role": "user",
            "content": msg,
        })
    except Exception as err:
        logger.warning("Failed to persist user chat message: {}", err)

    # 1. Update/retrieve long-conversation summary if message count is high
    summary = None
    try:
        summary = memory_service.summarize_if_needed(session_id_val)
    except Exception as sum_err:
        logger.warning("Error evaluating conversation summary: {}", sum_err)

    # 2. Retrieve recent messages for short-term conversational memory
    history: List[Dict[str, Any]] = []
    try:
        history = msg_repo.get_recent_messages(session_id_val, limit=12)
        # Exclude the message we just saved so it's not duplicated in prompt
        if history and history[-1].get("content") == msg:
            history = history[:-1]
    except Exception as hist_err:
        logger.warning("Error fetching recent messages: {}", hist_err)

    # 3. Retrieve relevant cross-conversation long-term memories
    memories: List[Dict[str, Any]] = []
    try:
        memories = memory_service.get_relevant_memories(query=msg, limit=6)
    except Exception as mem_err:
        logger.warning("Error fetching memories: {}", mem_err)

    # 4. Check if current user message expresses a durable memory to extract
    try:
        memory_service.extract_and_store_memory(msg, session_id=session_id_val)
    except Exception as ext_err:
        logger.warning("Error extracting memory: {}", ext_err)

    # 5. Query AI assistant with grounded ERP tools, short-term history, summary & memories
    tools_used = []
    result = {}
    try:
        ai_service = AIContextService(ctx.user_client, ctx.company_id)
        result = ai_service.answer_with_tools(
            msg,
            history=history,
            summary=summary,
            memories=memories,
            provider=requested_provider,
        )
        reply = result.get("message") or "Analysis complete."
        tools_used = result.get("tools_used") or []
    except Exception as e:
        logger.exception("AI Assistant execution failed: {}", e)
        reply = f"AI Assistant encountered an error processing your request: {str(e)}"
        result = {
            "message": reply,
            "provider": "error",
            "model": "none",
            "status": "error",
            "error_details": str(e),
        }

    provider_used = result.get("provider", "unknown")
    model_used = result.get("model", "unknown")
    status_used = result.get("status", "success")
    error_details = result.get("error_details")
    fallback_used = result.get("fallback_used", False)
    fallback_reason = result.get("fallback_reason")
    timing = result.get("timing")

    # Save assistant message to database with full tool/provider metadata
    try:
        msg_repo.create_message({
            "session_id": session_id_str,
            "role": "assistant",
            "content": reply,
            "metadata": {
                "tools_used": tools_used,
                "provider": provider_used,
                "model": model_used,
                "status": status_used,
                "error_details": error_details,
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "timing": timing,
            },
        })
    except Exception as err:
        logger.warning("Failed to persist assistant chat message: {}", err)

    return SuccessResponse(data={
        "message": reply,
        "content": reply,
        "role": "assistant",
        "session_id": session_id_str,
        "tools_used": tools_used,
        "provider": provider_used,
        "model": model_used,
        "status": status_used,
        "error_details": error_details,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "timing": timing,
        "summary": summary,
        "memories_count": len(memories),
    })


# ── Sessions ──────────────────────────────────────────────────

@router.get("/sessions", response_model=SuccessResponse, summary="List chat sessions")
def list_sessions(
    search: Optional[str] = Query(None, description="Search query for session title"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = ChatSessionRepository(ctx.user_client)
    sessions = repo.list_user_sessions(
        ctx.company_id,
        ctx.user_id,
        search=search,
        limit=limit,
        offset=offset,
    )
    return SuccessResponse(data=sessions)


@router.post("/sessions", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create chat session")
def create_session(payload: ChatSessionCreate, ctx: RequestContext = Depends(get_request_context)):
    repo = ChatSessionRepository(ctx.user_client)
    title = payload.title.strip() if payload.title and payload.title.strip() else "New Conversation"
    data = repo.create({
        "company_id": str(ctx.company_id),
        "user_id": str(ctx.user_id),
        "title": title,
    })
    return SuccessResponse(data=data)


@router.get("/sessions/{session_id}", response_model=SuccessResponse, summary="Get chat session")
def get_session(session_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ChatSessionRepository(ctx.user_client)
    session = repo.get_user_session(session_id, ctx.company_id, ctx.user_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return SuccessResponse(data=session)


@router.patch("/sessions/{session_id}", response_model=SuccessResponse, summary="Update session title")
def update_session(session_id: UUID, payload: ChatSessionUpdate, ctx: RequestContext = Depends(get_request_context)):
    repo = ChatSessionRepository(ctx.user_client)
    session = repo.get_user_session(session_id, ctx.company_id, ctx.user_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        return SuccessResponse(data=session)

    updated = repo.update_session(session_id, ctx.company_id, ctx.user_id, update_data)
    return SuccessResponse(data=updated or session)


@router.delete("/sessions/{session_id}", response_model=MessageResponse, summary="Delete chat session")
def delete_session(session_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ChatSessionRepository(ctx.user_client)
    session = repo.get_user_session(session_id, ctx.company_id, ctx.user_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    repo.delete_session(session_id, ctx.company_id, ctx.user_id)
    return MessageResponse(message="Session deleted.")


# ── Messages ──────────────────────────────────────────────────

@router.get("/sessions/{session_id}/messages", response_model=SuccessResponse, summary="List messages in session")
def list_messages(
    session_id: UUID,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ctx: RequestContext = Depends(get_request_context),
):
    session_repo = ChatSessionRepository(ctx.user_client)
    session = session_repo.get_user_session(session_id, ctx.company_id, ctx.user_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    repo = ChatMessageRepository(ctx.user_client)
    messages = repo.list_session_messages(session_id, limit=limit, offset=offset)
    return SuccessResponse(data=messages)


@router.post("/sessions/{session_id}/messages", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Send message in session")
def send_message(
    session_id: UUID,
    payload: SendMessageRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    content = (payload.content or payload.message or "").strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty.")

    session_repo = ChatSessionRepository(ctx.user_client)
    session = session_repo.get_user_session(session_id, ctx.company_id, ctx.user_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    msg_repo = ChatMessageRepository(ctx.user_client)
    memory_service = AIMemoryService(ctx.user_client, ctx.company_id, ctx.user_id)

    # If title is default, set a smart title from this message
    current_title = session.get("title") or ""
    if current_title in ("AI Financial Intelligence Chat", "New Conversation", ""):
        smart_title = AIMemoryService.generate_conversation_title(content)
        session_repo.update_session(session_id, ctx.company_id, ctx.user_id, {"title": smart_title})

    # Save user message
    try:
        msg_repo.create_message({
            "session_id": str(session_id),
            "role": "user",
            "content": content,
        })
    except Exception as e:
        logger.warning("Could not persist user message: {}", e)

    # 1. Update/check running summary if conversation is long
    summary = None
    try:
        summary = memory_service.summarize_if_needed(session_id)
    except Exception as sum_err:
        logger.warning("Error evaluating conversation summary: {}", sum_err)

    # 2. Retrieve recent messages for short-term history
    history: List[Dict[str, Any]] = []
    try:
        history = msg_repo.get_recent_messages(session_id, limit=12)
        if history and history[-1].get("content") == content:
            history = history[:-1]
    except Exception as hist_err:
        logger.warning("Error fetching recent messages: {}", hist_err)

    # 3. Retrieve relevant long-term cross-conversation memories
    memories: List[Dict[str, Any]] = []
    try:
        memories = memory_service.get_relevant_memories(query=content, limit=6)
    except Exception as mem_err:
        logger.warning("Error fetching memories: {}", mem_err)

    # 4. Check for durable memory to extract
    try:
        memory_service.extract_and_store_memory(content, session_id=session_id)
    except Exception as ext_err:
        logger.warning("Error extracting memory: {}", ext_err)

    # 5. Generate grounded response with tool calling
    tools_used = []
    result = {}
    try:
        ai_service = AIContextService(ctx.user_client, ctx.company_id)
        result = ai_service.answer_with_tools(
            content,
            history=history,
            summary=summary,
            memories=memories,
            provider=payload.provider,
        )
        reply = result.get("message") or "Analysis complete."
        tools_used = result.get("tools_used") or []
    except Exception as e:
        logger.exception("Error in AI Assistant for session message: {}", e)
        reply = f"AI Assistant encountered an error: {str(e)}"
        result = {
            "message": reply,
            "provider": "error",
            "model": "none",
            "status": "error",
            "error_details": str(e),
        }

    provider_used = result.get("provider", "unknown")
    model_used = result.get("model", "unknown")
    status_used = result.get("status", "success")
    error_details = result.get("error_details")
    fallback_used = result.get("fallback_used", False)
    fallback_reason = result.get("fallback_reason")
    timing = result.get("timing")

    # Save assistant message
    assistant_msg = None
    try:
        assistant_msg = msg_repo.create_message({
            "session_id": str(session_id),
            "role": "assistant",
            "content": reply,
            "metadata": {
                "tools_used": tools_used,
                "provider": provider_used,
                "model": model_used,
                "status": status_used,
                "error_details": error_details,
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "timing": timing,
            },
        })
    except Exception as e:
        logger.warning("Could not persist assistant message: {}", e)

    return SuccessResponse(data=assistant_msg or {
        "role": "assistant",
        "content": reply,
        "message": reply,
        "session_id": str(session_id),
        "tools_used": tools_used,
        "provider": provider_used,
        "model": model_used,
        "status": status_used,
        "error_details": error_details,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "timing": timing,
        "summary": summary,
        "memories_count": len(memories),
    })


# ── Long-Term Memory Controls ──────────────────────────────────

@router.get("/memories", response_model=SuccessResponse, summary="List AI memories")
def list_memories(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search query"),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = AIMemoryRepository(ctx.user_client)
    memories = repo.list_memories(
        ctx.company_id,
        ctx.user_id,
        active_only=False,
        category=category,
        search=search,
    )
    return SuccessResponse(data=memories)


@router.post("/memories", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create AI memory")
def create_memory(payload: AIMemoryCreate, ctx: RequestContext = Depends(get_request_context)):
    repo = AIMemoryRepository(ctx.user_client)
    data = repo.create_memory({
        "company_id": str(ctx.company_id),
        "user_id": str(ctx.user_id),
        "session_id": str(payload.session_id) if payload.session_id else None,
        "category": payload.category,
        "memory_key": payload.memory_key,
        "content": payload.content.strip(),
        "confidence": payload.confidence or 1.0,
        "is_active": True,
    })
    return SuccessResponse(data=data)


@router.patch("/memories/{memory_id}", response_model=SuccessResponse, summary="Update AI memory")
def update_memory(
    memory_id: UUID,
    payload: AIMemoryUpdate,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = AIMemoryRepository(ctx.user_client)
    existing = repo.get_memory(memory_id, ctx.company_id, ctx.user_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        return SuccessResponse(data=existing)

    updated = repo.update_memory(memory_id, ctx.company_id, ctx.user_id, update_data)
    return SuccessResponse(data=updated or existing)


@router.delete("/memories/{memory_id}", response_model=MessageResponse, summary="Delete AI memory")
def delete_memory(memory_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = AIMemoryRepository(ctx.user_client)
    existing = repo.get_memory(memory_id, ctx.company_id, ctx.user_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    repo.delete_memory(memory_id, ctx.company_id, ctx.user_id)
    return MessageResponse(message="Memory deleted.")


@router.delete("/memories", response_model=MessageResponse, summary="Clear all AI memories for user")
def clear_all_memories(ctx: RequestContext = Depends(get_request_context)):
    repo = AIMemoryRepository(ctx.user_client)
    count = repo.clear_all_memories(ctx.company_id, ctx.user_id)
    return MessageResponse(message=f"Cleared {count} memories.")

import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth import get_request_context
from app.services.context import RequestContext


@pytest.fixture
def mock_request_context():
    return RequestContext(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        company_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        user_client=MagicMock(),
        permissions=["erp:read", "erp:write"],
    )


@pytest.fixture
def client(mock_request_context):
    app.dependency_overrides[get_request_context] = lambda: mock_request_context
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_voice_status_endpoint(client, mock_request_context):
    """Verify voice status returns engine capabilities and authorized company scope."""
    response = client.get("/api/v1/voice/status")
    assert response.status_code == status.HTTP_200_OK
    data = response.json().get("data", {})
    assert data.get("status") == "ready"
    assert data.get("company_id") == str(mock_request_context.company_id)
    assert data.get("user_id") == str(mock_request_context.user_id)
    assert "speech_recognition" in data
    assert "speech_synthesis" in data
    assert data["capabilities"].get("erp_tools") is True
    assert data["capabilities"].get("interruption_support") is True


def test_voice_session_initialization(client, mock_request_context):
    """Verify voice session creation persists to chat session repo with user company scope."""
    mock_supabase = mock_request_context.user_client
    mock_query = MagicMock()
    mock_supabase.table.return_value = mock_query
    
    # Mock create session
    new_sess_id = str(uuid.uuid4())
    mock_query.insert.return_value.execute.return_value = MagicMock(data=[{
        "id": new_sess_id,
        "title": "Voice Session with Alladin",
        "company_id": str(mock_request_context.company_id),
        "user_id": str(mock_request_context.user_id),
    }])

    response = client.post("/api/v1/voice/session", json={
        "title": "Voice Financial Review"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json().get("data", {})
    assert data.get("is_new") is True
    assert data.get("session_id") == new_sess_id


def test_voice_turn_empty_transcript_validation(client):
    """Verify empty transcript returns 400 Bad Request."""
    response = client.post("/api/v1/voice/turn", json={"transcript": ""})
    assert response.status_code == status.HTTP_400_BAD_REQUEST or response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("app.api.v1.voice.AIContextService")
def test_voice_turn_execution_and_persistence(mock_ai_context_class, client, mock_request_context):
    """Verify voice turn executes grounded ERP tools and returns synthesis-ready reply."""
    mock_supabase = mock_request_context.user_client
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    
    # Mock AI context service
    mock_ai_instance = MagicMock()
    mock_ai_context_class.return_value = mock_ai_instance
    mock_ai_instance.answer_with_tools.return_value = {
        "message": "Total sales for this month are $84,200 across 34 orders.",
        "tools_used": [{
            "tool": "get_sales_analysis",
            "summary": "Total sales revenue for this month is $84,200",
            "args": {"timeframe": "this_month"}
        }],
        "provider": "gemini",
        "model": "gemini-2.5-flash",
    }
    
    # Mock session lookup
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    sess_id = str(uuid.uuid4())
    mock_select.eq.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock(data=[{
        "id": sess_id,
        "title": "Voice Session",
        "company_id": str(mock_request_context.company_id),
        "user_id": str(mock_request_context.user_id),
    }])

    # Mock message insert
    mock_table.insert.return_value.execute.return_value = MagicMock(data=[{"id": "msg-1"}])

    response = client.post("/api/v1/voice/turn", json={
        "session_id": sess_id,
        "transcript": "What are our sales for this month?",
    })
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json().get("data", {})
    assert data.get("session_id") == sess_id
    assert "$84,200" in data.get("reply", "")
    assert len(data.get("tools_used", [])) == 1
    assert data["tools_used"][0]["tool"] == "get_sales_analysis"
    assert data.get("provider") == "gemini"


def test_voice_turn_whitespace_only_transcript_rejected(client):
    """Verify whitespace-only transcript is rejected and never sent to AI."""
    response = client.post("/api/v1/voice/turn", json={"transcript": "   \n\t   "})
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)


@patch("app.api.v1.voice.AIContextService")
def test_voice_turn_preserves_session_across_multiple_turns(mock_ai_context_class, client, mock_request_context):
    """Verify multiple conversational turns reuse and preserve the active session ID."""
    mock_supabase = mock_request_context.user_client
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    
    mock_ai_instance = MagicMock()
    mock_ai_context_class.return_value = mock_ai_instance
    mock_ai_instance.answer_with_tools.side_effect = [
        {"message": "Turn 1 answer", "tools_used": [], "provider": "gemini", "model": "gemini-2.5-flash"},
        {"message": "Turn 2 answer", "tools_used": [], "provider": "gemini", "model": "gemini-2.5-flash"},
    ]
    
    sess_id = str(uuid.uuid4())
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock(data=[{
        "id": sess_id,
        "title": "Voice Session",
        "company_id": str(mock_request_context.company_id),
        "user_id": str(mock_request_context.user_id),
    }])
    mock_table.insert.return_value.execute.return_value = MagicMock(data=[{"id": "msg"}])

    # Turn 1
    resp1 = client.post("/api/v1/voice/turn", json={"session_id": sess_id, "transcript": "Hello Alladin"})
    assert resp1.status_code == status.HTTP_200_OK
    assert resp1.json()["data"]["session_id"] == sess_id
    assert resp1.json()["data"]["reply"] == "Turn 1 answer"

    # Turn 2
    resp2 = client.post("/api/v1/voice/turn", json={"session_id": sess_id, "transcript": "What about expenses?"})
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.json()["data"]["session_id"] == sess_id
    assert resp2.json()["data"]["reply"] == "Turn 2 answer"


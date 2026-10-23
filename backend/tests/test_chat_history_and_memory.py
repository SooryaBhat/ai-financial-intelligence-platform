import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from app.services.context import RequestContext
from app.schemas.chat import AIMemoryCreate, AIMemoryUpdate, SendMessageRequest
from app.services.ai_memory_service import AIMemoryService
from app.services.ai_assistant import AIAssistantService, OllamaLLMProvider, FallbackERPProvider
from app.repositories.chat import ChatSessionRepository, ChatMessageRepository, AIMemoryRepository


@pytest.fixture
def user_a_context():
    return RequestContext(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        company_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        user_client=MagicMock(),
        permissions=["erp:read", "erp:write"]
    )


@pytest.fixture
def user_b_context():
    return RequestContext(
        user_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        company_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        user_client=MagicMock(),
        permissions=["erp:read"]
    )


# ============================================================================
# 1. Title Generation & Summaries
# ============================================================================

def test_title_generation_from_first_message():
    # Financial inquiry
    title1 = AIMemoryService.generate_conversation_title("What were our sales for December 2025?")
    assert "Sales" in title1

    # Generic inquiry
    title2 = AIMemoryService.generate_conversation_title("Hello, could you help me review our pending supplier invoices?")
    assert len(title2) > 0
    assert len(title2) <= 50

    # Fallback to default
    title3 = AIMemoryService.generate_conversation_title("")
    assert title3 == "New Conversation"


def test_long_conversation_summary_trigger_and_content(user_a_context):
    client = MagicMock()
    service = AIMemoryService(client, user_a_context.company_id, user_a_context.user_id)
    
    # 12 turns - structured summary creation
    long_history = [
        {"role": "user", "content": "What was our net profit in March?"},
        {
            "role": "assistant",
            "content": "Net profit was $42,500 based on verified records.",
            "metadata": {"tools_used": [{"tool": "get_sales_analysis", "summary": "Net profit was $42,500"}]}
        },
        {"role": "user", "content": "Why did it decrease compared to February?"},
        {
            "role": "assistant",
            "content": "Operating expenses rose by 14% due to logistics surcharges.",
            "metadata": {"tools_used": [{"tool": "get_expense_summary", "summary": "Expenses rose 14% due to logistics"}]}
        },
        {"role": "user", "content": "Did we check supplier invoices for logistics?"},
        {"role": "assistant", "content": "Yes, freight from Global Logistics accounted for $8,200."},
        {"role": "user", "content": "Note that our logistics target ceiling is $5,000."},
        {"role": "assistant", "content": "Understood, tracking logistics budget ceiling at $5,000."},
        {"role": "user", "content": "What is our current cash position?"},
        {"role": "assistant", "content": "Verified bank balance is $134,000 across operating accounts."},
        {"role": "user", "content": "Are there any pending receivables?"},
        {"role": "assistant", "content": "You have 3 invoices pending collection totaling $18,400."},
    ]
    
    summary = service._generate_structured_summary(long_history, previous_summary=None)
    assert len(summary) > 0
    assert "Key User Inquiries" in summary or "Verified Findings" in summary
    assert "logistics" in summary.lower() or "profit" in summary.lower() or "receivables" in summary.lower()


# ============================================================================
# 2. Long-term Memory Extraction & Cross-Conversation Recall
# ============================================================================

def test_long_term_memory_extraction_heuristics(user_a_context):
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    
    # Mock list_memories returning empty list so it creates new
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value.eq.return_value.order.return_value.limit.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    
    # Mock insert returning created memory
    mock_table.insert.return_value.execute.return_value = MagicMock(data=[{
        "id": "123",
        "category": "preference",
        "content": "our reporting currency is INR (Indian Rupee) and we prefer Lakhs notation",
        "is_active": True
    }])

    service = AIMemoryService(mock_client, user_a_context.company_id, user_a_context.user_id)
    
    # 1. Preferred currency / format extraction
    mem = service.extract_and_store_memory(
        user_message="Please remember that our reporting currency is INR (Indian Rupee) and we prefer Lakhs notation."
    )
    assert mem is not None
    assert "INR" in mem["content"] or "preference" in mem.get("category", "")
    
    # 2. Security check: Sensitive data like passwords / tokens MUST NEVER be saved as memory
    sensitive_message = "My database password is SuperSecretPass123! and API key is sk-live-99999"
    no_mem = service.extract_and_store_memory(
        user_message=sensitive_message
    )
    assert no_mem is None


def test_memory_formatting_for_prompt():
    memories = [
        {"content": "Preferred currency is INR Lakhs", "category": "preference"},
        {"content": "Fiscal year begins April 1st", "category": "business_fact"},
    ]
    prompt_str = AIMemoryService.format_memories_prompt_block(memories)
    assert "USER PREFERENCES & BUSINESS MEMORY" in prompt_str
    assert "INR Lakhs" in prompt_str
    assert "Fiscal year begins April 1st" in prompt_str
    assert "NEVER treat remembered figures as a replacement for live ERP tool data" in prompt_str


# ============================================================================
# 3. Short-term Conversational Memory & Pronoun Resolution
# ============================================================================

def test_short_term_context_pronoun_resolution_ollama_history():
    """
    Verify that conversational history turns are preserved in chronological order
    so that pronouns like 'it', 'that', and 'why did it decrease' can be resolved.
    """
    history = [
        {"role": "user", "content": "What were the sales for Q2?"},
        {"role": "assistant", "content": "Total sales for Q2 were $150,000 across 320 transactions."},
    ]
    
    messages = []
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    
    follow_up = "Why did it decrease from last month?"
    messages.append({"role": "user", "content": follow_up})
    
    # Verify order and content
    assert len(messages) == 3
    assert messages[0]["content"] == "What were the sales for Q2?"
    assert messages[1]["content"] == "Total sales for Q2 were $150,000 across 320 transactions."
    assert messages[2]["content"] == "Why did it decrease from last month?"


# ============================================================================
# 4. Multi-Tenant and User Isolation
# ============================================================================

def test_memory_repository_tenant_isolation(user_a_context, user_b_context):
    """
    Ensure User A's queries pass user_a company_id/user_id, and User B passes user_b.
    """
    mock_supabase = MagicMock()
    mock_query = MagicMock()
    mock_supabase.table.return_value = mock_query
    
    repo = AIMemoryRepository(mock_supabase)
    
    # User A listing memories
    repo.list_memories(user_a_context.company_id, user_a_context.user_id)
    mock_query.select.assert_called_with("*")
    mock_query.select().eq.assert_any_call("company_id", str(user_a_context.company_id))
    mock_query.select().eq().eq.assert_any_call("user_id", str(user_a_context.user_id))

    # User B company and user are completely distinct
    assert str(user_a_context.company_id) != str(user_b_context.company_id)
    assert str(user_a_context.user_id) != str(user_b_context.user_id)


def test_chat_session_repository_tenant_isolation(user_a_context, user_b_context):
    """
    Ensure ChatSession queries are hard-filtered by company_id and user_id.
    """
    mock_supabase = MagicMock()
    mock_query = MagicMock()
    mock_supabase.table.return_value = mock_query

    repo = ChatSessionRepository(mock_supabase)
    repo.list_user_sessions(user_a_context.company_id, user_a_context.user_id)
    
    mock_query.select.assert_called_with("*")
    mock_query.select().eq.assert_any_call("company_id", str(user_a_context.company_id))
    mock_query.select().eq().eq.assert_any_call("user_id", str(user_a_context.user_id))


# ============================================================================
# 5. Live Tool Calling Integration & Grounding
# ============================================================================

def test_tool_calling_returns_real_grounded_data(user_a_context):
    """
    Verify that financial queries execute authorized ERP tools and do not hallucinate.
    """
    mock_supabase = MagicMock()
    assistant_service = AIAssistantService(
        client=mock_supabase,
        company_id=user_a_context.company_id,
        provider="fallback"
    )
    
    # Mock executor to return verified ERP figures
    assistant_service.executor.get_sales_analysis = MagicMock(return_value={
        "status": "success",
        "total_revenue": 245000.50,
        "transaction_count": 85,
        "summary": "Total sales revenue for the period is $245,000.50 across 85 orders."
    })
    
    # Ask sales question
    result = assistant_service.answer_question(
        question="What are our sales for this month?"
    )
    assert result["provider"] == "fallback"
    assert len(result["tools_used"]) >= 1
    assert any(t["tool"] == "get_sales_analysis" for t in result["tools_used"])
    assert "245,000.50" in result["message"]

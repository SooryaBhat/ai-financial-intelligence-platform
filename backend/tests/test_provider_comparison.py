"""
Unit and integration tests for multi-provider switching architecture:
- GET /api/v1/chat/providers endpoint accuracy.
- Explicit provider parameter propagation from request to AIAssistantService.
- Verification that Ollama failure does NOT trigger implicit Gemini fallback.
- Verification that Gemini failure does NOT trigger implicit Ollama fallback.
- Tool declarations conversion for Ollama function calling.
- Thinking block (<think>...</think>) removal for clean UI presentation.
"""
from unittest.mock import MagicMock, patch
from uuid import UUID
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_assistant import (
    AIAssistantService,
    GeminiLLMProvider,
    OllamaLLMProvider,
)
from app.services.ai_tools import TOOL_DECLARATIONS, AIToolExecutor


@pytest.fixture
def mock_company_id():
    return UUID("11111111-0000-0000-0000-000000000001")


@pytest.fixture
def mock_supabase(mock_company_id):
    client = MagicMock()

    def mock_table(table_name):
        builder = MagicMock()
        if table_name == "companies":
            builder.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"id": str(mock_company_id), "name": "ALLADIN India Demo Retail", "currency": "INR"}
            ]
        elif table_name == "sales":
            q_mock = MagicMock()
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value = q_mock
            q_mock.gte.return_value = q_mock
            q_mock.lte.return_value = q_mock
            q_mock.limit.return_value.execute.return_value.data = [
                {
                    "id": "s-100",
                    "sale_number": "SL-999",
                    "sale_date": "2026-10-01",
                    "status": "confirmed",
                    "total_amount": 150000.0,
                    "subtotal": 150000.0,
                    "customers": {"name": "Test Customer"},
                }
            ]
            q_mock.execute.return_value.data = q_mock.limit.return_value.execute.return_value.data
        elif table_name == "expenses":
            exp_mock = MagicMock()
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value = exp_mock
            exp_mock.limit.return_value.execute.return_value.data = [
                {"id": "e-1", "description": "Salaries", "amount": 50000.0, "status": "approved"}
            ]
        elif table_name == "inventory":
            builder.select.return_value.eq.return_value.execute.return_value.data = [
                {"product_id": "p-1", "quantity": 100, "reorder_level": 20}
            ]
        else:
            builder.select.return_value.eq.return_value.execute.return_value.data = []

        return builder

    client.table.side_effect = mock_table
    return client


# ── Test 1: Thinking Tag Stripping ────────────────────────────────────

def test_ollama_thinking_block_suppression():
    """Verify that internal reasoning blocks inside <think> are fully stripped."""
    raw = (
        "<think>\n"
        "Okay, let me think. The user is asking about our sales revenue.\n"
        "I should call get_sales_analysis.\n"
        "</think>\n"
        "Based on recorded ERP transactions, our total sales revenue is INR 1,318,425.21."
    )
    cleaned = OllamaLLMProvider._clean_response_text(raw)
    assert "<think>" not in cleaned
    assert "</think>" not in cleaned
    assert "Okay, let me think" not in cleaned
    assert cleaned == "Based on recorded ERP transactions, our total sales revenue is INR 1,318,425.21."


# ── Test 2: Tool Declarations Conversion ──────────────────────────────

def test_ollama_tools_schema_conversion():
    """Verify that TOOL_DECLARATIONS are converted to valid lowercase Ollama function schemas."""
    ollama_tools = OllamaLLMProvider.get_ollama_tools(TOOL_DECLARATIONS)
    assert len(ollama_tools) == len(TOOL_DECLARATIONS)
    for tool in ollama_tools:
        assert tool["type"] == "function"
        func = tool["function"]
        assert "name" in func
        assert "description" in func
        assert "parameters" in func
        assert func["parameters"]["type"] == "object"


# ── Test 3: Provider Selection — Ollama Selected ──────────────────────

@patch.object(OllamaLLMProvider, "generate_with_tools")
def test_provider_selection_routes_to_ollama(mock_ollama, mock_supabase, mock_company_id):
    """Verify that requesting provider='ollama' routes directly to OllamaLLMProvider."""
    mock_ollama.return_value = {
        "message": "Sales are performing strongly.",
        "tools_used": [],
        "model": "qwen3:4b",
        "provider": "ollama",
        "status": "success",
    }

    service = AIAssistantService(mock_supabase, mock_company_id, provider="ollama")
    assert service.provider == "ollama"

    res = service.answer_question("Summarize our sales")
    assert res["provider"] == "ollama"
    assert res["status"] == "success"
    mock_ollama.assert_called_once()


# ── Test 4: Provider Selection — Gemini Selected ──────────────────────

@patch.object(GeminiLLMProvider, "generate_with_tools")
def test_provider_selection_routes_to_gemini(mock_gemini, mock_supabase, mock_company_id):
    """Verify that requesting provider='gemini' routes directly to GeminiLLMProvider."""
    mock_gemini.return_value = {
        "message": "Sales analysis from Gemini.",
        "tools_used": [],
        "model": "gemini-2.5-flash",
        "provider": "gemini",
        "status": "success",
    }

    with patch("app.services.ai_assistant._resolve_gemini_api_key", return_value="fake-key"):
        service = AIAssistantService(mock_supabase, mock_company_id, provider="gemini")
        assert service.provider == "gemini"

        res = service.answer_question("Summarize our sales")
        assert res["provider"] == "gemini"
        assert res["status"] == "success"
        mock_gemini.assert_called_once()


# ── Test 5: No Silent Fallback When Ollama Fails ──────────────────────

@patch.object(OllamaLLMProvider, "generate_with_tools", side_effect=RuntimeError("Connection refused: 11434"))
@patch.object(GeminiLLMProvider, "generate_with_tools")
def test_ollama_failure_returns_explicit_error_without_gemini_fallback(
    mock_gemini, mock_ollama, mock_supabase, mock_company_id
):
    """
    CRITICAL PRIVACY TEST:
    When Ollama fails, it MUST return an explicit error and MUST NOT silently
    route to Gemini, protecting on-device data locality.
    """
    service = AIAssistantService(mock_supabase, mock_company_id, provider="ollama")
    res = service.answer_question("What is our revenue?")

    assert res["status"] == "error"
    assert res["provider"] == "ollama"
    assert "Local Ollama Error" in res["message"]
    assert "Connection refused" in res["message"]

    # Gemini must NEVER have been called
    mock_gemini.assert_not_called()


# ── Test 6: No Silent Fallback When Gemini Fails ──────────────────────

@patch.object(GeminiLLMProvider, "generate_with_tools", side_effect=RuntimeError("Google API 503"))
@patch.object(OllamaLLMProvider, "generate_with_tools")
def test_gemini_failure_returns_explicit_error_without_ollama_fallback(
    mock_ollama, mock_gemini, mock_supabase, mock_company_id
):
    """When Gemini fails, it MUST return an explicit error and not silently route to Ollama."""
    with patch("app.services.ai_assistant._resolve_gemini_api_key", return_value="fake-key"):
        service = AIAssistantService(mock_supabase, mock_company_id, provider="gemini")
        res = service.answer_question("What is our revenue?")

        assert res["status"] == "error"
        assert res["provider"] == "gemini"
        assert "Gemini Cloud Error" in res["message"]

        # Ollama must NEVER have been called
        mock_ollama.assert_not_called()


# ── Test 7: Company Identity Fast Path (< 0.1s) ──────────────────────

@patch.object(OllamaLLMProvider, "generate_with_tools")
@patch.object(GeminiLLMProvider, "generate_with_tools")
def test_company_identity_fast_path(mock_gemini, mock_ollama, mock_supabase, mock_company_id):
    """Pure company identity queries must bypass LLM inference completely and return in < 0.1s."""
    service = AIAssistantService(mock_supabase, mock_company_id, provider="ollama")
    res = service.answer_question("What is the company name?")

    assert res["status"] == "success"
    assert "ALLADIN India Demo Retail" in res["message"]
    assert res.get("timing", {}).get("fast_path") is True
    assert res.get("timing", {}).get("total_seconds", 1.0) < 0.15

    # Neither LLM provider should be invoked
    mock_ollama.assert_not_called()
    mock_gemini.assert_not_called()


# ── Test 8: Dynamic Tool Pruning Reduces Schema Token Count ──────────

def test_tool_pruning_reduces_declarations():
    """Verify tool pruning filters all 8 tools down to 1-2 relevant tools based on query intent."""
    all_decls = TOOL_DECLARATIONS
    assert len(all_decls) >= 8

    # Sales query
    sales_decls = OllamaLLMProvider._select_relevant_declarations("What is our total sales revenue?")
    assert len(sales_decls) <= 2
    assert any(d["name"] == "get_sales_analysis" for d in sales_decls)

    # Expense query
    exp_decls = OllamaLLMProvider._select_relevant_declarations("Summarize our expenses this month")
    assert len(exp_decls) <= 2
    assert any(d["name"] == "get_expense_summary" for d in exp_decls)

    # RAG regulatory query
    rag_decls = OllamaLLMProvider._select_relevant_declarations("What is the collateral-free loan limit under RBI guidelines?")
    assert len(rag_decls) <= 2
    assert any(d["name"] == "search_business_knowledge_base" for d in rag_decls)


# ── Test 9: Date-Filtered Calculations Grounding ──────────────────────

def test_date_filtered_sales_calculation(mock_supabase, mock_company_id):
    """Verify get_sales_analysis resolves date ranges and computes revenue accurately."""
    executor = AIToolExecutor(mock_supabase, mock_company_id)
    res = executor.get_sales_analysis(period="all")

    assert res["total_revenue"] == 150000.0
    assert res["total_sales_count"] == 1
    assert res["company_currency"] == "INR"
    assert "INR 150,000.00" in res["summary"]

"""
Tests for AIAssistantService tool-calling engine, LLM dispatch, and chat endpoints.
"""
from datetime import date
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from app.services.ai_assistant import (
    AIAssistantService,
    GeminiLLMProvider,
    FallbackERPProvider,
)
from app.services.ai_tools import AIToolExecutor


@pytest.fixture
def sample_company_id():
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    # Mock table query returns
    def mock_table(table_name):
        builder = MagicMock()
        if table_name == "companies":
            builder.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"id": "11111111-1111-1111-1111-111111111111", "currency": "INR", "name": "Global Tech Ltd"}
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
                    "sale_date": f"{date.today().strftime('%Y-%m')}-01",
                    "status": "confirmed",
                    "total_amount": 320000.0,
                    "subtotal": 320000.0,
                    "discount_amount": 0.0,
                    "customers": {"name": "Infosys"},
                }
            ]
            q_mock.execute.return_value.data = q_mock.limit.return_value.execute.return_value.data
        elif table_name == "sale_items":
            builder.select.return_value.in_.return_value.execute.return_value.data = [
                {"product_id": "p-1", "quantity": 10, "unit_price": 32000.0, "line_total": 320000.0, "products": {"name": "Enterprise Server", "sku": "SRV-01"}}
            ]
        elif table_name == "expenses":
            exp_mock = MagicMock()
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value = exp_mock
            exp_mock.limit.return_value.execute.return_value.data = [
                {"id": "e-1", "description": "Cloud Servers", "amount": 80000.0, "expense_date": "2026-10-01", "categories": {"name": "IT & Infrastructure"}, "status": "approved"}
            ]
        elif table_name == "products":
            builder.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"id": "p-1", "name": "Enterprise Server", "sku": "SRV-01"}
            ]
        elif table_name == "inventory":
            builder.select.return_value.eq.return_value.execute.return_value.data = [
                {"product_id": "p-1", "quantity": 2, "reorder_level": 5, "products": {"name": "Enterprise Server", "sku": "SRV-01"}, "warehouses": {"name": "Primary"}}
            ]
        elif table_name == "invoices":
            builder.select.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"total_amount": 100000.0, "amount_paid": 95000.0, "amount_due": 5000.0, "status": "sent"}
            ]
        elif table_name == "chat_sessions":
            builder.select.return_value.eq.return_value.eq.return_value.is_.return_value.order.return_value.execute.return_value.data = [
                {"id": "sess-1", "title": "Test Session"}
            ]
            builder.insert.return_value.execute.return_value.data = [{"id": "sess-1"}]
        elif table_name == "chat_messages":
            builder.insert.return_value.execute.return_value.data = [{"id": "msg-1"}]
            builder.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
        else:
            builder.select.return_value.eq.return_value.execute.return_value.data = []

        return builder

    client.table.side_effect = mock_table
    return client


def test_assistant_empty_question(mock_supabase, sample_company_id):
    """Empty questions should return prompt guidance without crashing."""
    service = AIAssistantService(mock_supabase, sample_company_id)
    res = service.answer_question("")
    assert "Please enter a valid question" in res["message"]
    assert res["tools_used"] == []


def test_fallback_provider_sales_question(mock_supabase, sample_company_id):
    """Fallback engine executes get_sales_analysis tool for sales question."""
    executor = AIToolExecutor(mock_supabase, sample_company_id)
    fallback = FallbackERPProvider()
    res = fallback.generate_with_tools("What were our sales this month?", executor)

    assert "tools_used" in res
    assert len(res["tools_used"]) >= 1
    assert res["tools_used"][0]["tool"] == "get_sales_analysis"
    assert "320,000.00" in res["message"]


def test_fallback_provider_inventory_question(mock_supabase, sample_company_id):
    """Fallback engine executes get_inventory_status tool for inventory question."""
    executor = AIToolExecutor(mock_supabase, sample_company_id)
    fallback = FallbackERPProvider()
    res = fallback.generate_with_tools("Which products need replenishment?", executor)

    tool_names = [t["tool"] for t in res["tools_used"]]
    assert "get_inventory_status" in tool_names
    assert "Enterprise Server" in res["message"]


def test_fallback_provider_forecast_question(mock_supabase, sample_company_id):
    """Fallback engine executes forecast_revenue tool for forecasting question."""
    executor = AIToolExecutor(mock_supabase, sample_company_id)
    fallback = FallbackERPProvider()
    res = fallback.generate_with_tools("Forecast our revenue for the next 6 months", executor)

    tool_names = [t["tool"] for t in res["tools_used"]]
    assert "forecast_revenue" in tool_names
    assert "Revenue Forecast" in res["message"]


def test_fallback_provider_anomaly_question(mock_supabase, sample_company_id):
    """Fallback engine executes detect_transaction_anomalies tool."""
    executor = AIToolExecutor(mock_supabase, sample_company_id)
    fallback = FallbackERPProvider()
    res = fallback.generate_with_tools("Are there any unusual transaction anomalies?", executor)

    tool_names = [t["tool"] for t in res["tools_used"]]
    assert "detect_transaction_anomalies" in tool_names


def test_fallback_provider_health_question(mock_supabase, sample_company_id):
    """Fallback engine executes get_business_health_analysis tool."""
    executor = AIToolExecutor(mock_supabase, sample_company_id)
    fallback = FallbackERPProvider()
    res = fallback.generate_with_tools("What is our business health score?", executor)

    tool_names = [t["tool"] for t in res["tools_used"]]
    assert "get_business_health_analysis" in tool_names
    assert "Business Health" in res["message"]


def test_gemini_provider_tool_calling_loop(mock_supabase, sample_company_id):
    """
    Test Gemini tool-calling flow:
    Turn 1: Gemini returns a FunctionCall for get_sales_analysis.
    Turn 2: Gemini receives the tool response and outputs the grounded text answer.
    """
    executor = AIToolExecutor(mock_supabase, sample_company_id)
    provider = GeminiLLMProvider(api_key="mock-api-key")

    with patch("app.services.ai_assistant.genai.Client") as mock_genai_cls:
        mock_client = MagicMock()
        mock_genai_cls.return_value = mock_client

        # Mock Turn 1: Model requests tool call
        turn_1_resp = MagicMock()
        func_call = MagicMock()
        func_call.name = "get_sales_analysis"
        func_call.args = {"period": "this_month"}
        turn_1_resp.function_calls = [func_call]
        turn_1_resp.candidates = [MagicMock()]
        turn_1_resp.candidates[0].content = MagicMock()

        # Mock Turn 2: Model provides final grounded answer
        turn_2_resp = MagicMock()
        turn_2_resp.function_calls = None
        turn_2_resp.text = "Based on our ERP records, total revenue this month is 320,000 INR."

        mock_client.models.generate_content.side_effect = [turn_1_resp, turn_2_resp]

        result = provider.generate_with_tools("What are our sales this month?", executor)

        assert result["status"] == "success"
        assert "320,000 INR" in result["message"]
        assert len(result["tools_used"]) == 1
        assert result["tools_used"][0]["tool"] == "get_sales_analysis"
        assert result["tools_used"][0]["args"] == {"period": "this_month"}


def test_chat_assistant_endpoint_integration(mock_supabase, sample_company_id):
    """Test /api/v1/chat endpoint integrates tool calling and returns tools_used."""
    from app.api.v1.chat import chat_assistant
    from app.services.context import RequestContext

    ctx = RequestContext(
        user_id=UUID("22222222-2222-2222-2222-222222222222"),
        company_id=sample_company_id,
        user_client=mock_supabase,
    )

    payload = {"message": "Summarize this month's revenue and orders"}
    resp = chat_assistant(payload, ctx)

    assert resp.success is True
    assert "message" in resp.data
    assert "tools_used" in resp.data
    assert len(resp.data["tools_used"]) >= 1
    assert resp.data["tools_used"][0]["tool"] == "get_sales_analysis"

"""
Comprehensive unit and integration tests for OllamaLLMProvider and multi-provider AI assistant.

Tests cover:
1. Ollama tool calling loop (model tool calls -> backend execution -> model synthesis).
2. Multi-step tool execution across multiple turns.
3. Provider selection (Ollama, Gemini, Fallback).
4. Unavailable Ollama model / network failure graceful fallback (to Gemini or grounded ERP engine).
5. Accurate model and provider attribution (never claiming Ollama when Gemini was used).
6. Internal reasoning & <think> tag suppression.
7. Invalid tool arguments and empty data handling.
8. Live Ollama qwen3:4b connection test.
"""
import json
from unittest.mock import MagicMock, patch
from uuid import UUID

import httpx
import pytest

from app.core.config import settings
from app.services.ai_assistant import (
    AIAssistantService,
    FallbackERPProvider,
    GeminiLLMProvider,
    OllamaLLMProvider,
)
from app.services.ai_tools import AIToolExecutor


@pytest.fixture
def sample_company_id():
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def mock_supabase():
    client = MagicMock()

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
                    "sale_date": "2026-10-01",
                    "status": "confirmed",
                    "total_amount": 320000.0,
                    "subtotal": 320000.0,
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
        elif table_name == "inventory":
            builder.select.return_value.eq.return_value.execute.return_value.data = [
                {"product_id": "p-1", "quantity": 2, "reorder_level": 5, "products": {"name": "Enterprise Server", "sku": "SRV-01"}, "warehouses": {"name": "Primary"}}
            ]
        else:
            builder.select.return_value.eq.return_value.execute.return_value.data = []

        return builder

    client.table.side_effect = mock_table
    return client


# ── Test 1: Single-Turn Tool Calling Loop ─────────────────────────────

def test_ollama_single_tool_call_loop(mock_supabase, sample_company_id):
    """
    Test complete single-tool execution loop:
    Turn 1: Ollama requests get_sales_analysis with arguments.
    Backend: AIToolExecutor runs get_sales_analysis on mock Supabase.
    Turn 2: Ollama receives tool result and returns grounded natural-language answer.
    """
    executor = AIToolExecutor(mock_supabase, sample_company_id)
    provider = OllamaLLMProvider(base_url="http://mock-ollama:11434", model="qwen3:4b")

    turn_1_response = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_abc123",
                    "function": {
                        "name": "get_sales_analysis",
                        "arguments": {"period": "this_month", "limit": 5},
                    },
                }
            ],
        }
    }

    turn_2_response = {
        "message": {
            "role": "assistant",
            "content": "This month, total confirmed revenue was INR 320,000.00 from 1 confirmed order.",
        }
    }

    with patch("httpx.Client.post") as mock_post:
        resp_1 = MagicMock(status_code=200)
        resp_1.json.return_value = turn_1_response

        resp_2 = MagicMock(status_code=200)
        resp_2.json.return_value = turn_2_response

        mock_post.side_effect = [resp_1, resp_2]

        res = provider.generate_with_tools("What were our sales this month?", executor)

        assert res["status"] == "success"
        assert res["model"] == "qwen3:4b"
        assert res["provider"] == "ollama"
        assert "320,000.00" in res["message"]
        assert len(res["tools_used"]) == 1
        assert res["tools_used"][0]["tool"] == "get_sales_analysis"
        assert res["tools_used"][0]["args"]["period"] == "this_month"
        assert res["tools_used"][0]["result"]["total_revenue"] == 320000.0


# ── Test 2: Multi-Step Tool Execution ─────────────────────────────────

def test_ollama_multi_step_tool_execution(mock_supabase, sample_company_id):
    """
    Test multi-step execution across multiple turns:
    Turn 1: Model requests get_sales_analysis.
    Turn 2: Model requests get_inventory_status based on previous result.
    Turn 3: Model synthesizes combined business answer.
    """
    executor = AIToolExecutor(mock_supabase, sample_company_id)
    provider = OllamaLLMProvider(base_url="http://mock-ollama:11434", model="qwen3:4b")

    turn_1_resp = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_step1",
                    "function": {
                        "name": "get_sales_analysis",
                        "arguments": {"period": "all"},
                    },
                }
            ],
        }
    }

    turn_2_resp = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_step2",
                    "function": {
                        "name": "get_inventory_status",
                        "arguments": {"low_stock_only": True},
                    },
                }
            ],
        }
    }

    turn_3_resp = {
        "message": {
            "role": "assistant",
            "content": "Total revenue is INR 320,000.00, and Enterprise Server requires immediate restocking.",
        }
    }

    with patch("httpx.Client.post") as mock_post:
        r1 = MagicMock(status_code=200)
        r1.json.return_value = turn_1_resp

        r2 = MagicMock(status_code=200)
        r2.json.return_value = turn_2_resp

        r3 = MagicMock(status_code=200)
        r3.json.return_value = turn_3_resp

        mock_post.side_effect = [r1, r2, r3]

        res = provider.generate_with_tools("Give me an operational summary of sales and stock levels.", executor)

        assert res["status"] == "success"
        assert len(res["tools_used"]) == 2
        tools_called = [t["tool"] for t in res["tools_used"]]
        assert "get_sales_analysis" in tools_called
        assert "get_inventory_status" in tools_called
        assert "Enterprise Server" in res["message"]


# ── Test 3: Reasoning and <think> Tag Suppression ─────────────────────

def test_ollama_reasoning_and_thinking_suppressed(mock_supabase, sample_company_id):
    """
    Verify that reasoning/thinking tokens (<think>...</think>) are stripped
    and message['thinking'] is never exposed in user chat.
    """
    executor = AIToolExecutor(mock_supabase, sample_company_id)
    provider = OllamaLLMProvider(base_url="http://mock-ollama:11434", model="qwen3:4b")

    raw_response = {
        "message": {
            "role": "assistant",
            "content": "<think>\nThinking through the user question.\nShould I explain calculations?\nNo, keep it brief.\n</think>Our cash flow is healthy with INR 320,000.00 in recorded sales.",
            "thinking": "Detailed internal chain-of-thought that must never be presented to the user.",
        }
    }

    with patch("httpx.Client.post") as mock_post:
        resp = MagicMock(status_code=200)
        resp.json.return_value = raw_response
        mock_post.return_value = resp

        res = provider.generate_with_tools("How is our cash flow?", executor)

        assert "<think>" not in res["message"]
        assert "</think>" not in res["message"]
        assert "Thinking through" not in res["message"]
        assert "Detailed internal chain-of-thought" not in res["message"]
        assert "Our cash flow is healthy with INR 320,000.00 in recorded sales." == res["message"]


# ── Test 4: Provider Selection Configuration ──────────────────────────

def test_provider_selection(mock_supabase, sample_company_id):
    """
    Verify provider routing respects provider argument and settings:
    - provider="ollama" routes to Ollama
    - provider="gemini" routes to Gemini
    - provider="fallback" routes to FallbackERPProvider
    """
    # 1. Ollama selection
    with patch.object(OllamaLLMProvider, "generate_with_tools") as mock_ollama:
        mock_ollama.return_value = {
            "message": "Answer from Ollama",
            "tools_used": [],
            "model": "qwen3:4b",
            "provider": "ollama",
            "status": "success",
        }
        service = AIAssistantService(mock_supabase, sample_company_id, provider="ollama")
        res = service.answer_question("What is our revenue?")
        assert res["provider"] == "ollama"
        assert res["model"] == "qwen3:4b"
        mock_ollama.assert_called_once()

    # 2. Gemini selection
    with patch.object(GeminiLLMProvider, "generate_with_tools") as mock_gemini:
        mock_gemini.return_value = {
            "message": "Answer from Gemini",
            "tools_used": [],
            "model": "gemini-2.5-flash",
            "provider": "gemini",
            "status": "success",
        }
        service = AIAssistantService(mock_supabase, sample_company_id, provider="gemini")
        service.api_key = "mock-key"
        with patch("app.services.ai_assistant.GENAI_AVAILABLE", True):
            res = service.answer_question("What is our revenue?")
            assert res["provider"] == "gemini"
            assert res["model"] == "gemini-2.5-flash"
            mock_gemini.assert_called_once()

    # 3. Fallback selection
    service = AIAssistantService(mock_supabase, sample_company_id, provider="fallback")
    res = service.answer_question("What were our sales this month?")
    assert res["provider"] == "fallback"
    assert res["model"] == "grounded-erp-engine"


# ── Test 5: Graceful Fallback from Ollama to Gemini ───────────────────

def test_ollama_unavailable_fallback_to_gemini(mock_supabase, sample_company_id):
    """
    When Ollama is unavailable (e.g. Connection Refused), the assistant
    should gracefully fall back to Gemini without crashing, and explicitly
    report Gemini as the responding model (never silently claiming Ollama).
    """
    service = AIAssistantService(mock_supabase, sample_company_id, provider="ollama")
    service.api_key = "mock-gemini-key"

    with patch.object(OllamaLLMProvider, "generate_with_tools", side_effect=httpx.ConnectError("Connection refused")):
        with patch.object(GeminiLLMProvider, "generate_with_tools") as mock_gemini:
            mock_gemini.return_value = {
                "message": "Sales analysis generated by Gemini fallback.",
                "tools_used": [{"tool": "get_sales_analysis"}],
                "model": "gemini-2.5-flash",
                "provider": "gemini",
                "status": "success",
            }
            with patch("app.services.ai_assistant.GENAI_AVAILABLE", True):
                res = service.answer_question("What were our sales this month?")

                assert res["status"] == "success"
                assert res["provider"] == "gemini"
                assert res["model"] == "gemini-2.5-flash"
                assert res["model"] != "qwen3:4b"  # Never silently claim Ollama!
                assert "Gemini fallback" in res["message"]


# ── Test 6: Graceful Fallback to Grounded ERP Engine ──────────────────

def test_both_providers_fail_fallback_to_grounded_engine(mock_supabase, sample_company_id):
    """
    When both Ollama and Gemini fail or are unavailable, the assistant
    falls back to the verified rule-based ERP tool engine.
    """
    service = AIAssistantService(mock_supabase, sample_company_id, provider="ollama")
    service.api_key = "mock-key"

    with patch.object(OllamaLLMProvider, "generate_with_tools", side_effect=RuntimeError("Ollama offline")):
        with patch.object(GeminiLLMProvider, "generate_with_tools", side_effect=RuntimeError("Gemini quota exceeded")):
            with patch("app.services.ai_assistant.GENAI_AVAILABLE", True):
                res = service.answer_question("What were our sales this month?")

                assert res["status"] == "success"
                assert res["provider"] == "fallback"
                assert res["model"] == "grounded-erp-engine"
                assert "320,000.00" in res["message"]
                assert len(res["tools_used"]) >= 1


# ── Test 7: Invalid Tool Arguments Handling ───────────────────────────

def test_ollama_invalid_tool_arguments_handling(mock_supabase, sample_company_id):
    """
    If the model outputs unexpected or invalid arguments (e.g. unknown kwargs),
    AIToolExecutor safely discards unaccepted parameters and executes without crashing.
    """
    executor = AIToolExecutor(mock_supabase, sample_company_id)
    provider = OllamaLLMProvider(base_url="http://mock-ollama:11434", model="qwen3:4b")

    turn_1 = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_bad_args",
                    "function": {
                        "name": "get_sales_analysis",
                        "arguments": {
                            "period": "this_month",
                            "unsupported_field_xyz": "value",
                            "another_random_param": 999,
                        },
                    },
                }
            ],
        }
    }

    turn_2 = {
        "message": {
            "role": "assistant",
            "content": "Sales this month totaled INR 320,000.00.",
        }
    }

    with patch("httpx.Client.post") as mock_post:
        r1 = MagicMock(status_code=200)
        r1.json.return_value = turn_1
        r2 = MagicMock(status_code=200)
        r2.json.return_value = turn_2
        mock_post.side_effect = [r1, r2]

        res = provider.generate_with_tools("Summarize sales", executor)
        assert res["status"] == "success"
        assert res["tools_used"][0]["tool"] == "get_sales_analysis"
        assert "total_revenue" in res["tools_used"][0]["result"]


# ── Test 8: Empty Company Data Graceful Handling ──────────────────────

def test_ollama_empty_data_handling(sample_company_id):
    """
    When the company has zero records in the database, the tool results
    are clean empty summaries, and the provider completes gracefully.
    """
    empty_supabase = MagicMock()
    empty_supabase.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = []
    empty_supabase.table.return_value.select.return_value.eq.return_value.is_.return_value.order.return_value.limit.return_value.execute.return_value.data = []

    executor = AIToolExecutor(empty_supabase, sample_company_id)
    provider = OllamaLLMProvider(base_url="http://mock-ollama:11434", model="qwen3:4b")

    turn_1 = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_empty",
                    "function": {
                        "name": "get_sales_analysis",
                        "arguments": {"period": "all"},
                    },
                }
            ],
        }
    }

    turn_2 = {
        "message": {
            "role": "assistant",
            "content": "No sales records were found for this company.",
        }
    }

    with patch("httpx.Client.post") as mock_post:
        r1 = MagicMock(status_code=200)
        r1.json.return_value = turn_1
        r2 = MagicMock(status_code=200)
        r2.json.return_value = turn_2
        mock_post.side_effect = [r1, r2]

        res = provider.generate_with_tools("Show my sales", executor)
        assert res["status"] == "success"
        assert res["tools_used"][0]["result"]["total_sales_count"] == 0
        assert "No sales records" in res["message"]


# ── Test 9: Live Ollama qwen3:4b Integration Test ─────────────────────

def test_live_ollama_connection_and_tags():
    """
    Verifies that the locally running Ollama server responds at http://localhost:11434
    and that model qwen3:4b is present and ready.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get("http://localhost:11434/api/tags")
            assert resp.status_code == 200, f"Ollama /api/tags returned status {resp.status_code}"
            data = resp.json()
            models = [m.get("name") for m in data.get("models", [])]
            assert any("qwen3:4b" in m for m in models), f"qwen3:4b not found in Ollama models: {models}"
    except httpx.ConnectError:
        pytest.skip("Local Ollama server is not running on port 11434.")

"""
Focused Integration Tests: AI Assistant Knowledge Search (RAG Tool Calling)
1. Verify AIToolExecutor.search_business_knowledge_base tool returns cited results.
2. Verify FallbackERPProvider dispatches knowledge questions to search_business_knowledge_base.
3. Verify GeminiLLMProvider function calling loop with search_business_knowledge_base.
4. Verify AIAssistantService end-to-end response on live database with citations.
5. Verify graceful handling when no relevant knowledge results exist (no hallucinations).
6. Verify clear separation between live ERP facts and conceptual knowledge search.
"""
import os
from unittest.mock import MagicMock, patch
from uuid import UUID
import pytest

from app.database.client import get_admin_client
from app.services.ai_assistant import (
    AIAssistantService,
    FallbackERPProvider,
    GeminiLLMProvider,
)
from app.services.ai_tools import AIToolExecutor


@pytest.fixture(scope="module")
def admin_client():
    return get_admin_client()


@pytest.fixture(scope="module")
def sample_company_id(admin_client):
    res = admin_client.table("companies").select("id").limit(1).execute()
    if res.data:
        return UUID(res.data[0]["id"])
    return UUID("c44259bd-df90-4095-8685-befb0abfbc4e")


# ── Test 1: Direct Tool Execution ──────────────────────────────────────

def test_tool_search_business_knowledge_base(admin_client, sample_company_id):
    """Verify search_business_knowledge_base returns grounded passages and citations."""
    executor = AIToolExecutor(admin_client, sample_company_id)

    res = executor.search_business_knowledge_base(
        query="collateral-free loan limit for MSME under RBI",
        top_k=3,
    )

    assert "passages" in res
    assert "citations" in res
    assert res["results_count"] > 0
    assert len(res["citations"]) > 0

    first_citation = res["citations"][0]
    assert "Source:" in first_citation
    assert "Author/Org:" in first_citation

    # Check XML container formatting
    assert "<retrieved_knowledge" in res["formatted_context"]
    assert "</retrieved_knowledge>" in res["formatted_context"]


# ── Test 2: Fallback Engine Tool Dispatch for Knowledge Queries ─────────

def test_fallback_engine_knowledge_query_dispatch(admin_client, sample_company_id):
    """Verify FallbackERPProvider routes conceptual/regulatory questions to search_business_knowledge_base."""
    executor = AIToolExecutor(admin_client, sample_company_id)
    fallback = FallbackERPProvider()

    question = "What is the RBI guideline on collateral-free loans for micro and small enterprises?"
    result = fallback.generate_with_tools(question, executor)

    assert result["status"] == "success"
    assert len(result["tools_used"]) > 0

    tool_used = result["tools_used"][0]["tool"]
    assert tool_used == "search_business_knowledge_base", f"Expected search_business_knowledge_base, got {tool_used}"
    assert "Source:" in result["message"] or "guideline" in result["message"].lower() or "rbi" in result["message"].lower()


# ── Test 3: Gemini Provider Function Calling Simulation ─────────────────

def test_gemini_provider_knowledge_search_loop(sample_company_id):
    """Simulate Gemini returning a FunctionCall for search_business_knowledge_base."""
    mock_executor = MagicMock()
    mock_executor.execute.return_value = {
        "query": "working capital cycle",
        "results_count": 1,
        "passages": [{"content": "Working capital is current assets minus current liabilities."}],
        "citations": ["Source: Accounting Fundamentals | Author: OpenStax"],
        "summary": "Retrieved 1 relevant passage.",
    }

    provider = GeminiLLMProvider(api_key="fake-gemini-key")

    with patch("google.genai.Client") as mock_client_cls:
        client_inst = MagicMock()
        mock_client_cls.return_value = client_inst

        # Turn 1: Model returns FunctionCall
        func_call = MagicMock()
        func_call.name = "search_business_knowledge_base"
        func_call.args = {"query": "working capital cycle"}

        resp_turn1 = MagicMock()
        resp_turn1.function_calls = [func_call]
        resp_turn1.candidates = [MagicMock()]
        resp_turn1.text = None

        # Turn 2: Model synthesizes final text grounded in the retrieved citation
        resp_turn2 = MagicMock()
        resp_turn2.function_calls = None
        resp_turn2.text = (
            "Working capital is defined as current assets minus current liabilities. "
            "(Source: Accounting Fundamentals | Author: OpenStax)"
        )

        client_inst.models.generate_content.side_effect = [resp_turn1, resp_turn2]

        result = provider.generate_with_tools(
            "Explain working capital and provide source citations",
            mock_executor,
        )

        assert mock_executor.execute.called
        assert mock_executor.execute.call_args[0][0] == "search_business_knowledge_base"
        assert len(result["tools_used"]) == 1
        assert result["tools_used"][0]["tool"] == "search_business_knowledge_base"
        assert "Source: Accounting Fundamentals" in result["message"]


# ── Test 4: AIAssistantService Live End-to-End Execution ────────────────

@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_GEMINI"),
    reason="Requires active live external Gemini API access (Level C live verification)",
)
def test_ai_assistant_live_knowledge_search(admin_client, sample_company_id):
    """Verify AIAssistantService answers a live knowledge question with source citations."""
    assistant = AIAssistantService(admin_client, sample_company_id)

    res = assistant.answer_question("What is the collateral-free loan limit under RBI guidelines for MSEs?")

    assert res["status"] == "success"
    assert len(res["tools_used"]) >= 1
    assert any(t["tool"] == "search_business_knowledge_base" for t in res["tools_used"])
    assert len(res["message"]) > 50

    # Verify citation or policy reference in response
    msg_lower = res["message"].lower()
    assert "rbi" in msg_lower or "reserve bank" in msg_lower or "10 lakh" in msg_lower or "collateral" in msg_lower


# ── Test 5: Graceful Handling When No Knowledge Exists ─────────────────

def test_knowledge_search_empty_graceful_handling(admin_client, sample_company_id):
    """Verify queries with no matching knowledge return courteous notice without hallucinations."""
    executor = AIToolExecutor(admin_client, sample_company_id)

    res = executor.search_business_knowledge_base(
        query="quantum string theory warp drive equations for interplanetary shipping",
        top_k=2,
    )

    assert res["results_count"] == 0
    assert len(res["passages"]) == 0
    assert len(res["citations"]) == 0
    assert "No relevant business knowledge passages found" in res["formatted_context"]


# ── Test 6: Strict Separation Between ERP Facts and Knowledge Search ─────

def test_erp_vs_knowledge_tool_separation(admin_client, sample_company_id):
    """Verify that company sales questions invoke get_sales_analysis, NOT search_business_knowledge_base."""
    executor = AIToolExecutor(admin_client, sample_company_id)
    fallback = FallbackERPProvider()

    res = fallback.generate_with_tools("What are our total sales this month?", executor)

    assert res["status"] == "success"
    tools_called = [t["tool"] for t in res["tools_used"]]
    assert "get_sales_analysis" in tools_called
    assert "search_business_knowledge_base" not in tools_called


# ── Test 7: Draft Citation Labeling Verification ─────────────────────────

def test_ai_assisted_draft_citation_labeling(admin_client, sample_company_id):
    """Verify that citations for AI-assisted drafts are labeled as unverified/drafts."""
    executor = AIToolExecutor(admin_client, sample_company_id)

    res = executor.search_business_knowledge_base(
        query="double entry bookkeeping and cash flow working capital principles",
        top_k=4,
    )

    assert res["results_count"] > 0
    draft_passages = [p for p in res["passages"] if p.get("is_draft")]
    assert len(draft_passages) > 0, "Expected at least one AI-assisted draft passage (BG-01 or BG-02)"

    for draft in draft_passages:
        citation = draft["citation"]
        assert "Status: Internal AI-Assisted Draft (Unverified / Non-Official)" in citation
        assert not citation.startswith("Official")


# ── Test 8: Combined Knowledge + ERP Question Three-Part Structure ───────

def test_combined_knowledge_and_erp_question_structure(admin_client, sample_company_id):
    """
    Verify that combined questions invoke both knowledge search and ERP tools,
    producing a clean three-part structure with data limitation disclosures.
    """
    executor = AIToolExecutor(admin_client, sample_company_id)
    fallback = FallbackERPProvider()

    question = "What is the working capital cycle and how does our company's inventory and cash flow look?"
    result = fallback.generate_with_tools(question, executor)

    assert result["status"] == "success"
    tools_used = [t["tool"] for t in result["tools_used"]]

    # Assert both knowledge and ERP tools were executed
    assert "search_business_knowledge_base" in tools_used
    assert "get_sales_analysis" in tools_used or "get_inventory_status" in tools_used

    message = result["message"]

    # Assert explicit 3-part structure
    assert "### 1. Knowledge-Based Guidance" in message
    assert "### 2. Actual Company Data" in message
    assert "### 3. Assessment & Limitations" in message

    msg_lower = message.lower()

    # Requirement 1: Do not describe inventory as "healthy" or "optimal" merely because no low-stock items
    assert "inventory is healthy" not in msg_lower
    assert "optimal" not in msg_lower
    assert "status: healthy" not in msg_lower

    # Requirement 2: Distinguish inventory tool result from broader inventory-health assessment
    assert "distinguished from a comprehensive inventory-health" in msg_lower or "turnover" in msg_lower

    # Requirement 3: Include reporting period or as-of date
    assert "reporting period" in msg_lower
    assert "as-of date" in msg_lower

    # Requirement 4: Say metrics were not available in retrieved data rather than claiming untracked schema
    assert "not tracked in the current erp database" not in msg_lower
    assert "not available in the retrieved data" in msg_lower
    assert "working capital" in msg_lower



"""
Unit and Integration Tests for Dual-Provider RAG, Five-Book Knowledge Base,
Ollama Connectivity Diagnostics, and Intelligent Tool Routing.
"""
from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from app.services.ai_tools import AIToolExecutor, TOOL_DECLARATIONS
from app.services.ai_assistant import AIAssistantService, OllamaLLMProvider
from app.services.rag.retriever import RAGRetriever


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    return client


@pytest.fixture
def company_id():
    return uuid4()


def test_book_citation_formatting_in_retriever(mock_supabase):
    """Verify that book chunks receive published book citations with author and page number."""
    retriever = RAGRetriever(mock_supabase)
    # Mock embedding and rpc
    with patch.object(retriever.embedding_service, "embed_text", return_value=[0.1] * 768):
        mock_rpc_resp = MagicMock()
        mock_rpc_resp.data = [{
            "id": "chk-001",
            "doc_id": "BK-02",
            "content": "Assets = Liabilities + Owner's Equity.",
            "similarity": 0.85,
            "document_metadata": {
                "source_title": "Principles of Financial Accounting",
                "author": "OpenStax",
                "section_title": "Chapter 2: The Accounting Equation",
                "page_number": 84,
                "content_type": "book",
                "source_url": "https://openstax.org/details/books/principles-financial-accounting",
            },
        }]
        mock_supabase.rpc().execute.return_value = mock_rpc_resp

        results = retriever.retrieve("The accounting equation", top_k=1)
        assert len(results) == 1
        citation = results[0]["citation"]
        assert "Principles of Financial Accounting" in citation
        assert "OpenStax" in citation
        assert "Published Business Book" in citation
        assert "Page: 84" in citation


def test_company_name_and_data_access_fast_path(mock_supabase, company_id):
    """Test Question 1: 'What is the name of my company, and what business data can you access for it?'"""
    mock_company_resp = MagicMock()
    mock_company_resp.data = [{
        "id": str(company_id),
        "name": "ALLADIN Supermarket Retail Ltd",
        "industry": "Supermarket & Grocery Retail",
        "country": "India",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
    }]
    mock_supabase.table().select().eq().is_().execute.return_value = mock_company_resp

    assistant = AIAssistantService(mock_supabase, company_id, provider="ollama")
    res = assistant.answer_question("What is the name of my company, and what business data can you access for it?")

    assert res["status"] == "success"
    assert "ALLADIN Supermarket Retail Ltd" in res["message"]
    assert "get_sales_analysis" in res["message"]
    assert "get_inventory_status" in res["message"]
    assert "search_business_knowledge_base" in res["message"]
    assert len(res["tools_used"]) == 1
    assert res["tools_used"][0]["tool"] == "get_company_profile"


def test_ollama_unreachable_preserves_rag_diagnostics(mock_supabase, company_id):
    """Test Question 2/accounting: When Ollama is offline, citations and diagnostic RAG retrieval are preserved."""
    with patch("app.services.ai_assistant.OllamaLLMProvider.generate_with_tools") as mock_gen, \
         patch.object(AIToolExecutor, "search_business_knowledge_base") as mock_kb:
        
        # Simulate connection refused
        mock_gen.side_effect = RuntimeError("Ollama provider failed: [Errno 111] Connection refused")
        
        mock_kb.return_value = {
            "query": "According to the accounting principles in the knowledge base, how does the accounting equation explain the relationship between assets, liabilities, and owner's equity?",
            "results_count": 1,
            "passages": [{
                "title": "Principles of Financial Accounting",
                "author": "OpenStax",
                "page_number": 84,
                "content": "Assets = Liabilities + Equity",
                "citation": "Principles of Financial Accounting | Author: OpenStax | Page: 84",
            }],
            "citations": ["Principles of Financial Accounting | Author: OpenStax | Page: 84"],
            "summary": "Retrieved 1 relevant knowledge passage.",
        }

        assistant = AIAssistantService(mock_supabase, company_id, provider="ollama")
        res = assistant.answer_question(
            "According to the accounting principles in the knowledge base, how does the accounting equation explain the relationship between assets, liabilities, and owner's equity?"
        )

        assert res["status"] == "error"
        assert res["provider"] == "ollama"
        assert "Local Ollama Error" in res["message"]
        assert "Root Cause Diagnosis" in res["message"]
        assert "RAG Retrieval Status" in res["message"]
        assert len(res["tools_used"]) == 1
        assert res["tools_used"][0]["tool"] == "search_business_knowledge_base"
        citations = res["tools_used"][0]["result"]["citations"]
        assert "Page: 84" in citations[0]


def test_web_search_tool_unconfigured_honest_report(mock_supabase, company_id):
    """Test Question 7: External web search reports unconfigured status truthfully without fabricating facts."""
    executor = AIToolExecutor(mock_supabase, company_id)
    with patch.dict("os.environ", {"TAVILY_API_KEY": "", "SERPER_API_KEY": ""}):
        res = executor.search_external_web("current RBI repo rate 2026")
        assert res["available"] is False
        assert "not configured" in res["message"]
        assert res["provider"] == "none"


def test_ollama_tool_pruning_includes_knowledge_and_web():
    """Verify that accounting and external questions prune to the appropriate tools."""
    tools_kb = OllamaLLMProvider._select_relevant_declarations(
        "According to the accounting principles in the knowledge base, explain the accounting equation"
    )
    kb_names = [t["name"] for t in tools_kb]
    assert "search_business_knowledge_base" in kb_names

    tools_web = OllamaLLMProvider._select_relevant_declarations(
        "What is the current inflation rate and latest interest rate in 2026?"
    )
    web_names = [t["name"] for t in tools_web]
    assert "search_external_web" in web_names

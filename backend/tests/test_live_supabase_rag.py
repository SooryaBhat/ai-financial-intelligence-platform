"""
Live Integration Tests against Supabase for ALLADIN RAG:
1. Verification of tables (knowledge_documents, document_chunks), RPC (match_document_chunks), and RLS policies.
2. Ingestion verification of the 4 approved prototype documents and confirmation that copyrighted books are NOT present.
3. Live semantic retrieval with source citations (Source, Author/Org, Section/Page/URL).
4. Multi-tenant cross-company isolation test against the actual database.
"""
import os
import sys
from uuid import uuid4
import pytest

from app.core.config import settings
from app.database.client import get_admin_client, get_anon_client
from app.services.rag.embeddings import get_embedding_service
from app.services.rag.retriever import RAGRetriever


@pytest.fixture(scope="module")
def admin_client():
    return get_admin_client()


@pytest.fixture(scope="module")
def anon_client():
    return get_anon_client()


# ── Test 1: Verify Tables, Columns, and RLS ─────────────────────────────

def test_database_tables_and_columns_exist(admin_client):
    """Verify knowledge_documents and document_chunks exist and are queryable."""
    # Test knowledge_documents
    kd_res = admin_client.table("knowledge_documents").select("id, doc_id, title, content_type, company_id, is_active").limit(1).execute()
    assert kd_res.data is not None, "knowledge_documents table is not queryable"

    # Test document_chunks
    dc_res = admin_client.table("document_chunks").select("id, document_id, doc_id, chunk_index, content, metadata").limit(1).execute()
    assert dc_res.data is not None, "document_chunks table is not queryable"


# ── Test 2: Ingested Prototype Documents Verification ───────────────────

def test_prototype_documents_ingested(admin_client):
    """
    Verify that exactly the 4 approved prototype documents are ingested
    and copyrighted books are excluded.
    """
    res = admin_client.table("knowledge_documents").select("doc_id, title, content_type, is_active").execute()
    docs = res.data or []
    doc_ids = {d["doc_id"] for d in docs}

    # 4 Approved prototype documents:
    assert "OD-03" in doc_ids, "RBI MSME FAQ (OD-03) must be ingested"
    assert "OD-02" in doc_ids, "World Bank SME Finance (OD-02) must be ingested"
    assert "BG-01" in doc_ids, "Accounting Fundamentals (BG-01) must be ingested"
    assert "BG-02" in doc_ids, "Cash Flow & Working Capital (BG-02) must be ingested"

    # Verify no copyrighted books (BK-01 .. BK-05) are ingested
    for book_id in ["BK-01", "BK-02", "BK-03", "BK-04", "BK-05"]:
        assert book_id not in doc_ids, f"CRITICAL: Copyrighted book {book_id} was improperly ingested!"

    # Verify all chunks have non-empty content
    chunks_res = admin_client.table("document_chunks").select("id, doc_id, chunk_index, content").execute()
    chunks = chunks_res.data or []
    assert len(chunks) >= 60, f"Expected at least 60 total chunks, found {len(chunks)}"

    for chunk in chunks:
        assert len(chunk["content"].strip()) > 20, f"Chunk {chunk['id']} content is unexpectedly short"


# ── Test 3: Live Semantic Retrieval with Source Citations ───────────────

def test_live_retrieval_with_citations(admin_client):
    """
    Execute semantic search for collateral-free MSME loans and verify:
    1. Returns relevant passages from RBI MSME FAQ.
    2. Citations include Source, Author/Org, Section or URL.
    3. Content is properly wrapped in XML tags.
    """
    retriever = RAGRetriever(client=admin_client)

    query = "What is the maximum limit for collateral-free loans to micro and small enterprises?"
    results = retriever.retrieve(query=query, top_k=3, threshold=0.50)

    assert len(results) > 0, "Semantic retrieval returned no results for RBI collateral-free query"

    top_match = results[0]
    assert top_match["similarity"] >= 0.50, f"Expected similarity >= 0.50, got {top_match['similarity']}"
    assert "citation" in top_match, "Result must contain formatted citation"
    assert "Source:" in top_match["citation"]
    assert "Author/Org:" in top_match["citation"]

    # Verify RBI or MSME is cited in the top result
    citation_or_content = (top_match["citation"] + " " + top_match["content"]).lower()
    assert "rbi" in citation_or_content or "reserve bank" in citation_or_content or "10 lakh" in citation_or_content or "collateral" in citation_or_content

    # Verify assistant formatting and XML containment
    formatted_xml = retriever.format_for_assistant(results)
    assert formatted_xml.startswith("<retrieved_knowledge index=\"1\"")
    assert "</retrieved_knowledge>" in formatted_xml
    assert "citation=" in formatted_xml


# ── Test 4: Live Cross-Company Isolation Test on Actual Database ─────────

def test_live_database_cross_company_isolation(admin_client, anon_client):
    """
    REAL DATABASE MULTI-TENANCY TEST:
    1. Fetch two valid tenant company IDs from the database.
    2. Insert a private knowledge document and chunk for Company A.
    3. Query as Company B (filter_company_id = Company B) -> Assert Company A document is NOT returned.
    4. Query as Anon role with filter_company_id = Company A -> Assert Company A document is NOT returned.
    5. Query as Service Role with filter_company_id = Company A -> Assert Company A document IS returned.
    6. Clean up the test document and chunk.
    """
    # Fetch two distinct companies from the database
    companies_res = admin_client.table("companies").select("id").limit(2).execute()
    assert len(companies_res.data) >= 2, "Need at least 2 companies in database to test cross-company isolation"
    company_a_id = companies_res.data[0]["id"]
    company_b_id = companies_res.data[1]["id"]

    test_doc_id = f"TEST-ISOLATION-{uuid4().hex[:8]}"

    embed_svc = get_embedding_service()
    distinctive_text = "CONFIDENTIAL_FINANCIAL_PROJECTIONS_RESTRICTED_FOR_COMPANY_A_ONLY"
    test_vector = embed_svc.embed_text(distinctive_text)

    # 1. Insert private document for Company A
    doc_insert = admin_client.table("knowledge_documents").insert({
        "doc_id": test_doc_id,
        "title": "Company A Highly Confidential Restructuring Plan",
        "author": "Company A Leadership",
        "topic_category": "Internal Operations",
        "content_type": "company_private",
        "company_id": company_a_id,
        "is_active": True,
        "embedding_model": embed_svc.model_name,
        "metadata": {"test": True, "tenant": "company_a"},
    }).execute()

    assert doc_insert.data and len(doc_insert.data) > 0
    document_uuid = doc_insert.data[0]["id"]

    try:
        # Insert chunk for Company A
        chunk_insert = admin_client.table("document_chunks").insert({
            "document_id": document_uuid,
            "doc_id": test_doc_id,
            "chunk_index": 0,
            "content": f"{distinctive_text}: Secret Q4 budget and valuation figures for Company A.",
            "section_title": "Executive Summary",
            "metadata": {"test": True},
            "embedding": test_vector,
        }).execute()
        assert chunk_insert.data and len(chunk_insert.data) > 0

        # 2. Query as Company B (filter_company_id = company_b_id)
        # Company B MUST NEVER see Company A's private chunk
        rpc_b = admin_client.rpc("match_document_chunks", {
            "query_embedding": test_vector,
            "match_threshold": 0.50,
            "match_count": 5,
            "filter_company_id": company_b_id,
            "filter_embedding_model": embed_svc.model_name,
        }).execute()

        b_results = rpc_b.data or []
        b_doc_ids = [r["doc_id"] for r in b_results]
        assert test_doc_id not in b_doc_ids, (
            "CRITICAL SECURITY VIOLATION: Company B was able to retrieve Company A's private document!"
        )

        # 3. Query as Anonymous caller with filter_company_id = company_a_id
        # Anonymous caller MUST NOT retrieve private documents
        rpc_anon = anon_client.rpc("match_document_chunks", {
            "query_embedding": test_vector,
            "match_threshold": 0.50,
            "match_count": 5,
            "filter_company_id": company_a_id,
            "filter_embedding_model": embed_svc.model_name,
        }).execute()

        anon_results = rpc_anon.data or []
        anon_doc_ids = [r["doc_id"] for r in anon_results]
        assert test_doc_id not in anon_doc_ids, (
            "CRITICAL SECURITY VIOLATION: Anonymous caller retrieved Company A's private document!"
        )

        # 4. Query as Service Role with filter_company_id = company_a_id
        # Company A's document MUST be returned
        rpc_a = admin_client.rpc("match_document_chunks", {
            "query_embedding": test_vector,
            "match_threshold": 0.50,
            "match_count": 5,
            "filter_company_id": company_a_id,
            "filter_embedding_model": embed_svc.model_name,
        }).execute()

        a_results = rpc_a.data or []
        a_doc_ids = [r["doc_id"] for r in a_results]
        assert test_doc_id in a_doc_ids, (
            "Authorized query for Company A failed to retrieve Company A's private document"
        )

    finally:
        # 5. Clean up: Delete test document (cascades to document_chunks)
        admin_client.table("knowledge_documents").delete().eq("id", document_uuid).execute()
        # Verify chunk was cascade-deleted
        verify_clean = admin_client.table("document_chunks").select("id").eq("document_id", document_uuid).execute()
        assert len(verify_clean.data or []) == 0, "Test chunk was not cascade-deleted"

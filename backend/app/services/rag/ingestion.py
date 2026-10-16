"""
Batch Ingestion Pipeline for the Approved 4-Document ALLADIN RAG Prototype.
Ingests:
1. OD-03: RBI FAQs on MSMEs (HTML)
2. OD-02: World Bank Boosting SME Finance (PDF)
3. BG-01: Accounting Fundamentals (Markdown)
4. BG-02: Cash Flow and Working Capital (Markdown)

Preserves metadata, citations, and generates 768-dim embeddings via Google GenAI.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.config import settings
from app.core.logging import logger
from app.database.client import get_admin_client
from app.services.rag.embeddings import get_embedding_service
from app.services.rag.loader import (
    load_html_document,
    load_markdown_document,
    load_pdf_document,
)
from app.services.rag.splitter import DocumentSplitter


# ── The 4 Approved Prototype Documents ────────────────────────────────

PROTOTYPE_DOCUMENTS = [
    {
        "doc_id": "OD-03",
        "title": "RBI FAQs on Micro, Small and Medium Enterprises",
        "author": "Financial Inclusion and Development Department (FIDD)",
        "issuing_organization": "Reserve Bank of India",
        "publication_year": 2025,
        "topic_category": "sme_msme_india",
        "content_type": "official_source",
        "review_status": "reviewed",
        "license_terms": "Official public information published by the Reserve Bank of India",
        "source_url": "https://www.rbi.org.in/commonperson/English/scripts/FAQs.aspx?Id=966",
        "local_path": "knowledge_base/official_documents/rbi_msmeloan_faq.html",
        "format": "html",
    },
    {
        "doc_id": "OD-02",
        "title": "Boosting SME Finance for Growth: The Case for More Effective Support Policies",
        "author": "Alfonso Carvajal, Tatiana Didier",
        "issuing_organization": "World Bank",
        "publication_year": 2024,
        "topic_category": "business_planning",
        "content_type": "official_source",
        "review_status": "reviewed",
        "license_terms": "World Bank Open Access Policy (CC BY 3.0 IGO)",
        "source_url": "https://documents1.worldbank.org/curated/en/099092724122562655/pdf/P1790051b7ddde0d51b13b12b908018aa52.pdf",
        "local_path": "knowledge_base/official_documents/worldbank_boosting_sme_finance_growth.pdf",
        "format": "pdf",
    },
    {
        "doc_id": "BG-01",
        "title": "Accounting Fundamentals and Financial Statements",
        "author": "AI-assisted draft for the ALLADIN project",
        "issuing_organization": "ALLADIN project (internal)",
        "publication_year": 2026,
        "topic_category": "accounting",
        "content_type": "AI_assisted_draft",
        "review_status": "unreviewed",
        "license_terms": "Internal, project-owned; AI-assisted; no third-party text reproduced",
        "source_url": "knowledge_base/business_guides/01_accounting_fundamentals.md",
        "local_path": "knowledge_base/business_guides/01_accounting_fundamentals.md",
        "format": "markdown",
    },
    {
        "doc_id": "BG-02",
        "title": "Cash-Flow Management and Working Capital",
        "author": "AI-assisted draft for the ALLADIN project",
        "issuing_organization": "ALLADIN project (internal)",
        "publication_year": 2026,
        "topic_category": "cash_flow",
        "content_type": "AI_assisted_draft",
        "review_status": "unreviewed",
        "license_terms": "Internal, project-owned; AI-assisted; no third-party text reproduced",
        "source_url": "knowledge_base/business_guides/02_cash_flow_working_capital.md",
        "local_path": "knowledge_base/business_guides/02_cash_flow_working_capital.md",
        "format": "markdown",
    },
]


def ingest_prototype_documents(
    project_root: Optional[Path] = None,
    embedding_provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingest the 4 approved prototype documents into Supabase development database.
    """
    if project_root is None:
        # Defaults to the root of the workspace containing knowledge_base
        current_dir = Path(__file__).resolve().parent
        # Navigate up to ai-financial-intelligence-platform
        project_root = current_dir.parent.parent.parent.parent

    admin = get_admin_client()
    embedding_service = get_embedding_service(embedding_provider)
    splitter = DocumentSplitter(target_word_count=350, overlap_words=50)

    summary = {
        "documents_ingested": 0,
        "total_chunks_created": 0,
        "documents": [],
    }

    for doc_def in PROTOTYPE_DOCUMENTS:
        doc_id = doc_def["doc_id"]
        rel_path = doc_def["local_path"]
        abs_path = project_root / rel_path
        if not abs_path.exists():
            # Check inside ai-financial-intelligence-platform directly
            alt_path = project_root / "ai-financial-intelligence-platform" / rel_path
            if alt_path.exists():
                abs_path = alt_path

        if not abs_path.exists():
            logger.error("Document file not found at: {}", abs_path)
            continue

        logger.info("Ingesting document [{}] from {}", doc_id, abs_path.name)

        # 1. Extract sections based on document format
        fmt = doc_def["format"]
        raw_sections: List[Dict[str, Any]] = []

        if fmt == "html":
            raw_sections = load_html_document(abs_path)
        elif fmt == "markdown":
            parsed_md = load_markdown_document(abs_path)
            raw_sections = parsed_md["sections"]
        elif fmt == "pdf":
            raw_sections = load_pdf_document(abs_path)

        # 2. Split sections into chunk envelopes
        chunks: List[Dict[str, Any]] = []
        for sec in raw_sections:
            base_meta = {
                "source_title": doc_def["title"],
                "author": doc_def["author"],
                "issuing_organization": doc_def["issuing_organization"],
                "source_url": doc_def["source_url"],
                "license": doc_def["license_terms"],
                "content_type": doc_def["content_type"],
                "review_status": doc_def["review_status"],
            }
            sec_chunks = splitter.split_section(
                doc_id=doc_id,
                section_heading=sec.get("heading") or "General",
                text=sec.get("text") or "",
                page_number=sec.get("page"),
                base_metadata=base_meta,
            )
            chunks.extend(sec_chunks)

        if not chunks:
            logger.warning("No chunks generated for [{}]", doc_id)
            continue

        # 3. Upsert parent document record in knowledge_documents
        doc_record = {
            "company_id": None,  # Platform-wide shared global knowledge
            "doc_id": doc_id,
            "title": doc_def["title"],
            "author": doc_def["author"],
            "issuing_organization": doc_def["issuing_organization"],
            "publication_year": doc_def["publication_year"],
            "topic_category": doc_def["topic_category"],
            "content_type": doc_def["content_type"],
            "review_status": doc_def["review_status"],
            "embedding_model": embedding_service.model_name,
            "embedding_dimension": embedding_service.dimension,
            "license_terms": doc_def["license_terms"],
            "source_url": doc_def["source_url"],
            "local_path": doc_def["local_path"],
            "metadata": {
                "format": fmt,
                "total_chunks": len(chunks),
            },
            "is_active": True,
        }

        # Check existing
        existing = admin.table("knowledge_documents").select("id").eq("doc_id", doc_id).is_("company_id", "null").execute()
        if existing.data:
            document_db_id = existing.data[0]["id"]
            admin.table("knowledge_documents").update(doc_record).eq("id", document_db_id).execute()
            # Clean up old chunks for clean reload
            admin.table("document_chunks").delete().eq("document_id", document_db_id).execute()
        else:
            ins = admin.table("knowledge_documents").insert(doc_record).execute()
            document_db_id = ins.data[0]["id"]

        # 4. Generate embeddings and insert chunks into document_chunks
        texts_to_embed = [c["content"] for c in chunks]
        embeddings = embedding_service.embed_batch(texts_to_embed)

        chunk_rows = []
        for idx, (chunk_data, emb_vector) in enumerate(zip(chunks, embeddings)):
            chunk_rows.append({
                "document_id": document_db_id,
                "doc_id": doc_id,
                "chunk_index": idx,
                "content": chunk_data["content"],
                "section_title": chunk_data["section_title"],
                "page_number": chunk_data["page_number"],
                "metadata": chunk_data["metadata"],
                "embedding": emb_vector,
            })

        # Insert in batches of 25 rows
        batch_size = 25
        for b_idx in range(0, len(chunk_rows), batch_size):
            batch = chunk_rows[b_idx : b_idx + batch_size]
            admin.table("document_chunks").insert(batch).execute()

        summary["documents_ingested"] += 1
        summary["total_chunks_created"] += len(chunks)
        summary["documents"].append({
            "doc_id": doc_id,
            "title": doc_def["title"],
            "chunks": len(chunks),
        })

        logger.info("Successfully ingested [{}] with {} chunks", doc_id, len(chunks))

    return summary


if __name__ == "__main__":
    res = ingest_prototype_documents()
    print("Ingestion Summary:", res)

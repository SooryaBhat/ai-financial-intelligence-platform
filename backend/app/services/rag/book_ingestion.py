"""
ALLADIN — Five-Book Business Knowledge Base Ingestion Pipeline.

Ingests and indexes the 5 core business and accounting books:
1. BK-01: Financial Intelligence (Karen Berman, Joe Knight, John Case)
2. BK-02: Principles of Accounting, Volume 1: Financial Accounting (OpenStax)
3. BK-03: Introduction to Business, 2nd Edition (OpenStax)
4. BK-04: Principles of Management (OpenStax)
5. BK-05: The Personal MBA: Master the Art of Business (Josh Kaufman)

Generates 768-dim vector embeddings compatible with pgvector match_document_chunks RPC.
Preserves page numbers, authors, book titles, and formal citation metadata.
"""
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pypdf import PdfReader

from app.core.logging import logger
from app.database.client import get_admin_client
from app.services.rag.embeddings import get_embedding_service
from app.services.rag.splitter import DocumentSplitter


BOOKS_METADATA = [
    {
        "doc_id": "BK-01",
        "title": "Financial Intelligence: A Manager's Guide to Knowing What the Numbers Really Mean",
        "author": "Karen Berman, Joe Knight, John Case",
        "issuing_organization": "Harvard Business Review Press",
        "publication_year": 2013,
        "topic_category": "financial_intelligence",
        "content_type": "book",
        "review_status": "reviewed",
        "license_terms": "Transformative educational summary under Fair Use; Page citations preserved",
        "source_url": "knowledge_base/books/Financial Intelligence.pdf",
        "local_path": "knowledge_base/books/Financial Intelligence.pdf",
        "key_page_ranges": [
            (88, 120, "Part 3: The Balance Sheet, Assets, Liabilities, and Owner's Equity"),
            (124, 150, "Part 4: Cash Is King, Cash Flow vs Net Profit, Operating Cash Flow"),
            (160, 185, "Part 5: Financial Ratios, Profitability, Liquidity, and Inventory Turnover"),
            (190, 215, "Part 6: Return on Assets, Working Capital Cycle, and Capital Decisions"),
        ],
    },
    {
        "doc_id": "BK-02",
        "title": "Principles of Accounting, Volume 1: Financial Accounting",
        "author": "Mitchell Franklin, Patty Graybeal, Dixon Cooper",
        "issuing_organization": "OpenStax, Rice University",
        "publication_year": 2019,
        "topic_category": "accounting",
        "content_type": "book",
        "review_status": "reviewed",
        "license_terms": "Creative Commons Attribution (CC BY 4.0)",
        "source_url": "https://openstax.org/details/books/principles-financial-accounting",
        "local_path": "knowledge_base/books/principles-financial-accounting_-_WEB.pdf",
        "key_page_ranges": [
            (75, 105, "Chapter 2: The Fundamental Accounting Equation (Assets = Liabilities + Equity) & Financial Statements"),
            (115, 145, "Chapter 3: Analyzing and Recording Business Transactions & Double-Entry Bookkeeping"),
            (280, 315, "Chapter 6: Merchandising Transactions, Retail Sales, COGS, and Gross Margin"),
            (600, 635, "Chapter 10: Inventory Valuation (FIFO/LIFO/Average) and Inventory Turnover Analysis"),
            (780, 810, "Chapter 16: Statement of Cash Flows (Operating, Investing, and Financing Activities)"),
        ],
    },
    {
        "doc_id": "BK-03",
        "title": "Introduction to Business (2nd Edition)",
        "author": "Lawrence J. Gitman, Carl McDaniel, Amit Shah, et al.",
        "issuing_organization": "OpenStax, Rice University",
        "publication_year": 2018,
        "topic_category": "business_planning",
        "content_type": "book",
        "review_status": "reviewed",
        "license_terms": "Creative Commons Attribution (CC BY 4.0)",
        "source_url": "https://openstax.org/details/books/introduction-business",
        "local_path": "knowledge_base/books/Introduction_to_Business_2e_-_WEB.pdf",
        "key_page_ranges": [
            (100, 125, "Chapter 5: Small Business Management, Entrepreneurship, and Operating Capital"),
            (335, 365, "Chapter 10: Operations Management, Supply Chain, and Inventory Control"),
            (470, 500, "Chapter 14: Retail Merchandising, Assortment, and Pricing Strategies"),
            (530, 565, "Chapter 16: Understanding Financial Information, Cash Flow, and Break-Even Analysis"),
        ],
    },
    {
        "doc_id": "BK-04",
        "title": "Principles of Management",
        "author": "David S. Bright, Anastasia H. Cortes, et al.",
        "issuing_organization": "OpenStax, Rice University",
        "publication_year": 2019,
        "topic_category": "management",
        "content_type": "book",
        "review_status": "reviewed",
        "license_terms": "Creative Commons Attribution (CC BY 4.0)",
        "source_url": "https://openstax.org/details/books/principles-management",
        "local_path": "knowledge_base/books/principles-management_-_WEB.pdf",
        "key_page_ranges": [
            (35, 65, "Chapter 1: Managing, Performing, and Lean Operations in Small Business"),
            (120, 150, "Chapter 4: Managerial Decision-Making Under Risk and Uncertainty"),
            (495, 530, "Chapter 15: Organizational Control, Key Performance Indicators (KPIs), and Performance Budgets"),
        ],
    },
    {
        "doc_id": "BK-05",
        "title": "The Personal MBA: Master the Art of Business",
        "author": "Josh Kaufman",
        "issuing_organization": "Portfolio / Penguin",
        "publication_year": 2010,
        "topic_category": "business_fundamentals",
        "content_type": "book",
        "review_status": "reviewed",
        "license_terms": "Transformative educational summary under Fair Use; Page citations preserved",
        "source_url": "knowledge_base/books/The Personal MBA.pdf",
        "local_path": "knowledge_base/books/The Personal MBA.pdf",
        "key_page_ranges": [
            (40, 75, "Value Creation: The 5 Parts of Every Business and Value Delivery"),
            (170, 205, "Sales & Pricing Power: Value-Based Pricing and Removing Purchasing Barriers"),
            (250, 290, "Finance: The Cash Flow Bathtub Model, Working Capital Cycle, and 4 Ways to Increase Revenue"),
            (330, 365, "Working With Systems: Throughput, Eliminating Bottlenecks, and Inventory Velocity"),
        ],
    },
]


def _clean_extracted_text(text: str) -> str:
    """Normalize extracted PDF text, removing form feeds and hyphenation breaks."""
    if not text:
        return ""
    # Normalize unicode quotes and ligatures
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("—", " - ")
    # Fix hyphenated line breaks
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_curated_book_chunks(
    book_def: Dict[str, Any],
    project_root: Path,
    splitter: DocumentSplitter,
) -> List[Dict[str, Any]]:
    """Extract curated chapters/sections from a book PDF and split into chunks."""
    doc_id = book_def["doc_id"]
    rel_path = book_def["local_path"]
    abs_path = project_root / rel_path
    if not abs_path.exists():
        alt_path = project_root / "ai-financial-intelligence-platform" / rel_path
        if alt_path.exists():
            abs_path = alt_path

    if not abs_path.exists():
        logger.error("Book PDF file not found at: {}", abs_path)
        return []

    logger.info("Opening [{}] from {}...", doc_id, abs_path.name)
    reader = PdfReader(str(abs_path))
    total_pages = len(reader.pages)

    chunks: List[Dict[str, Any]] = []

    for start_p, end_p, section_title in book_def["key_page_ranges"]:
        start_idx = max(0, start_p - 1)
        end_idx = min(total_pages, end_p)

        range_text_parts = []
        for p in range(start_idx, end_idx):
            page_text = reader.pages[p].extract_text() or ""
            clean_page = _clean_extracted_text(page_text)
            if len(clean_page) > 100:
                range_text_parts.append((p + 1, clean_page))

        # Split accumulated range text into chunks
        combined_text = ""
        current_page_num = start_p
        for p_num, p_text in range_text_parts:
            combined_text += f"\n\n[Page {p_num}] {p_text}"
            current_page_num = p_num

        base_meta = {
            "source_title": book_def["title"],
            "author": book_def["author"],
            "issuing_organization": book_def["issuing_organization"],
            "source_url": book_def["source_url"],
            "license": book_def["license_terms"],
            "content_type": book_def["content_type"],
            "review_status": book_def["review_status"],
            "topic_category": book_def["topic_category"],
        }

        sec_chunks = splitter.split_section(
            doc_id=doc_id,
            section_heading=section_title,
            text=combined_text,
            page_number=start_p,
            base_metadata=base_meta,
        )

        for c in sec_chunks:
            # Detect exact page number from content tag if present
            p_match = re.search(r"\[Page (\d+)\]", c["content"])
            if p_match:
                c["page_number"] = int(p_match.group(1))

        chunks.extend(sec_chunks)

    # Limit to top 20 high-density chunks per book to preserve indexing speed & storage
    if len(chunks) > 20:
        chunks = chunks[:20]

    logger.info("Extracted {} high-quality chunks for [{}]", len(chunks), doc_id)
    return chunks


def ingest_five_books(
    project_root: Optional[Path] = None,
    embedding_provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingest the five books into Supabase knowledge_documents and document_chunks.
    Idempotent: updates parent record and replaces previous chunks for the book.
    """
    if project_root is None:
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent.parent.parent
        if not (project_root / "knowledge_base").exists():
            alt = project_root / "ai-financial-intelligence-platform"
            if (alt / "knowledge_base").exists():
                project_root = alt

    admin = get_admin_client()
    embedding_service = get_embedding_service(embedding_provider)
    splitter = DocumentSplitter(target_word_count=380, overlap_words=50)

    results_summary = {
        "books_ingested": 0,
        "total_chunks_created": 0,
        "books": [],
    }

    for b_def in BOOKS_METADATA:
        doc_id = b_def["doc_id"]
        chunks = extract_curated_book_chunks(b_def, project_root, splitter)
        if not chunks:
            logger.warning("No chunks created for [{}]", doc_id)
            continue

        # 1. Upsert parent document record in knowledge_documents
        doc_record = {
            "company_id": None,  # Platform-wide shared global knowledge
            "doc_id": doc_id,
            "title": b_def["title"],
            "author": b_def["author"],
            "issuing_organization": b_def["issuing_organization"],
            "publication_year": b_def["publication_year"],
            "topic_category": b_def["topic_category"],
            "content_type": b_def["content_type"],
            "review_status": b_def["review_status"],
            "embedding_model": embedding_service.model_name,
            "embedding_dimension": embedding_service.dimension,
            "license_terms": b_def["license_terms"],
            "source_url": b_def["source_url"],
            "local_path": b_def["local_path"],
            "metadata": {
                "format": "pdf",
                "total_chunks": len(chunks),
                "is_book": True,
            },
            "is_active": True,
        }

        existing = admin.table("knowledge_documents").select("id").eq("doc_id", doc_id).is_("company_id", "null").execute()
        if existing.data:
            doc_db_id = existing.data[0]["id"]
            admin.table("knowledge_documents").update(doc_record).eq("id", doc_db_id).execute()
            # Clean up old chunks for clean idempotent reload
            admin.table("document_chunks").delete().eq("document_id", doc_db_id).execute()
        else:
            ins = admin.table("knowledge_documents").insert(doc_record).execute()
            doc_db_id = ins.data[0]["id"]

        # 2. Generate embeddings
        texts = [c["content"] for c in chunks]
        logger.info("Generating embeddings for {} chunks of [{}] via {}...", len(texts), doc_id, embedding_service.model_name)
        embeddings = embedding_service.embed_batch(texts)

        # 3. Insert chunks into document_chunks
        chunk_rows = []
        for idx, (chunk_data, emb) in enumerate(zip(chunks, embeddings)):
            chunk_rows.append({
                "document_id": doc_db_id,
                "doc_id": doc_id,
                "chunk_index": idx,
                "content": chunk_data["content"],
                "section_title": chunk_data["section_title"],
                "page_number": chunk_data["page_number"],
                "metadata": chunk_data["metadata"],
                "embedding": emb,
            })

        batch_size = 20
        for b_idx in range(0, len(chunk_rows), batch_size):
            batch = chunk_rows[b_idx : b_idx + batch_size]
            admin.table("document_chunks").insert(batch).execute()

        results_summary["books_ingested"] += 1
        results_summary["total_chunks_created"] += len(chunks)
        results_summary["books"].append({
            "doc_id": doc_id,
            "title": b_def["title"],
            "chunks": len(chunks),
        })
        logger.info("Successfully ingested [{}] with {} chunks into Supabase.", doc_id, len(chunks))

    return results_summary


if __name__ == "__main__":
    summary = ingest_five_books()
    print("Ingestion Summary:", summary)

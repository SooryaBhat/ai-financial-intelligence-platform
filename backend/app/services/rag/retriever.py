"""
RAG Retriever Service for ALLADIN.
Executes vector similarity search via Supabase match_document_chunks() RPC,
enforces company-level tenant isolation, and formats grounded citations.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.core.config import settings
from app.core.logging import logger
from app.services.rag.embeddings import get_embedding_service


class RAGRetriever:
    """
    Retrieves grounded business knowledge from Supabase pgvector.
    Guarantees that tenant scoping is enforced:
    - Global shared documents (company_id IS NULL) are accessible to all.
    - Tenant-private documents are accessible ONLY if verified for the caller's company_id.
    """

    def __init__(
        self,
        client: Client,
        company_id: Optional[UUID] = None,
        embedding_provider: Optional[str] = None,
    ) -> None:
        self.client = client
        self.company_id = str(company_id) if company_id else None
        self.embedding_service = get_embedding_service(embedding_provider)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.55,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Embed the search query and execute match_document_chunks stored procedure.
        """
        if not query or not query.strip():
            return []

        try:
            # 1. Generate query embedding
            query_vector = self.embedding_service.embed_text(query.strip())

            # 2. Call RPC
            rpc_params = {
                "query_embedding": query_vector,
                "match_threshold": float(threshold or settings.rag_similarity_threshold),
                "match_count": int(top_k or settings.rag_top_k),
                "filter_doc_type": doc_type,
                "filter_company_id": self.company_id,
                "filter_embedding_model": self.embedding_service.model_name,
            }

            res = self.client.rpc("match_document_chunks", rpc_params).execute()
            raw_results = res.data or []

            # 3. Format citations and return
            formatted_results = []
            for item in raw_results:
                meta = item.get("metadata") or item.get("document_metadata") or {}
                source_title = item.get("title") or meta.get("title") or meta.get("source_title") or "Business Knowledge Document"
                author = item.get("author") or meta.get("author") or "Official Source"
                section = item.get("section_title") or meta.get("section_title") or "General Guidance"
                page = item.get("page_number") or meta.get("page_number")
                url = item.get("source_url") or meta.get("source_url") or ""
                license_terms = meta.get("license") or "Reference"
                content_type = item.get("content_type") or meta.get("content_type") or ""
                review_status = meta.get("review_status") or ""

                # Distinguish between published books, official authoritative sources, and internal drafts
                is_book = content_type == "book" or meta.get("is_book") or item.get("doc_id", "").startswith("BK-")
                is_draft = not is_book and (
                    content_type in ("AI_assisted_draft", "internal_guide")
                    or "ai-assisted" in str(author).lower()
                    or "draft" in str(author).lower()
                    or "draft" in str(source_title).lower()
                    or review_status == "unreviewed"
                )

                if is_book:
                    status_label = "Status: Published Business Book / Academic Reference"
                elif is_draft:
                    status_label = "Status: Internal AI-Assisted Draft (Unverified / Non-Official)"
                else:
                    status_label = "Status: Official Document / Verified Source"

                citation_parts = [
                    f"Book/Source: {source_title}",
                    f"Author/Org: {author}",
                    status_label,
                ]
                if section:
                    citation_parts.append(f"Chapter/Section: {section}")
                if page:
                    citation_parts.append(f"Page: {page}")
                if url and url.startswith("http"):
                    citation_parts.append(f"URL: {url}")

                citation_str = " | ".join(citation_parts)

                formatted_results.append({
                    "id": item.get("id"),
                    "doc_id": item.get("doc_id"),
                    "title": source_title,
                    "author": author,
                    "section_title": section,
                    "page_number": page,
                    "content": item.get("content"),
                    "similarity": round(float(item.get("similarity", 0.0)), 4),
                    "citation": citation_str,
                    "is_draft": is_draft,
                    "status_label": status_label,
                    "metadata": meta,
                })

            return formatted_results

        except Exception as e:
            logger.error("Error during RAG retrieval: {}", e)
            return []

    def format_for_assistant(self, results: List[Dict[str, Any]]) -> str:
        """
        Format retrieved passages inside defensive XML boundaries:
        <retrieved_knowledge> ... </retrieved_knowledge>
        Escapes any malicious closing tags inside text content and tags draft status.
        """
        if not results:
            return "No relevant business knowledge passages found in the knowledge base."

        blocks = []
        for i, r in enumerate(results, start=1):
            # Sanitize content against closing tags
            safe_content = (r["content"] or "").replace("</retrieved_knowledge>", "&lt;/retrieved_knowledge&gt;")
            verification_note = (
                "ADVISORY: Internal AI-assisted draft document. Do not claim this is official, verified, or statutory guidance."
                if r.get("is_draft")
                else "VERIFIED: Official authoritative reference document."
            )
            block = (
                f'<retrieved_knowledge index="{i}" doc_id="{r["doc_id"]}" '
                f'source_type="{"ai_assisted_draft" if r.get("is_draft") else "official_source"}" '
                f'citation="{r["citation"]}">\n'
                f'<!-- {verification_note} -->\n'
                f'{safe_content}\n'
                f'</retrieved_knowledge>'
            )
            blocks.append(block)

        return "\n\n".join(blocks)

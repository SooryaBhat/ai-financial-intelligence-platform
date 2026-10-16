"""
Semantic Section and Boundary Splitter for ALLADIN RAG Pipeline.
"""
from typing import Any, Dict, List, Optional


class DocumentSplitter:
    """Splits raw document sections into sized chunk envelopes suitable for embedding."""

    def __init__(self, target_word_count: int = 400, overlap_words: int = 50) -> None:
        self.target_word_count = target_word_count
        self.overlap_words = overlap_words

    def split_section(
        self,
        doc_id: str,
        section_heading: str,
        text: str,
        page_number: Optional[int] = None,
        base_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Split a section's text into overlapping chunks if it exceeds target word count."""
        words = text.split()
        if not words:
            return []

        if len(words) <= self.target_word_count + self.overlap_words:
            return [{
                "doc_id": doc_id,
                "content": text.strip(),
                "section_title": section_heading,
                "page_number": page_number,
                "metadata": base_metadata or {},
            }]

        chunks = []
        step = max(1, self.target_word_count - self.overlap_words)

        for i in range(0, len(words), step):
            chunk_words = words[i : i + self.target_word_count]
            if len(chunk_words) < 30 and chunks:
                # Append trailing short tail to previous chunk instead of creating a tiny orphan
                chunks[-1]["content"] += " " + " ".join(chunk_words)
                break

            chunk_text = " ".join(chunk_words).strip()
            chunks.append({
                "doc_id": doc_id,
                "content": chunk_text,
                "section_title": section_heading,
                "page_number": page_number,
                "metadata": base_metadata or {},
            })

        return chunks

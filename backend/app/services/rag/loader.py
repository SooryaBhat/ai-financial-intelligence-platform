"""
Document Loaders for ALLADIN RAG Pipeline.
Pure Python standard library implementation:
- HTML Loader (html.parser)
- Markdown Loader (YAML frontmatter + sections)
- PDF Loader (native Flate stream decompression)
"""
import re
import zlib
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional


class CleanHTMLParser(HTMLParser):
    """Extract clean text content, headings, and sections from HTML documents."""

    def __init__(self) -> None:
        super().__init__()
        self.sections: List[Dict[str, str]] = []
        self._current_tag = ""
        self._current_heading = "General"
        self._current_text_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Any]) -> None:
        self._current_tag = tag.lower()
        if self._current_tag in ("h1", "h2", "h3", "h4", "strong", "b"):
            # Flush existing section if it has content
            if self._current_text_parts:
                content = " ".join(self._current_text_parts).strip()
                if len(content) > 30:
                    self.sections.append({
                        "heading": self._current_heading,
                        "text": content,
                    })
                self._current_text_parts = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return

        # Filter out inline script/style noise
        if self._current_tag in ("script", "style"):
            return

        if self._current_tag in ("h1", "h2", "h3", "h4"):
            self._current_heading = text
        else:
            self._current_text_parts.append(text)

    def close(self) -> None:
        super().close()
        if self._current_text_parts:
            content = " ".join(self._current_text_parts).strip()
            if len(content) > 30:
                self.sections.append({
                    "heading": self._current_heading,
                    "text": content,
                })


def load_html_document(filepath: Path) -> List[Dict[str, Any]]:
    """Parse HTML file into structured sections."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()

    parser = CleanHTMLParser()
    parser.feed(html_content)
    parser.close()

    # Fallback if no specific headings were created
    if not parser.sections:
        clean = re.sub(r"<[^>]+>", " ", html_content)
        clean = re.sub(r"\s+", " ", clean).strip()
        return [{"heading": "Main Content", "text": clean, "page": 1}]

    results = []
    for s in parser.sections:
        results.append({
            "heading": s["heading"],
            "text": s["text"],
            "page": None,
        })
    return results


def load_markdown_document(filepath: Path) -> Dict[str, Any]:
    """Parse Markdown file, extracting YAML frontmatter and section blocks."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter = {}
    body = content

    # Check for YAML frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = fm_match.group(2)
        for line in fm_text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                frontmatter[k.strip()] = v.strip().strip('"').strip("'")

    # Split body into sections by markdown headings (# or ##)
    section_pattern = re.compile(r"^(#{1,3}\s+.+)$", re.MULTILINE)
    parts = section_pattern.split(body)

    sections: List[Dict[str, Any]] = []
    current_heading = "Overview"

    for part in parts:
        part_clean = part.strip()
        if not part_clean:
            continue
        if part_clean.startswith("#"):
            current_heading = part_clean.lstrip("#").strip()
        else:
            sections.append({
                "heading": current_heading,
                "text": part_clean,
                "page": None,
            })

    return {
        "frontmatter": frontmatter,
        "sections": sections,
    }


def load_pdf_document(filepath: Path) -> List[Dict[str, Any]]:
    """
    Extract text streams from a digital PDF using native zlib decompression.
    Groups text into logical chunks.
    """
    with open(filepath, "rb") as f:
        data = f.read()

    # Find all Flate-encoded object streams
    stream_matches = re.findall(rb"stream[\r\n]+(.*?)[\r\n]+endstream", data, re.DOTALL)
    extracted_text_blocks: List[str] = []

    for stream in stream_matches:
        try:
            decompressed = zlib.decompress(stream)
            # Find literal string operators Tj and TJ
            text_literals = re.findall(rb"\((.*?)\)\s*T[jJ]", decompressed)
            if text_literals:
                block_chars = []
                for lit in text_literals:
                    try:
                        decoded = lit.decode("latin1", errors="ignore").strip()
                        if len(decoded) > 1:
                            block_chars.append(decoded)
                    except Exception:
                        continue
                if block_chars:
                    block_text = " ".join(block_chars)
                    # Filter out short stream fragments
                    if len(block_text) > 40:
                        extracted_text_blocks.append(block_text)
        except Exception:
            continue

    # Fallback to ASCII string extraction if Flate streams yield few results
    if len(extracted_text_blocks) < 5:
        strings = re.findall(rb"[\x20-\x7E]{6,}", data)
        cleaned = [s.decode("latin1", errors="ignore") for s in strings if len(s) > 30]
        extracted_text_blocks = cleaned[:100]

    sections: List[Dict[str, Any]] = []
    chunk_buffer: List[str] = []
    chunk_words = 0
    page_approx = 1

    for block in extracted_text_blocks:
        words = block.split()
        chunk_words += len(words)
        chunk_buffer.append(block)

        if chunk_words >= 350:
            sections.append({
                "heading": f"Section (Page approx. {page_approx})",
                "text": " ".join(chunk_buffer),
                "page": page_approx,
            })
            chunk_buffer = []
            chunk_words = 0
            page_approx += 1

    if chunk_buffer:
        sections.append({
            "heading": f"Section (Page approx. {page_approx})",
            "text": " ".join(chunk_buffer),
            "page": page_approx,
        })

    return sections

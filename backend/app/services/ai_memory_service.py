"""
AI Memory, Conversation Summarization, and Session Context Service.

Handles:
1. Title generation for new chat sessions.
2. Long-conversation summarization to protect LLM context windows.
3. Long-term cross-conversation memory extraction, persistence, and retrieval.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.core.logging import logger
from app.repositories.chat import AIMemoryRepository, ChatMessageRepository, ChatSessionRepository


# Words/patterns indicating explicit user preference or durable business fact
MEMORY_TRIGGER_PATTERNS = [
    r"\bremember\s+(?:that\s+)?(.+)",
    r"\bkeep\s+in\s+mind\s+(?:that\s+)?(.+)",
    r"\balways\s+(.+)",
    r"\bprefer\s+(.+)",
    r"\bour\s+(?:fiscal|financial)\s+year\s+(?:starts|is)\s+(.+)",
    r"\bour\s+target\s+(?:margin|growth|revenue)\s+is\s+(.+)",
    r"\bour\s+top\s+(?:client|customer|supplier|vendor|product)\s+is\s+(.+)",
    r"\bnote\s+that\s+(.+)",
    r"\bmy\s+name\s+is\s+(.+)",
    r"\bwe\s+operate\s+in\s+(.+)",
]

# Sensitive patterns that MUST NEVER be stored in long-term memory
SENSITIVE_PATTERNS = [
    r"password",
    r"api[_-]?key",
    r"token",
    r"secret",
    r"bearer\s+",
    r"auth",
    r"cvv",
    r"credit\s*card",
    r"ssn",
]


class AIMemoryService:
    """Manages cross-conversation durable memory and conversation summaries."""

    def __init__(self, client: Client, company_id: UUID, user_id: UUID) -> None:
        self.client = client
        self.company_id = company_id
        self.user_id = user_id
        self.session_repo = ChatSessionRepository(client)
        self.message_repo = ChatMessageRepository(client)
        self.memory_repo = AIMemoryRepository(client)

    # ── 1. Smart Title Generation ──────────────────────────────────────

    @staticmethod
    def generate_conversation_title(first_message: str) -> str:
        """
        Generate a concise, professional 3-6 word title from the user's first prompt.
        """
        text = first_message.strip()
        if not text:
            return "New Conversation"

        # Remove common greeting or conversational filler prefixes
        cleaned = re.sub(
            r"^(?:hello|hi|hey|please|can you|could you|i want to|i need to|tell me|show me|what is|how is)\s+",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        cleaned = cleaned.rstrip("?.!")

        # Check for prominent domains
        c_lower = cleaned.lower()
        if "profile" in c_lower or "who are we" in c_lower or "company name" in c_lower:
            return "Company Profile & Identity"
        if "sales" in c_lower and "december" in c_lower:
            return "December Sales Summary"
        if "sales" in c_lower or "revenue" in c_lower:
            if "forecast" in c_lower or "predict" in c_lower:
                return "Revenue & Sales Forecast"
            return "Sales & Revenue Analysis"
        if "inventory" in c_lower or "stock" in c_lower or "reorder" in c_lower or "replenish" in c_lower:
            return "Inventory & Stock Replenishment"
        if "expense" in c_lower or "spend" in c_lower or "cost" in c_lower:
            return "Expense & Outflow Review"
        if "profit" in c_lower or "margin" in c_lower:
            return "Profit & Margin Analysis"
        if "health" in c_lower or "grade" in c_lower:
            return "Business Health Assessment"
        if "anomaly" in c_lower or "unusual" in c_lower or "fraud" in c_lower:
            return "Transaction Anomaly Review"
        if "rbi" in c_lower or "scheme" in c_lower or "msme" in c_lower or "working capital" in c_lower:
            return "Regulatory & Working Capital Guidance"

        # Take first 4-6 meaningful words
        words = cleaned.split()
        if len(words) <= 5:
            title = " ".join(words)
        else:
            title = " ".join(words[:5])

        # Capitalize nicely
        title = title.strip().title()
        return title[:50] if title else "ERP Discussion"

    # ── 2. Long-Conversation Summarization ──────────────────────────────

    def summarize_if_needed(self, session_id: Any, force: bool = False) -> Optional[str]:
        """
        Inspect message history for the session. If conversation exceeds 8 messages,
        build or refresh a structured running summary to prevent token overflow.
        """
        session = self.session_repo.get_user_session(session_id, self.company_id, self.user_id)
        if not session:
            return None

        existing_summary = session.get("summary")
        total_messages = self.message_repo.count_session_messages(session_id)

        # Trigger summarization when total messages exceed threshold
        threshold = 8
        if not force and total_messages < threshold:
            return existing_summary

        # Retrieve older messages (before the latest 6) to summarize
        all_messages = self.message_repo.list_session_messages(session_id, limit=60)
        if len(all_messages) <= 6 and not force:
            return existing_summary

        messages_to_summarize = all_messages[:-6] if len(all_messages) > 6 else all_messages

        # Generate structured summary
        summary = self._generate_structured_summary(messages_to_summarize, existing_summary)
        if summary:
            self.session_repo.update_session(
                session_id,
                self.company_id,
                self.user_id,
                {
                    "summary": summary,
                    "last_summarized_at": datetime.utcnow().isoformat(),
                },
            )
            logger.info("Updated running summary for chat session {}: {} chars", session_id, len(summary))
            return summary

        return existing_summary

    @staticmethod
    def _generate_structured_summary(
        messages: List[Dict[str, Any]],
        previous_summary: Optional[str] = None,
    ) -> str:
        """
        Create a compact structured summary highlighting topics, decisions,
        timeframes, and verified facts.
        """
        topics: List[str] = []
        verified_facts: List[str] = []
        user_queries: List[str] = []

        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "")
            meta = m.get("metadata", {}) or {}

            if role == "user":
                user_queries.append(content[:120].strip())
            elif role == "assistant":
                tools_used = meta.get("tools_used") or []
                for t in tools_used:
                    tool_name = t.get("tool", "")
                    summary_text = t.get("summary", "")
                    if summary_text and summary_text not in verified_facts:
                        verified_facts.append(summary_text[:160])
                    elif tool_name and tool_name not in topics:
                        topics.append(tool_name)

        summary_parts = []
        if previous_summary:
            summary_parts.append(f"Prior Context: {previous_summary.strip()}")

        if user_queries:
            recent_q = user_queries[-3:]
            summary_parts.append(f"Key User Inquiries: {'; '.join(recent_q)}")

        if verified_facts:
            summary_parts.append("Verified Findings from Tools: " + "; ".join(verified_facts[-4:]))
        elif topics:
            summary_parts.append(f"Topics Covered: {', '.join(topics)}")

        return " | ".join(summary_parts)

    # ── 3. Long-Term Cross-Conversation Memory ─────────────────────────

    def extract_and_store_memory(
        self,
        user_message: str,
        session_id: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract durable user preferences or business facts from user message.
        Guarantees that sensitive data (passwords, tokens, etc.) are never saved.
        """
        text = user_message.strip()
        lower_text = text.lower()

        # Security check: never persist credentials
        for pat in SENSITIVE_PATTERNS:
            if re.search(pat, lower_text):
                logger.warning("Message contains sensitive pattern '{}'; skipping memory extraction.", pat)
                return None

        # Check for trigger patterns
        extracted_content = None
        category = "preference"

        for pat in MEMORY_TRIGGER_PATTERNS:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                extracted_content = match.group(1).strip()
                break

        if not extracted_content:
            return None

        # Determine category
        ec_lower = extracted_content.lower()
        if "fiscal" in ec_lower or "report" in ec_lower or "monthly" in ec_lower or "weekly" in ec_lower:
            category = "reporting"
        elif "target" in ec_lower or "goal" in ec_lower or "achieve" in ec_lower:
            category = "goal"
        elif "client" in ec_lower or "vendor" in ec_lower or "product" in ec_lower or "operate" in ec_lower:
            category = "business_fact"
        else:
            category = "preference"

        # Check existing active memories to prevent duplicate clutter
        existing = self.memory_repo.list_memories(
            self.company_id,
            self.user_id,
            active_only=True,
            limit=20,
        )
        for mem in existing:
            if mem.get("content", "").lower() == extracted_content.lower():
                logger.info("Memory already exists; skipping duplicate.")
                return mem

        memory_record = {
            "company_id": str(self.company_id),
            "user_id": str(self.user_id),
            "session_id": str(session_id) if session_id else None,
            "category": category,
            "content": extracted_content,
            "confidence": 1.0,
            "is_active": True,
            "metadata": {"extracted_from": text[:200]},
        }

        try:
            saved = self.memory_repo.create_memory(memory_record)
            logger.info("Stored new durable AI memory [{}]: '{}'", category, extracted_content)
            return saved
        except Exception as e:
            logger.warning("Failed to store AI memory: {}", e)
            return None

    def get_relevant_memories(self, query: Optional[str] = None, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Retrieve active memories for the user and company.
        """
        try:
            return self.memory_repo.list_memories(
                self.company_id,
                self.user_id,
                active_only=True,
                limit=limit,
            )
        except Exception as e:
            logger.warning("Could not fetch relevant memories: {}", e)
            return []

    @staticmethod
    def format_memories_prompt_block(memories: List[Dict[str, Any]]) -> str:
        """
        Format active memories into a clean Markdown block for LLM system prompt.
        """
        if not memories:
            return ""

        lines = [
            "--- USER PREFERENCES & BUSINESS MEMORY (ACROSS CONVERSATIONS) ---",
            "The user has defined the following ongoing business preferences and context for this company:",
        ]
        for m in memories:
            cat = m.get("category", "preference").upper()
            content = m.get("content", "").strip()
            if content:
                lines.append(f"- [{cat}]: {content}")

        lines.append(
            "IMPORTANT: Use these preferences for context, tone, and focus. "
            "NEVER treat remembered figures as a replacement for live ERP tool data. "
            "Always query tools for up-to-date metrics."
        )
        lines.append("--- END OF MEMORIES ---")
        return "\n".join(lines)

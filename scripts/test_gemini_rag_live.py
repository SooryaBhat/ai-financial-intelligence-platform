# -*- coding: utf-8 -*-
"""
test_gemini_rag_live.py
========================
Tests the live end-to-end integration of Google Gemini with ALLADIN's
existing RAG pipeline, deterministic ERP financial tools, and multi-tenant scoping
for the dedicated Indian demo company 'ALLADIN India Demo Retail'.
"""

import os
import sys
from uuid import UUID

# Add backend to path
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.append(BACKEND_DIR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.database.client import get_admin_client
from app.services.ai_assistant import AIAssistantService

import time

DEMO_COMPANY_ID = UUID("11111111-0000-0000-0000-000000000001")

QUESTIONS = [
    "What were our sales this month?",
    "Compare this month with last month.",
    "Which products sold the most this week?",
    "What were our largest expense categories?",
    "What are our current gross profit and net profit?",
    "Which products are running low on stock?",
    "What does our knowledge base say about inventory management?",
    "Why did revenue increase or decrease compared with last month?",
]

def main():
    print("=" * 75)
    print("ALLADIN — LIVE GEMINI RAG & ERP TOOL EXECUTION VERIFICATION")
    print("=" * 75)
    admin = get_admin_client()

    print(f"\nInitializing AIAssistantService with provider='gemini' for company {DEMO_COMPANY_ID}...")
    assistant = AIAssistantService(
        client=admin,
        company_id=DEMO_COMPANY_ID,
        provider="gemini",
    )
    print(f"  -> Configured provider: {assistant.provider}")
    print(f"  -> Gemini API Key present: {bool(assistant.api_key)}")

    all_passed = True
    results = []

    for idx, q in enumerate(QUESTIONS, 1):
        print("\n" + "-" * 75)
        print(f"TEST {idx}/{len(QUESTIONS)}: \"{q}\"")
        print("-" * 75)

        try:
            resp = assistant.answer_question(q)
            provider_used = resp.get("provider", "unknown")
            model_used = resp.get("model", "unknown")
            tools_used = resp.get("tools_used", [])
            message = resp.get("message", "")
            fallback_used = resp.get("fallback_used", False)

            print(f"  Provider Used : {provider_used.upper()} (Model: {model_used})")
            print(f"  Fallback Used : {fallback_used}")
            print(f"  Tools Invoked : {len(tools_used)}")
            for t in tools_used:
                tool_name = t.get("tool")
                tool_args = t.get("args")
                summary = t.get("summary")
                print(f"    • [{tool_name}] args: {tool_args}")
                if summary:
                    print(f"      Summary: {summary[:120]}...")

            print(f"\n  AI Response Output:")
            # Indent response for clean readability
            for line in message.strip().split("\n"):
                print(f"    {line}")

            # Verify no $ symbol appeared
            has_dollar = "$" in message
            has_rupee = "₹" in message or "INR" in message
            print(f"\n  Currency Check:")
            print(f"    Contains INR/₹ : {has_rupee}")
            print(f"    Contains USD/$ : {has_dollar}")

            results.append({
                "question": q,
                "provider": provider_used,
                "model": model_used,
                "tools": [t.get("tool") for t in tools_used],
                "has_dollar": has_dollar,
                "has_rupee": has_rupee,
                "status": "PASS" if not has_dollar else "WARN_DOLLAR",
            })

        except Exception as e:
            print(f"  ERROR executing query: {e}")
            all_passed = False
            results.append({
                "question": q,
                "error": str(e),
                "status": "FAIL",
            })

        if idx < len(QUESTIONS):
            time.sleep(12)

    print("\n" + "=" * 75)
    print("SUMMARY OF ALL 8 GEMINI RAG TEST QUERIES")
    print("=" * 75)
    for idx, r in enumerate(results, 1):
        status = r.get("status")
        tools_str = ", ".join(r.get("tools", [])) or "None"
        prov = r.get("provider", "err")
        print(f"[{status}] Q{idx}: {r['question']}")
        print(f"       Provider: {prov} | Tools: {tools_str}")

    print("\n" + "=" * 75)

if __name__ == "__main__":
    main()

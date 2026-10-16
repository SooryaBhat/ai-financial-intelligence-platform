---
document_id: EV-04
title: "Knowledge Base Quality Checklist"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: evaluation
content_type: AI_assisted_draft
review_status: unreviewed
license_reuse_status: "Internal, project-owned; AI-assisted"
applicable_region: general
---

# Knowledge Base Quality Checklist

Use before indexing a document and at each review. `[ ]` = to verify by a human.

## Metadata and provenance
- [ ] Front matter present and valid against `schemas/document_metadata_schema.json`
- [ ] `content_type` correct (official_source, book, internal_guide, AI_assisted_draft, fictional_case_study)
- [ ] `review_status` honest (AI drafts stay `unreviewed` until a qualified person reviews)
- [ ] No invented author, publisher, year, page, chapter, URL, or quotation
- [ ] `source_url` is real and verified where present; otherwise null
- [ ] License/reuse status recorded; no copyrighted book copied in full
- [ ] `applicable_region` set; region-specific content flagged

## Content accuracy
- [ ] Formulas stated with definitions together and checked
- [ ] Numerical examples recomputed; fictional data labelled
- [ ] Illustrative thresholds labelled; no "universal" thresholds
- [ ] No unsupported legal, tax, accounting, or regulatory claims; `[SOURCE NEEDED]` tags resolved or retained
- [ ] India-specific statements only with reviewed official sources
- [ ] Limitations and assumptions stated; no guaranteed outcomes
- [ ] Outdated content flagged

## Business rules
- [ ] Unique rule ID; entry in `business_rules_catalog.csv`
- [ ] Purpose, preconditions, fields, logic, thresholds, outcome, severity, follow-up, exceptions, DQ checks, explanation, evidence, tests, status all present (directly or via the documented global conventions)
- [ ] Mandatory logic distinguished from configurable thresholds
- [ ] Assumed fields marked and reconciled with the real schema
- [ ] Zero/negative denominators, empty periods, mixed currency, soft deletes handled
- [ ] Anomaly outputs worded as "may deserve investigation"
- [ ] Forecast rules use chronological validation; test set not reused
- [ ] No rule marked `validated` without passing tests and review

## RAG readiness
- [ ] Chunks follow headings; formulas stay with definitions
- [ ] Chunk metadata carries document_id, section, content_type, review_status, region, tenant_scope
- [ ] Retrieval tested on `rag_test_questions.md`; hit rate recorded
- [ ] Retrieval returns a small set of passages, not the whole library
- [ ] Private documents carry `tenant_id` and are filtered at retrieval time
- [ ] Citations resolve to real passages

## Assistant behaviour
- [ ] Cross-tenant tests pass (BT: AST-001, DQ-010)
- [ ] Prompt-injection and secrets tests pass
- [ ] Insufficient-information questions produce "insufficient data", not guesses
- [ ] Named-book questions without a source say "not found in the indexed sources"
- [ ] Forecast answers include period, method, metrics, and estimate notice

## Maintenance
- [ ] Review schedule and owner assigned
- [ ] Changes re-tested; version recorded
- [ ] Feedback on wrong answers logged and fed back into guides/rules

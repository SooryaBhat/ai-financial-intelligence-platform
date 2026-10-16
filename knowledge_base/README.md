# ALLADIN Knowledge & Business Rules Library

**ALLADIN** — *AI-powered Ledger Learning and Analytics for Decision Intelligence Network*
Tagline: *From business data to intelligent decisions.*

ALLADIN is an AI-enabled ERP and financial-intelligence platform for SMEs/MSMEs. This library supplies the **general business knowledge** (guides) and the **explicit decision logic** (business rules) that the ALLADIN assistant and backend use alongside live ERP data.

> **Status of this library:** AI-assisted drafts. Nothing here is legally, tax, or professionally authoritative, and no rule is "validated" until tested against the real ERP schema and real data. All numerical examples are **fictional**. All thresholds are **illustrative defaults requiring configuration** unless stated otherwise.

## The three sources of intelligence (never mix them)

| Source | What it is | Where it lives | Authority |
|---|---|---|---|
| A. General business knowledge | Concepts, formulas, practices | `business_guides/` (indexed in RAG) | Explains *why/how*; never overrides company data |
| B. Company-specific facts | Sales, expenses, stock, etc. of the authenticated company | ERP database via backend tools | The only source for a company's actual figures |
| C. Business rules & decision logic | How metrics are computed, flagged, interpreted | `business_rules/` + `schemas/` | Defines calculations and outcomes; thresholds are configuration |

Example: Guide 03 explains why stockouts hurt (A). The ERP gives current stock, demand history, lead time (B). Rule `INV-006` computes the reorder point and `INV-008` classifies risk (C).

## Directory structure

```
knowledge_base/
  README.md
  business_guides/      01–12  (RAG-indexed explanatory guides)
  business_rules/       01–10  (rule specifications)
  schemas/              business_rule_schema.json, document_metadata_schema.json,
                        kpi_definitions.csv, business_rules_catalog.csv
  evaluation/           rag_test_questions.md, business_rule_test_cases.md,
                        expected_answers_and_evidence.md, knowledge_base_quality_checklist.md
```

## Conventions

- **Metadata:** every guide starts with YAML front matter conforming to `schemas/document_metadata_schema.json`. Guides here are `content_type: AI_assisted_draft` (case-study guide: `fictional_case_study`), `review_status: unreviewed`, `source_url: null` — i.e. **no external source is cited**, and none has been invented. Where a guide mentions a standard or regulator, it is flagged `[SOURCE NEEDED]` for human verification.
- **Rule fields:** every rule carries the 16 fields required by `schemas/business_rule_schema.json`. Rule status is one of `proposed`, `configuration_dependent`, `validated`. Currently **no rule is `validated`**.
- **Mandatory vs configurable:** rule logic marked **MANDATORY** (formulas, tenant isolation, "insufficient data" gates) must not be changed by tenants; values marked **CONFIG** (thresholds, windows, service levels) are tenant/industry configuration.
- **Assumed fields:** ERP field names such as `sales.total_amount` are **ASSUMED** and must be reconciled with the real Supabase schema (see the consolidated assumptions table in `business_rules/10_data_quality_and_exception_rules.md` and the "schema items to reconcile" section at the end of each rule file).
- **Region:** guides are written as general international practice. India-specific legal, GST, MCA, or MSME-scheme statements are deliberately not asserted without sources; they are flagged `[INDIA-SPECIFIC: SOURCE NEEDED]`.

## Build progress (final batch)

All planned files exist: README, 4 schema/catalog files, 12 guides, 10 rule documents, 4 evaluation files.

**Known limitations of this release**
- **Rule format:** `schemas/business_rule_schema.json` is *not* enforced against the Markdown. Rule blocks in several files use compact grouped tables; some per-rule fields (e.g. evidence attribution, data-quality checks) are inherited from each file's global conventions rather than repeated. A machine-readable rule export that validates against the schema is still to be built.
- **No rule is validated;** every threshold is an illustrative default; every ERP field name is assumed.
- **No external sources are cited;** all documents are unreviewed AI-assisted drafts (or fictional case studies).
- **Not yet integrated or tested** against ALLADIN's FastAPI backend, Supabase schema, or a RAG index; evaluation files are written but have not been run.
- `ANO-000` and `SAL-000` are mandatory-definition pseudo-rules (wording / measure declaration) included in the catalog.

---
document_id: BR-10
title: "Data Quality and Exception Rules"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: data_quality
content_type: AI_assisted_draft
review_status: unreviewed
license_reuse_status: "Internal, project-owned; AI-assisted"
applicable_region: general
---

# Business Rules 10: Data Quality and Exception Rules (DQ-001 to DQ-010)

> Status: `proposed`. These rules decide when other rules may produce a figure. Gates are **MANDATORY**; tolerances are **CONFIG** (illustrative defaults shown).

## Outcome vocabulary (MANDATORY)
`OK`, `OK_WITH_WARNINGS`, `INSUFFICIENT_DATA`, `CANNOT_CALCULATE_RELIABLY`, `UNDEFINED`, `NO_RECORDS`, `DATA_ERROR`, `INVALID_INPUT`, `UNAUTHORIZED`. Every rule output carries one of these plus reasons.

## Rules
| ID | Rule | Logic / threshold | Outcome and explanation | Tests |
|---|---|---|---|---|
| DQ-001 | Required-field presence | Every field required by a rule is present for ≥ CONFIG share of records (illustrative 95%) | Below ⇒ INSUFFICIENT_DATA naming fields and coverage % | 80% of sales missing dates ⇒ insufficient |
| DQ-002 | Valid date range | `start < end`; not unreasonably far in the future; period begins on or after the first record or flagged | INVALID_INPUT or "no records before <first date>" | end < start ⇒ INVALID_INPUT |
| DQ-003 | Duplicate-looking records | Same company, vendor/customer, amount, date (±CONFIG days, illustrative 1) or same document number | Flag `POSSIBLE_DUPLICATE` for review; never delete or exclude silently | two identical invoices ⇒ flag |
| DQ-004 | Negative or zero values | Negative amounts allowed only for credit notes/refunds/reversals with proper type; zero-amount sales flagged | Otherwise DATA_ERROR for that record, counted in warnings | sale −100 type "sale" ⇒ DATA_ERROR |
| DQ-005 | Unit consistency | Quantities carry a unit; conversion defined between stock, sales, purchase units | Mismatch ⇒ block inventory rules (INV-012) | sales in pcs, stock in cartons ⇒ blocked |
| DQ-006 | Currency consistency | One currency per aggregation, or conversion rates with date | Mixed ⇒ CANNOT_CALCULATE_MIXED_CURRENCY | INR + USD no rate ⇒ cannot calculate |
| DQ-007 | Status validity | Status values belong to known vocabulary; unknown ⇒ excluded and counted | OK_WITH_WARNINGS listing excluded counts | status "xyz" ⇒ warning |
| DQ-008 | Timeliness | Latest record date within CONFIG window of today (illustrative 7 days) for "current" questions | Stale ⇒ warning "latest data is from <date>" | last record 20 days old ⇒ warning |
| DQ-009 | Referential integrity | Sale items have products; refunds have sales; payments have invoices | Orphans counted; reliability reduced | refund with no sale ⇒ flag |
| DQ-010 | Tenant integrity | All records returned belong to the session `company_id`; mismatch is a critical error | UNAUTHORIZED + alert/log; no data shown | query returns foreign company row ⇒ block |

## Handling exceptions
- **Missing data:** state what is missing and what would be needed; do not impute silently. Imputation (if ever used) must be labelled and configurable.
- **Contradictory records:** e.g., invoice paid but status unpaid; report the contradiction, show both, do not choose silently.
- **Incomplete financial statements:** ratios requiring absent statements return CANNOT_CALCULATE with the missing statement named (see Guide 1 §11).
- **Late-arriving data:** results are as-of a timestamp; note that recent periods may change.

## Assumptions needing reconciliation with the real ERP schema (consolidated)
| Area | Assumed | Must verify |
|---|---|---|
| Identity | `company_id` on every table; session-derived | Column names, RLS policies |
| Soft delete | `deleted_at` or `is_deleted` | Which, per table |
| Sales | `sales`, `sale_items`, statuses | Table names, status vocabulary, date semantics (order/invoice/delivery), tax and discount columns |
| Refunds | `refunds` table | Existence, link to sales |
| Expenses | `expenses` with category, status | Taxonomy, class mapping, capex flag |
| Payments/AR/AP | `payments`, `invoices`, `bills` | Existence and linkage |
| Budgets | `budgets` | Existence |
| Inventory | on-hand, reserved, damaged, on-order | Which are tracked; units of measure |
| Purchasing | purchase orders with expected/received dates | Lead-time derivation |
| Costs | unit cost snapshot per sale item | Whether historical cost is stored |
| Settings | timezone, currency, thresholds per company | Where stored |
| Balance sheet | not assumed present | Whether any equivalent exists |

### Reconciled Schema Findings (Database Reconciliation Audit)
- **Expenses (`expenses`):** Expenses store `category_id` (foreign key referencing `categories.id`). Category names must be resolved by `JOIN categories ON expenses.category_id = categories.id`.
- **Inventory (`inventory`):** Stock quantity is tracked in the `inventory` table (`inventory.quantity`, `inventory.reorder_level`) partitioned by `product_id` and `warehouse_id`, not in `products.stock_quantity`.
- **Budgets (`budgets`):** No `budgets` table currently exists in the Supabase schema migrations. Budget comparison rules (`FIN-015`, `EXP-003`, `KPI-012`) must not claim live ERP budget support; the assistant must return `CANNOT_CALCULATE: no budget configured in ERP`.
- **Identity & Tenancy:** Verified `company_id NOT NULL` present on all core tables (`sales`, `sale_items`, `expenses`, `inventory`, `products`, `invoices`, `chat_sessions`).
- **Preserved Core Rules:** Revenue calculation (`SAL-000` to `SAL-009`, `FIN-001`, `FIN-002`), inventory policies (`INV-001` to `INV-013`), cash-flow rules (`FIN-003` to `FIN-015`), and anomaly detection (`ANO-000` to `ANO-008`) remain fully preserved.


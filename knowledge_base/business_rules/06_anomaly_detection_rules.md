---
document_id: BR-06
title: "Anomaly Detection Rules"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: anomaly_rules
content_type: AI_assisted_draft
review_status: unreviewed
license_reuse_status: "Internal, project-owned; AI-assisted"
applicable_region: general
---

# Business Rules 06: Transaction Anomaly Detection (ANO-001 to ANO-008)

> Status: `proposed` / `configuration_dependent`; none validated. Conventions G-1…G-10 and DQ rules apply.

## Mandatory wording (ANO-000)
An output is called **"an anomaly"** or **"a transaction that may deserve investigation"**. It is never described as fraud, theft, wrongdoing, or error without confirmed evidence. Each output lists the reason it was flagged **and plausible legitimate explanations**. Anomaly detection is a screening aid with false positives and false negatives; humans decide.

## Method and threshold selection
- Statistical rules per segment (category, vendor, product) with robust statistics (median/MAD or IQR) rather than mean/SD where distributions are skewed.
- ML anomaly scores (e.g., Isolation Forest in the existing prototype, **unverified**) may supplement rules but must convert to an explainable reason ("amount is X times the category median").
- Thresholds are CONFIG with illustrative defaults; selected by the company or reviewed against flagged-record feedback. Target an alert volume the owner can review (CONFIG, illustrative ≤ 10 flags per period); rank by score and amount.
- Minimum history per segment (illustrative 12 observations); otherwise no statistical flag (limited-history note).
- Owner feedback ("reviewed: legitimate") may be stored as review context and used to improve ranking or annotate similar future alerts. Do not permanently suppress similar alerts automatically: a repeated pattern can become meaningful when amounts, context, frequency, or business conditions change. Any configurable suppression/deduplication must be time-limited, explainable, reversible, and must not hide critical or materially changed alerts.

## Rules
| ID | Rule | Logic / threshold | Legitimate explanations to show | Tests |
|---|---|---|---|---|
| ANO-001 | Unusual amount | Within segment: `amount > Q3 + k×IQR` or modified z > CONFIG (3.5); also unusually small/zero if relevant | Bulk order, annual payment, price change, capex, correction | normal 100±10, record 900 ⇒ flag; segment with 5 records ⇒ no flag |
| ANO-002 | Unusual expense category | Category with no prior records in `lookback` (CONFIG 12 months), or share of expenses jumps by > CONFIG (illustrative +15 pts) | New supplier/line of business, reclassification, one-off | new "legal fees" category ⇒ flag low |
| ANO-003 | Duplicate-looking records | Same company + counterparty + amount (± CONFIG tolerance 0) + date within CONFIG days (1), or identical document number | Genuine repeat purchase, split delivery, retry after failed entry | two 5,000 invoices same day same vendor ⇒ flag; different document numbers and items ⇒ lower confidence |
| ANO-004 | Unexpected timing or frequency | Transaction on day/time outside the company's usual pattern (e.g., nonbusiness hours, weekend) or frequency spike (count in window > Q3 + k×IQR of historical counts) | Online orders, festival rush, month-end processing, timezone mistakes | weekday-only business with 20 weekend sales ⇒ flag; timezone mismatch noted |
| ANO-005 | Departure from historical pattern | Compare period aggregates (by vendor, product, category) to the trailing baseline (SAL-005 / EXP-004 method) | Seasonality, expansion, promotions | |
| ANO-006 | Missing or inconsistent attributes | Missing category/vendor/customer, date in the future, line total ≠ qty×price, payment before invoice date, quantity not an expected unit | Data entry shortcuts, migration artifacts | line total mismatch ⇒ data-quality flag (not fraud) |
| ANO-007 | Round-number and threshold clustering (optional, CONFIG off by default) | Many amounts just below an approval limit | Standard pricing, fixed fees | only active if the company defines an approval limit |
| ANO-008 | Alert prioritisation and explanation | Severity = f(score, amount share of period total, repeat count); output includes: record IDs, what was compared, the reason, plausible legitimate causes, suggested checks (supporting document, approval, supplier confirmation) | n/a | output lacking explanation fails |

## Standard user explanation
"This <expense/sale> of <amount> on <date> is about <k>× the usual <category> amount (median <m>). That can have normal causes, for example <explanations>. You may want to check the supporting document and whether it was recorded correctly. This does not mean anything improper happened."

## Edge cases (MANDATORY handling)
Refunds and reversals (negative amounts) evaluated separately; one-time capital expenses and annual fees; expansion periods (baseline shift); first-year companies (limited history); backdated imports (timing flags suppressed for import batches); soft-deleted records excluded.

## Evidence and attribution
Each flag stores: rule ID, parameters, baseline statistics, record IDs, model version (if ML), timestamp. No other tenant's data is used for baselines unless explicitly pooled and anonymised under a documented policy.

---
document_id: BR-07
title: "Business Health Scorecard"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: scorecard_rules
content_type: AI_assisted_draft
review_status: unreviewed
license_reuse_status: "Internal, project-owned; AI-assisted"
applicable_region: general
---

# Business Rules 07: Business-Health Scorecard (HLT-001 to HLT-009)

> Status: `configuration_dependent`; none validated. **All thresholds and weights below are illustrative defaults requiring configuration. There are no universal thresholds valid for all industries and companies.** The scorecard is an interpretable summary, not a credit rating or professional assessment.

## Design principles (MANDATORY)
1. Report **dimension-level** results first; an overall score is secondary and optional.
2. Each dimension reports `score` (0–100 or categorical), `coverage` (share of required inputs available), `confidence` (high/medium/low from coverage and data-quality flags), `evidence`, `explanation`, `next_action`.
3. Missing data ⇒ dimension status `INSUFFICIENT_DATA`; it is **never scored as zero or neutral**.
4. Overall score is produced only if (CONFIG illustrative): ≥ 4 of the 6 core dimensions scored, sum of weights of scored dimensions ≥ 0.7, and data completeness dimension ≥ CONFIG minimum (60). Otherwise the overall result is **"insufficient data"** with the list of missing dimensions.
5. Weights are CONFIG, must sum to 1 over scored dimensions after renormalisation, and are displayed with the score.
6. Direction (higher/lower is better) is defined per metric.
7. Scores come from piecewise-linear mapping of a metric between a "poor" threshold (score 0) and a "good" threshold (score 100), both configured per company/industry. Illustrative defaults are marked as such in the UI.

## Dimension definitions
| ID | Dimension | Required fields / rules | Calculation (illustrative) | Direction | Illustrative thresholds (poor → good), CONFIG | Illustrative weight | Missing-data behaviour | Next action |
|---|---|---|---|---|---|---|---|---|
| HLT-001 | Revenue performance | Revenue by period (FIN-001), ≥ 6 periods | Trend growth (FIN-011) and latest period-over-period (FIN-010), seasonality-adjusted if ≥ 24 months | Higher better | −10% → +10% growth | 0.20 | < 6 periods ⇒ INSUFFICIENT | Review products/customers (SAL) |
| HLT-002 | Profitability | FIN-007/009 (needs COGS/expenses coverage ≥ CONFIG 80%) | Net margin (or operating margin) vs own history and configured target | Higher better | 0% → 10% net margin (industry-specific!) | 0.25 | No COGS/expenses coverage ⇒ INSUFFICIENT | Review pricing, cost drivers |
| HLT-003 | Liquidity | FIN-012 (cash records), FIN-013 (AR/AP), balance-sheet for ratios | Cash runway or current ratio, whichever data exists (state which) | Higher better | runway 1 → 6 months; current ratio 1.0 → 2.0 | 0.20 | No cash/balance-sheet data ⇒ INSUFFICIENT | Cash forecast, collections |
| HLT-004 | Expense control | EXP-002, EXP-003, EXP-006 | Expense growth relative to revenue growth; budget variance if budget exists | Lower relative growth better | expense growth − revenue growth: +15 pts → ≤ 0 pts | 0.15 | Needs ≥ 6 periods | Review largest growing categories |
| HLT-005 | Inventory health | INV-008, INV-009, INV-010, INV-012 (only items passing the gate) | Weighted share of stock value in healthy cover range; share of items at high stockout risk; share slow/dead | Higher healthy share better | healthy share 40% → 80% | 0.15 | Items failing INV-012 excluded and counted; < CONFIG 50% items covered ⇒ INSUFFICIENT | Reorder, clear slow stock |
| HLT-006 | Data completeness | DQ-001…DQ-009 results | Weighted share of required fields present and valid, records in valid status, timely | Higher better | 60% → 95% | (gate, not weighted by default) | n/a | Fix recording gaps |
| HLT-007 | Forecast reliability (where relevant) | FCT-001…012 | Holdout WAPE and monitoring status | Lower WAPE better | WAPE 40% → 10% | 0.05 | No forecast ⇒ not applicable (excluded, not penalised) | Improve data history |

## Aggregation (HLT-008)
```
scored = [d for d in core_dimensions if d.status == SCORED]
if len(scored) < MIN_DIMS or sum(w[d] for d in scored) < MIN_WEIGHT or data_completeness < MIN_COMPLETENESS:
    return "insufficient data", missing_dimensions
overall = Σ w[d]·score[d] / Σ w[d]          # weights renormalised over scored dimensions
overall_confidence = min(confidence[d] for d in scored)   # conservative
return overall, per-dimension table, confidence, "illustrative thresholds" notice if unconfigured
```
**Overall labels** (CONFIG): e.g., ≥ 75 "Strong", 50–74 "Moderate", < 50 "Needs attention", always accompanied by confidence and dimension breakdown. A dimension in "needs attention" is shown even if the overall is strong (no averaging away of serious problems; CONFIG: any dimension < 30 caps the overall label at "Moderate").

## Explanation template (HLT-009)
"Your <dimension> score is <s>/100 (confidence <c>, based on <coverage>% of the data needed). It reflects <metric> of <value>, compared with your configured range <poor>–<good>. Thresholds are <illustrative/company-configured>. Suggested next step: <action>."

## Tests
| Case | Expected |
|---|---|
| Only sales data (no expenses, no cash, no inventory) | Revenue scored; others INSUFFICIENT; overall "insufficient data" |
| All dimensions with full data, net margin 5% in a 0%→10% range | Profitability 50 |
| Net margin negative below poor threshold | Score 0 (clamped), explanation says below configured poor level |
| 30% of inventory items fail INV-012 | Excluded and counted; confidence reduced |
| Liquidity dimension has only an AR ageing, no cash | INSUFFICIENT or partial with low confidence per CONFIG; must name the metric used |
| Unconfigured thresholds | Output carries "illustrative defaults" notice; no overall label shown unless the owner confirms |
| Data completeness 40% | Overall insufficient even if other dimensions scored |

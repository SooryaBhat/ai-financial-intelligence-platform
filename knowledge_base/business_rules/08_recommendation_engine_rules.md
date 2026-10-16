---
document_id: BR-08
title: "Recommendation Engine Rules"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: recommendation_rules
content_type: AI_assisted_draft
review_status: unreviewed
license_reuse_status: "Internal, project-owned; AI-assisted"
applicable_region: general
---

# Business Rules 08: Recommendation Engine (REC-001 to REC-006)

> Status: `proposed`. A recommendation is a **suggestion for the owner to evaluate**, not an instruction and not a prediction of results.

## REC-001 Structure (MANDATORY fields)
Each recommendation includes:
1. **Observed fact** (from ERP data or a model) with period and measure
2. **Calculation / rule / source** (rule ID, tool, document)
3. **Possible interpretation** (labelled as possible)
4. **Suggested next step**
5. **Expected benefit** — only if reasonably estimable from the company's own data; otherwise "not estimated"
6. **Cost, risk, or trade-off**
7. **Confidence / uncertainty**
8. **Missing information that could change the recommendation**
9. **How to measure whether it worked** (metric, baseline, review date)

## REC-002 Statement types (MANDATORY labels)
| Type | Meaning | Example |
|---|---|---|
| Verified fact | Retrieved from ERP records | "12 sales of Product A in March" |
| Calculated metric | Deterministic rule output | "Gross margin 38.5% (FIN-007)" |
| Model prediction | Output of a forecasting/ML model | "Estimated April revenue 210,000 ± range" |
| Possible explanation | Hypothesis, not established | "Margin may have fallen due to discounts" |
| Suggested action | Proposal | "Review supplier prices for the top 3 cost items" |

## REC-003 Prohibitions (MANDATORY)
- No fabricated financial impact; benefits only from computed company data with stated assumptions and ranges.
- No guaranteed profit, savings, or sales increases.
- No causal claim from correlation; use "may be related", and name the check that would test causation (Guide 4 §11).
- No recommendation that rests on a rule that returned `INSUFFICIENT_DATA` / `CANNOT_CALCULATE`; instead recommend collecting the missing data.
- No recommendation that cuts costs affecting safety, quality, employees, or compliance without an explicit caution.
- No accusation language (see ANO-000, EXP-007).
- No silent actions: recommendations never change data (AST-004).

## REC-004 Generation logic
```
for each triggered finding F (from FIN/SAL/EXP/INV/FCT/ANO/HLT):
    if F.status in (INSUFFICIENT_DATA, CANNOT_CALCULATE): create data-collection recommendation only
    template = lookup(F.rule_id, F.outcome)        # reviewed templates, not free-form invention
    fill with facts, rule IDs, periods
    estimate_benefit() only if inputs exist (e.g., excess stock value × configured carrying-cost rate); else "not estimated"
    attach confidence = min(confidence of inputs)
    attach missing_information from template + data-quality flags
rank by severity, amount at stake, confidence; cap at CONFIG N (illustrative 5)
```
The language model may rephrase the filled template but must not add figures, citations, or claims absent from the evidence bundle.

## REC-005 Prioritisation
Order by (severity, estimated amount at stake, confidence, ease). Present at most CONFIG N items, with "why this is first".

## REC-006 Professional-advice triggers
Suggest consulting an accountant/tax/legal professional for: tax treatment, statutory filings, write-offs, depreciation, loan covenants, employment actions, contract disputes, suspected fraud (refer to professionals, not accuse).

## Worked example (fictional)
| Element | Content |
|---|---|
| Observed fact | Product A stock cover is 6.5 days; supplier lead time averaged 9 days (n=3 orders). (Verified fact + calculated metric, INV-008) |
| Source | INV-003, INV-004, INV-006, INV-008; data period last 90 days |
| Interpretation | Stock may run out before a new order arrives (possible explanation) |
| Suggested step | Review placing an order now; ask the supplier about expediting |
| Expected benefit | Avoided lost sales: not estimated (no margin or demand-lost data); upper bound from average daily sales × gross margin × days at risk could be shown if margin data exists |
| Trade-off | Order cost/cash use; expedite fees; risk of overstock if demand falls |
| Confidence | Medium: lead time from 3 orders only |
| Missing information | Open purchase orders, confirmed customer orders, supplier stock availability |
| Measure | Stockout days for Product A over next 60 days vs previous 60 |

## Tests
| Case | Expected |
|---|---|
| Rule returned INSUFFICIENT_DATA | Only a data-collection recommendation |
| Request: "Guarantee 20% profit" | Declined; explains it can't guarantee; offers analysis |
| Correlation between ad spend and sales | Phrased as "may be related"; test suggested |
| No margin data | Benefit "not estimated" |
| Recommendation to cut staff to save cost | Includes caution about service, legal obligations; suggests professional advice |

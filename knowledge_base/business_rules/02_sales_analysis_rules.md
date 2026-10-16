---
document_id: BR-02
title: "Sales Analysis Rules"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: sales_rules
content_type: AI_assisted_draft
review_status: unreviewed
license_reuse_status: "Internal, project-owned; AI-assisted"
applicable_region: general
---

# Business Rules 02: Sales Analysis (SAL-001 to SAL-009)

> Status: `proposed` / `configuration_dependent`; none validated. Fields **ASSUMED**. Global conventions G-1…G-10 from `01_financial_calculation_rules.md` apply (tenant scope, soft deletes, status filters, `[start,end)` periods, empty-period handling, evidence). Explanations: Guide 4.

## Mandatory definition (SAL-000)
Every sales figure must declare its **measure**: `order_value` (all non-cancelled orders), `invoiced_revenue` (invoice date), `completed_sales` (final successful status), or `cash_collected` (payments). These are never interchangeable. If the schema supports only one, the answer says which and notes the others are unavailable.

## SAL-001 Sales by Date Range
| Field | Specification |
|---|---|
| Logic | `Σ amount` per declared measure, filtered per G-1…G-4; optional grouping by day/week/month in company timezone |
| Required fields | `sales.sale_date`, `total_amount`, `status`, `deleted_at`, `company_id` (ASSUMED) |
| Outcome | Total, count, AOV (= total ÷ count if count > 0), daily series |
| Severity | info |
| Edge | Partial periods labelled; future dates excluded or flagged |
| DQ | Duplicate invoice numbers; null dates |
| Explanation | "Between <start> and <end> there were <n> <measure> totalling <X>." |
| Tests | Range with no sales ⇒ NO_RECORDS; end < start ⇒ INVALID_DATE_RANGE; one sale on boundary end date excluded (half-open). |
| Status | proposed |

## SAL-002 Sales by Product / Category
| Logic | Σ line amount (`sale_items.quantity × unit_price − line_discount`) grouped by product or category; shares of total. Sum of lines must reconcile with header totals within CONFIG tolerance (illustrative 0.5%); otherwise flag `LINE_HEADER_MISMATCH`. |
|---|---|
| Required | `sale_items.product_id`, `quantity`, `unit_price`, `products.category` (ASSUMED) |
| Outcome | Ranked table with share and cumulative share |
| Edge | Uncategorised products shown as "Uncategorised"; returned items netted only if returns are linked; deleted products still appear with their historical name |
| Tests | Lines 600+400 with header 1000 ⇒ shares 60/40; header 900 ⇒ mismatch flag. |
| Status | configuration_dependent |

## SAL-003 Sales Growth and Decline
| Logic | FIN-010 on equal-length, comparable periods; per-day normalisation when lengths differ. Classification (CONFIG, illustrative): growth > +10%, stable within ±10%, decline < −10%, **only if** prior-period base ≥ CONFIG minimum (illustrative 20 sales). |
|---|---|
| Outcome | Direction label + magnitude + decomposition (orders vs AOV) |
| Severity | medium for decline beyond threshold |
| Follow-up | Offer breakdown by product/category (SAL-002) and checks in Guide 4 §10 |
| Edge | Partial current month; stockouts (INV-008) may explain declines; one-off bulk order |
| Explanation | "Sales were <C> versus <P> (<±x>%). Orders went from <o1> to <o2>; average order value from <a1> to <a2>." |
| Tests | 200,000/400 vs 180,000/360 ⇒ +11.1%, AOV 500 vs 500. Prior base 5 sales ⇒ "base too small". |
| Status | configuration_dependent |

## SAL-004 Top and Low Performing Products
| Logic | Rank by selected metric (revenue, units, gross profit if cost available). Top N / bottom N (CONFIG N=5). "Low performer" requires: product age ≥ CONFIG (illustrative 90 days) and available stock throughout (not stocked out). |
|---|---|
| Outcome | Ranked list + caveats |
| Edge | New products excluded; seasonal items judged in season; items with zero sales listed separately; **never recommend discontinuation from this rule alone** |
| Explanation | "These products had the lowest revenue. Check stock availability, margin, and whether they support sales of other items before deciding." |
| Tests | Item created 10 days ago excluded; item stocked out 60% of period flagged. |
| Status | configuration_dependent |

## SAL-005 Unusual Changes in Sales
| Logic | Compare the current day/week against history using a robust method: `modified z = 0.6745 × (x − median) ÷ MAD` over a trailing window (CONFIG, illustrative 8 same-weekday observations); flag if |z| > CONFIG (illustrative 3.5). Requires ≥ CONFIG minimum observations (illustrative 8). |
|---|---|
| Outcome | "Unusual change worth reviewing" (never "problem") |
| Severity | low/medium |
| Edge | Holidays, promotions, price changes, data entry gaps, stockouts; MAD = 0 ⇒ use percentage threshold fallback or skip |
| Tests | Stable 100 ± 5 with one day at 300 ⇒ flag; 5 observations ⇒ INSUFFICIENT_DATA. |
| Status | configuration_dependent |

## SAL-006 Sales Concentration
| Logic | Share of revenue from top 1 / top 5 customers and top products. Flags (CONFIG illustrative): top customer > 30%, top 5 > 70%. Requires customer IDs on ≥ CONFIG % of sales (illustrative 80%). |
|---|---|
| Outcome | Shares + flag; else `INSUFFICIENT_DATA: customer IDs missing` |
| Edge | "Walk-in" aggregate customer excluded from concentration |
| Explanation | "One customer accounts for <p>% of revenue. High dependence can increase risk if that customer reduces orders or pays late." |
| Tests | Customer A 400 of 1000 ⇒ 40% flag; 30% of sales without customer ID ⇒ insufficient. |
| Status | configuration_dependent |

## SAL-007 Period Comparisons
| Logic | Standard comparisons: month vs prior month; month vs same month prior year; rolling 30 vs previous 30; custom. Show both periods' dates; normalise per day when different lengths. |
|---|---|
| Edge | Same-month-last-year requires data that long; else say unavailable |
| Tests | Feb vs Jan ⇒ per-day view offered; no prior-year data ⇒ unavailable message. |
| Status | proposed |

## SAL-008 Seasonality Check
| Logic | With ≥ 24 months of history: seasonal index = mean(month value) ÷ mean(all months). With 12–23 months: "possible seasonality, cannot confirm". < 12 months ⇒ `INSUFFICIENT_DATA`. Do not describe seasonality from < 2 cycles as established. |
|---|---|
| Outcome | Indices or limitation message |
| Edge | Growth trend contaminates indices (detrend first); one-off events |
| Tests | 10 months ⇒ insufficient; 24 months with Dec index 1.4 ⇒ "December has been ~40% above average". |
| Status | configuration_dependent |

## SAL-009 Revenue, Orders, and Cash Distinction
| Logic | When a user says "sales", resolve to the configured default measure and state it. If the answer would differ materially between measures and more than one exists, show the key alternatives or offer to. Never convert order value into cash or revenue by assumption. |
|---|---|
| Tests | "How much did we earn in May?" ⇒ clarify: revenue vs profit vs cash; answer with stated measure. |
| Status | proposed |

## Schema items to reconcile
Order vs invoice vs payment tables; status vocabulary; line-item structure; customer IDs; returns/refund links; product categories; timezone.

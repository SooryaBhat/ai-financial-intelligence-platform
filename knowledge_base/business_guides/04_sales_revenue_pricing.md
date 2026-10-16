---
document_id: BG-04
title: "Sales, Revenue, Pricing, and Customer Analysis"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: sales
chapter: null
section: null
page_number: null
source_url: null
license_reuse_status: "Internal, project-owned; AI-assisted; no third-party text reproduced"
content_type: AI_assisted_draft
review_status: unreviewed
applicable_region: general
---

# Guide 4: Sales, Revenue, Pricing, and Customer Analysis

> All figures are **fictional**. Thresholds are illustrative. Not professional advice.

## 1. Sales, revenue, and cash collection are different things

| Term | Meaning | Example |
|---|---|---|
| Order value | Value of orders placed (may be cancelled, not yet delivered) | Customer orders 10,000 on 28 Jan |
| Invoiced / recognised revenue | Value of goods/services delivered and billed | Delivered 30 Jan, invoiced 31 Jan |
| Completed sale | Order that reached a final successful status | Delivered and not returned |
| Cash collected | Money actually received | Paid 25 Feb |

Every sales statement must say which of these it describes. "Sales rose 12%" based on order value can coexist with flat cash collected.

## 2. Revenue trends and seasonality

- **Trend:** the underlying direction after removing noise.
- **Seasonality:** repeating pattern tied to the calendar (festivals, weather, school terms, month-end salary cycles).
- Compare same period year-over-year when two years of data exist; otherwise compare to the prior period with caution.
- Normalise for days: a 28-day month vs a 31-day month differs by ~10.7% in days alone; compare **revenue per day** or per trading day.
- A decline is not a "decline in demand" until seasonality, stockouts, price changes, and calendar effects are checked.

## 3. Analysis dimensions

Product, category, customer, channel, location, salesperson, period. Start broad (total), then split by the dimension that explains most of the change.

**Sales growth** = (Current − Prior) ÷ Prior. **Fictional:** 200,000 vs 180,000 ⇒ +11.1%.

**Average order value (AOV)** = revenue ÷ number of orders (needs order counts). 200,000 ÷ 400 = 500. Prior: 180,000 ÷ 360 = 500. Here growth came from **more orders**, not larger orders.

**Decomposing a revenue change:** Δrevenue ≈ effect of volume (orders) + effect of AOV (price/mix). Check which moved.

## 4. Sales mix

Share of revenue by product/category. **Fictional:**

| Category | Revenue | Share | Gross margin |
|---|---|---|---|
| Notebooks | 90,000 | 45% | 30% |
| Pens | 60,000 | 30% | 50% |
| Art supplies | 50,000 | 25% | 40% |
| Total | 200,000 | 100% | 38.5% weighted (27,000 + 30,000 + 20,000 = 77,000 ÷ 200,000) |

Mix shift toward low-margin items lowers overall margin even when revenue rises.

## 5. Gross margin and contribution margin

- **Gross margin** = (revenue − COGS) ÷ revenue.
- **Contribution margin per unit** = price − variable cost per unit (includes variable selling costs, commissions, packaging, delivery if they vary with volume). Used for pricing and break-even (Guide 5).

## 6. Discounting and pricing

**Fictional example:** price 100, unit cost 60 ⇒ unit profit 40 (40% margin). A 10% discount ⇒ price 90, unit profit 30. To earn the same total profit, volume must rise from Q to 40Q ÷ 30 = **1.33Q, i.e. +33%**. Discounts need a volume rise larger than the margin loss.

Pricing approaches: cost-plus, competitor-based, value-based. Check the effect on volume with real data; do not assume elasticity. Price changes may be limited by regulation or contracts `[SOURCE NEEDED]`.

## 7. Customer concentration and retention

- **Concentration:** top-customer share of revenue. Illustrative flag (CONFIG): one customer > 30% of revenue, top 5 > 70%.
- **Retention rate** = customers at period end who were also customers at start ÷ customers at start. Needs customer IDs on sales (not all SMEs record them).
- **Repeat rate**, **customer lifetime value** need history and margin data; avoid if data is thin.

## 8. Returns, cancellations, refunds

Track by product, supplier, and reason. High returns may signal quality, description, delivery, or sizing problems. Net revenue = revenue − refunds/returns − discounts (rule FIN-002). A rising return rate can hide behind rising gross sales.

## 9. Identifying underperforming products

Candidates: low revenue, low margin, falling trend, high returns, high stock cover. Before deciding to drop one: is it a **traffic driver** or complement (people buy other things with it)? Was it out of stock? Is it new? Is the data complete?

## 10. Understanding a decline in sales

Checklist: (1) data completeness for the period; (2) days/seasonality; (3) price/discount changes; (4) stockouts; (5) product/category/customer split; (6) lost customers; (7) channel or location changes; (8) competitor or external events (only if evidenced); (9) returns/cancellations; (10) delayed invoicing.

## 11. Correlation versus causation

Two metrics moving together (advertising spend and sales) does not show one caused the other. Both might follow the season. To support a causal claim use a controlled comparison (A/B or before/after with a control group), or at minimum rule out obvious third factors, and state remaining uncertainty.

## 12. Ethical sales-growth strategies

Honest descriptions and pricing; no misleading urgency; respect consent for marketing communications `[SOURCE NEEDED: local marketing and data-protection rules]`; fair credit terms; handle complaints; do not push customers into products that do not suit them.

## 13. Decisions that require more information

| Tempting conclusion | Missing information |
|---|---|
| "Drop product X (low sales)" | Margin, complements, stockouts, trend |
| "Raise prices" | Competitor prices, volume response, contracts |
| "Customer Y is unprofitable" | Cost to serve, returns, discounts, payment delay |
| "Advertising works" | Control group, other changes, margin after ad cost |
| "Sales fell because of the weather" | Evidence beyond coincidence |

## 14. Related
Guides 5, 6, 9, 12; rules `SAL-001`–`SAL-009`, `FIN-001`, `FIN-002`, `FIN-010`.

---
document_id: BG-03
title: "Inventory Management and Optimization"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: inventory
chapter: null
section: null
page_number: null
source_url: null
license_reuse_status: "Internal, project-owned; AI-assisted; no third-party text reproduced"
content_type: AI_assisted_draft
review_status: unreviewed
applicable_region: general
---

# Guide 3: Inventory Management and Optimization

> All figures are **fictional**. Service levels, thresholds, and cost percentages are illustrative and must be configured per business. Formulas rest on stated assumptions; read the limitations.

## 1. Stock terms

| Term | Definition |
|---|---|
| On-hand stock | Physical units in the business's possession (per the system) |
| Reserved / allocated stock | On-hand units promised to confirmed orders |
| Damaged / quarantined stock | On-hand but not sellable |
| Available stock | On-hand − reserved − damaged/quarantined |
| On-order (incoming) stock | Ordered from suppliers, not yet received |
| **Inventory position** | Sellable on-hand + on-order − reserved − backorders, where sellable on-hand = on-hand − damaged/quarantined stock |

**Why it matters:** reordering decisions use *inventory position*, selling decisions use *available stock*. Using on-hand alone causes double ordering (ignores on-order) or overselling (ignores reservations). If a business does not track reserved, on-order, backorder, or damaged/quarantined quantities, say so; do not assume zero silently. If damaged stock is already excluded from the recorded on-hand quantity, do not subtract it a second time.

## 2. Inventory accuracy and reconciliation

- System stock can differ from physical stock (theft, damage, miscounts, unrecorded returns, wrong units).
- **Cycle counting:** count a subset regularly (e.g., fast movers more often) and correct the system with a documented adjustment.
- **Reconciliation:** `System quantity − counted quantity = variance`. Investigate recurring variances by item, location, or person-independent process step.
- **Inventory record accuracy** = items with correct count ÷ items counted.
- Do not compute reorder recommendations from items with unresolved large variances or negative stock (rules `INV-012`).

## 3. Demand forecasting (as an input, not the answer)

Demand is what customers want; **sales** are what you could fulfil. If you were out of stock, sales understate demand (censored demand). Methods: moving averages, exponential smoothing, seasonality adjustments (Guide 9). A forecast alone does **not** tell you how much to order; you also need current inventory position, lead time, supplier constraints, service-level objective, shelf life, storage and cash limits.

**Forecast demand ≠ confirmed customer orders.** Confirmed orders are commitments (reserved stock). Forecast is an estimate.

## 4. Supplier lead time

Lead time = time from placing an order to having sellable stock. Measure from actual order and receipt dates, per supplier (and ideally per item). Track average and variability; use **units consistent with demand** (days with daily demand, weeks with weekly demand). Missing lead time ⇒ no reliable reorder point.

## 5. Safety stock

Buffer against demand and lead-time variability.

**Common formulas (assume demand is roughly independent across days and approximately normal; assumptions often fail for lumpy or seasonal demand):**

- Variable demand, fixed lead time: `SS = z × σ_d × √L`
- Variable demand and lead time: `SS = z × √( L × σ_d² + d² × σ_L² )`

where d = average demand per period, σ_d = standard deviation of demand per period, L = average lead time (same period units), σ_L = standard deviation of lead time, z = service-level factor (e.g., 1.28 ≈ 90%, 1.65 ≈ 95%, 2.33 ≈ 99% cycle service level).

**Example:** d = 20 units/day, σ_d = 6, L = 9 days, 95% service level (z = 1.65): SS = 1.65 × 6 × √9 = 1.65 × 6 × 3 = 29.7 ≈ **30 units**.

**Limitations:** less than ~4–8 weeks of history gives an unstable σ_d; intermittent demand (many zero days) breaks the normal assumption; expensive or perishable items may need different methods; a higher z raises carrying cost nonlinearly.

## 6. Reorder point (ROP)

`ROP = expected demand during lead time + safety stock = d × L + SS`

Using the example: ROP = 20 × 9 + 30 = **210 units**. Reorder when **inventory position ≤ ROP**.

**Example decision:** on-hand 150, reserved 20, on-order 0 → inventory position 130 ≤ 210 ⇒ reorder is due. Stock cover = available (130) ÷ 20 per day = 6.5 days, shorter than the 9-day lead time ⇒ a stockout is likely before a new order arrives unless demand falls or an expedited order is possible.

## 7. Economic order quantity (EOQ)

`EOQ = √( 2 × D × S ÷ H )`

D = annual demand (units), S = fixed cost per order (currency), H = holding cost per unit per year (currency).

**Example:** D = 7,300; S = 500; unit cost 80; H = 25% × 80 = 20 → EOQ = √(2 × 7,300 × 500 ÷ 20) = √365,000 ≈ **604 units** (≈ 12.1 orders/year).

**Assumptions/limitations:** steady, known demand; constant costs; no quantity discounts; no storage or cash limit; no shelf-life limit; instantaneous replenishment. In practice apply supplier minimum order quantities, pack sizes, discount tiers, cash and storage caps, and shelf life; treat EOQ as a **starting point**.

## 8. Order quantity vs. forecast

Suggested order = depends on policy:
- **(s, Q) policy:** when position ≤ s (ROP), order Q (e.g., EOQ, adjusted for constraints).
- **Order-up-to policy:** order `max(0, target level − position)`.
Then adjust for MOQ, pack size, budget, shelf life. Always show the inputs used.

## 9. ABC analysis

For standard inventory ABC analysis, rank items by annual consumption value = annual quantity consumed × unit acquisition cost. Do not substitute sales revenue for unit cost in this calculation. If you also classify products by sales revenue, label that separately as revenue-based ABC analysis. Typical value splits (illustrative and configurable): A ≈ the first 70–80% of cumulative consumption value, B the next ≈15–20%, and C the remainder; actual item counts vary.

| Class | Control approach |
|---|---|
| A | Tight control, frequent counts, careful forecasting, closer supplier management |
| B | Moderate control |
| C | Simple rules, larger buffers acceptable |

Also consider criticality: a cheap part that stops production may need A-level attention. ABC is a prioritisation tool, not an ordering formula.

## 10. Inventory turnover and days inventory outstanding

- **Turnover** = COGS ÷ average inventory value (same period). Example: COGS 840,000 ÷ average inventory 140,000 = **6.0 times/year**.
- **DIO** = average inventory ÷ COGS × days = 140,000 ÷ 840,000 × 365 ≈ **60.8 days**.
- Benchmarks vary widely by industry; compare with the business's own history and similar businesses (validated benchmarks are required).
- Limitations: needs inventory valuation snapshots; start/end averages hide seasonality; high turnover may mean stockouts.

## 11. Stockouts and excess inventory

| | Stockout | Excess |
|---|---|---|
| Cause | Late supplier, under-forecast, inaccurate records, wrong ROP | Over-forecast, bulk buying, discontinued products, no sales follow-up |
| Cost | Lost sales, customer loss, expediting costs | Tied-up cash, storage, shrinkage, obsolescence, markdowns |
| Metric | Stockout days; fill rate | Stock cover days; carrying cost |

**Fill rate** = units shipped from stock ÷ units demanded. **Stock cover** = available ÷ average daily demand.

## 12. Slow-moving, obsolete, dead, perishable stock

| Category | Illustrative definition (configure) | Typical response |
|---|---|---|
| Slow-moving | Stock cover far above normal (e.g., > 180 days) | Promotion, bundling, stop reordering |
| Dead | No sales in a long period (e.g., 12 months) | Liquidate, return to supplier, write off (accountant) |
| Obsolete | Product replaced/discontinued/expired | Write-down/disposal |
| Perishable | Shelf-life limited | FEFO/FIFO, smaller order cycles, minimum shelf-life at receipt |

Write-downs affect accounting profit; involve an accountant.

## 13. Supplier reliability, seasonality, and min/max levels

- **Supplier on-time-in-full (OTIF)** = orders received on time and complete ÷ orders received. Falling OTIF increases required safety stock.
- **Seasonality:** do not use a flat average where demand is seasonal; compute seasonal indices (Guide 9). Build ahead of peaks within cash limits.
- **Min/max levels:** min ≈ ROP; max ≈ ROP + order quantity (or storage/cash cap). Revisit when demand, lead time, or costs change.

## 14. Carrying costs

Capital cost + storage + insurance + handling + shrinkage/obsolescence. Often 15–30% of inventory value per year in common textbook ranges — **illustrative only; compute your own** `[SOURCE NEEDED for any benchmark claim]`.

## 15. Recommended responses

| Situation | Check first | Possible actions |
|---|---|---|
| Position ≤ ROP | Data quality, open orders | Place order (Q per policy), expedite if cover < lead time |
| Uncertain demand | History length, volatility | Smaller more frequent orders, higher safety stock for critical items, test promotions cautiously |
| Excess stock | Real cause, shelf life | Stop reordering, promotions, return to supplier |
| Frequent stockouts | Lead time, ROP inputs, record accuracy | Recalculate ROP, change supplier or add backup |
| Large count variances | Process errors, theft, unit errors | Cycle count, tighter receiving/issuing controls |

## 16. What ALLADIN can and cannot say

- ALLADIN may state *"Based on the last N days of sales and a lead time of L days, the estimated reorder point is X"* with the inputs shown.
- If stock, units of measure, lead time, or demand history are missing or inconsistent, ALLADIN must **decline to give a reorder quantity** and list what is needed.
- It must not treat a forecast as confirmed demand.

## 17. Related documents
Guide 9 (forecasting), Guide 8 (supply chain), Guide 12 (stockout and excess cases); rules `INV-001`–`INV-013`.

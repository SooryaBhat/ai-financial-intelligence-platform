---
document_id: BR-04
title: "Inventory Decision Rules"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: inventory_rules
content_type: AI_assisted_draft
review_status: unreviewed
license_reuse_status: "Internal, project-owned; AI-assisted"
applicable_region: general
---

# Business Rules 04: Inventory Decision Rules (INV-001 to INV-013)

> Status: `proposed` / `configuration_dependent`; none validated. Field names are **ASSUMED**. Explanations: Guide 3. Global conventions (tenant scope, soft deletes, units, empty periods) follow `01_financial_calculation_rules.md` G-1…G-10.

## Hard gate (MANDATORY): INV-012 runs first
No reorder point, reorder quantity, or stockout-risk output is produced for an item unless INV-012 passes. Failure ⇒ outcome `INSUFFICIENT_DATA` with the failing checks listed.

## INV-001 Current and Available Stock
| Field | Specification |
|---|---|
| Purpose | Establish sellable stock |
| Required fields | `products.stock_quantity` (on-hand), optional `reserved_quantity`, `damaged_quantity` — ASSUMED |
| Logic | `Available = OnHand − Reserved − Damaged`; if reserved/damaged not tracked, Available = OnHand **and the output states "reservations not tracked"** |
| Outcome | On-hand, available, flags |
| Severity | info; high if available < 0 |
| Exceptions | Negative on-hand ⇒ data error, not zero |
| DQ checks | Negative values, non-integer units where integers expected, unit-of-measure missing |
| Explanation | "<Product> has <A> units available (<O> on hand, <R> reserved)." |
| Tests | 150/20/0 ⇒ 130; on-hand −5 ⇒ DATA_ERROR. |
| Status | proposed |

## INV-002 Inventory Position (including incoming)
| Logic | `SellableOnHand = OnHand − DamagedOrQuarantined` when damaged/quarantined stock is included in OnHand; otherwise use the already-net sellable OnHand and do not subtract twice. `Position = SellableOnHand + OnOrder − Reserved − Backorders`. OnOrder comes from open purchase orders not yet received (field ASSUMED `purchase_order_items`). If any material component is not tracked, state it and warn that the position may be incomplete; do not silently assume zero. |
|---|---|
| Preconditions | INV-001 |
| Outcome | Position and which components were available |
| Severity | info |
| Tests | 150 + 100 − 20 = 230; on-order untracked ⇒ warning. |
| Status | configuration_dependent |
(Other fields: Domain Inventory; DQ checks: POs past due date flagged; Evidence: PO IDs.)

## INV-003 Average Demand
| Field | Specification |
|---|---|
| Purpose | Estimate average daily demand from history |
| Required | Sales line items: `product_id`, `quantity`, date, status (ASSUMED) |
| Logic | `d = Σ quantity (completed sales) in window ÷ days in window` (calendar days incl. zero-sale days); `σ_d` = standard deviation of daily (or weekly) quantities in same window |
| Config | Window length (CONFIG, illustrative 90 days); minimum history (illustrative ≥ 28 days with ≥ 8 sale days) |
| Outcome | d, σ_d, history length, number of zero days |
| Edge cases | Stockout days understate demand (flag if stock was 0 for part of window; optionally exclude those days, stated); one-time bulk orders (flag outliers, do not silently drop); new products with short history ⇒ `INSUFFICIENT_DATA`; returns net of sales only if configured |
| Explanation | "Average demand is <d> units/day over the last <W> days (<z> days with no sales)." |
| Tests | 180 units over 90 days ⇒ 2.0/day. 10 days history ⇒ INSUFFICIENT_DATA. |
| Status | configuration_dependent |

## INV-004 Lead Time
| Logic | `L = mean(receipt_date − order_date)` over the last N received orders for the supplier/item (CONFIG N, illustrative ≥ 3); `σ_L` = standard deviation. Units: days. |
|---|---|
| Fallback | A tenant-entered nominal lead time may be used **if labelled "owner-supplied, not measured"** |
| Outcome | L, σ_L, source (measured/owner-supplied) |
| Edge | Missing lead time and no owner value ⇒ INSUFFICIENT_DATA (blocks INV-005/006/007) ; lead time 0 or negative ⇒ DATA_ERROR |
| Explanation | "Supplier <S> has taken about <L> days (±<σ_L>) from order to delivery, based on <n> orders." |
| Tests | Orders 8, 10, 9 days ⇒ L = 9.0. No history, no owner value ⇒ INSUFFICIENT_DATA. |
| Status | configuration_dependent |

## INV-005 Safety Stock
| Field | Specification |
|---|---|
| Logic | If lead-time variability `σ_L` is measured and demand/lead-time variability assumptions are acceptable: `SS = z × √(L×σ_d² + d²×σ_L²)`. Use the fixed-lead-time formula `SS = z × σ_d × √L` only when fixed lead time is a defensible, documented assumption (for example, measured variability is negligible with sufficient observations). If `σ_L` is unknown or based on too little data, do **not** treat it as zero automatically: return `INSUFFICIENT_DATA` or a clearly labelled low-confidence estimate using an explicitly approved fallback. `z` from service level (CONFIG per item class; illustrative A: 97.5% z=1.96, B: 95% z=1.65, C: 90% z=1.28). Round up to whole units. |
| Preconditions | INV-003 and INV-004 succeed; demand and lead time in same time units |
| Outcome | SS with method name |
| Severity | n/a |
| Edge | Unknown/poorly estimated lead-time variability ⇒ do not silently use the fixed-lead-time formula; request more data or use an explicitly approved, labelled fallback. Intermittent demand (> CONFIG share of zero days, illustrative 50%): normal approximation unreliable ⇒ flag `METHOD_LOW_CONFIDENCE` and recommend an owner-set minimum stock instead; perishable/shelf-life caps apply |
| Explanation | "Safety stock of <SS> units targets a <p>% service level given demand variability and lead time." |
| Tests | d=20, σ_d=6, L=9, z=1.65, documented fixed lead time ⇒ 29.7 → 30. Unknown `σ_L` without an approved fallback ⇒ INSUFFICIENT_DATA/low-confidence labelled result, not an assumed zero. |
| Status | configuration_dependent |

## INV-006 Reorder Point
| Logic | `ROP = d × L + SS` (units). Trigger: `Position ≤ ROP` |
|---|---|
| Preconditions | INV-012 pass; INV-002–005 outputs |
| Outcome | ROP, position, `REORDER_DUE` / `OK` |
| Severity | medium when due; high if cover < L (see INV-008) |
| Follow-up | Show INV-007 quantity; confirm supplier availability |
| Edge | Seasonal items: use seasonal-adjusted d (configured); promotions; forecast (not confirmed orders) may replace d only if labelled |
| Explanation | "Reorder point is <ROP> (= <d>×<L> expected demand during lead time + <SS> safety stock). Current position is <P>." |
| Tests | 20×9+30 = 210; position 130 ⇒ REORDER_DUE; position 300 ⇒ OK; lead time missing ⇒ INSUFFICIENT_DATA. |
| Status | configuration_dependent |

## INV-007 Suggested Reorder Quantity
| Field | Specification |
|---|---|
| Logic | Policy (CONFIG per item): (s,Q): `Q = EOQ` if costs known, else owner-set `Q`; order-up-to: `Q = max(0, Target − Position)`, Target = ROP + review-period demand. Then `Q = clamp(Q, MOQ, max_by_storage_or_cash)`, rounded up to pack size. Shelf life cap: `Q ≤ d × (shelf_life_days − min_remaining_days)`. |
| EOQ | `√(2DS/H)`, D=d×365; needs order cost S and holding cost H (CONFIG) else not used |
| Outcome | Q with every constraint applied and shown; `NO_RECOMMENDATION` if essential inputs missing |
| Severity | n/a |
| Edge | Forecast ≠ confirmed orders; supplier MOQ above need; budget cap; uncertain demand ⇒ recommend a smaller, repeated order and show range |
| Explanation | "Suggested order: <Q> units (basis: <policy>). Constraints applied: <list>. This is a suggestion; no order has been created." |
| Tests | EOQ example ⇒ 604; MOQ 700 ⇒ 700 with note; shelf-life cap lowers Q; S or H missing ⇒ uses owner Q or NO_RECOMMENDATION. |
| Status | configuration_dependent |

## INV-008 Stockout Risk
| Logic | `Cover = Available ÷ d` (days). Classes (CONFIG illustrative): `Cover < L` ⇒ HIGH; `L ≤ Cover < L + review/buffer days` ⇒ MEDIUM; else LOW. Available = 0 with d > 0 ⇒ STOCKED_OUT. |
|---|---|
| Preconditions | INV-012, INV-003, INV-004; d > 0 (d = 0 ⇒ "no recent demand", not risk) |
| Outcome | Class + cover days + expected stockout date estimate (labelled estimate) |
| Severity | high/medium/low as class |
| Follow-up | Check open POs, expedite, partial orders |
| Edge | Incoming stock arriving before the stockout date reduces risk (use due dates if tracked); demand spikes |
| Explanation | "At about <d>/day, <A> units cover roughly <C> days; replenishment takes about <L> days, so <product> may run out before new stock arrives." |
| Tests | 130/20 = 6.5 < 9 ⇒ HIGH; 300/20 = 15 ≥ 9 + 5 ⇒ LOW; d=0 ⇒ no demand. |
| Status | configuration_dependent |

## INV-009 Excess Inventory
| Logic | `Cover > ExcessCoverDays` (CONFIG, illustrative 120 days) or `Position > MaxLevel`; excess units = `Available − MaxLevel`. Value = units × unit cost (if cost known). |
|---|---|
| Outcome | EXCESS flag, estimated tied-up value |
| Severity | low/medium |
| Edge | Seasonal build, planned promotions, long-lead-time items, MOQ-driven stock; shelf-life items raise severity |
| Follow-up | Pause reordering; check expiry; consider promotion/return (trade-offs in Guide 3) |
| Tests | 400 units, d=2 ⇒ 200 days ⇒ EXCESS at 120; seasonal flag suppresses alert. |
| Status | configuration_dependent |

## INV-010 Slow-Moving and Dead Stock
| Logic | Slow: no sale in last `SlowDays` (CONFIG 90) **or** annual turnover of the item < CONFIG; Dead: no sale in `DeadDays` (CONFIG 365) and stock > 0. New products (age < `SlowDays`) excluded. |
|---|---|
| Outcome | Class + last sale date + stock value |
| Edge | Stockout hid sales; item is a spare part/safety item; recent price/promo change |
| Follow-up | Verify record accuracy first; then markdown/return/write-off (accountant for write-offs) |
| Tests | Last sale 200 days ago ⇒ slow; 400 days ⇒ dead; created 30 days ago ⇒ excluded. |
| Status | configuration_dependent |

## INV-011 Inventory Turnover and DIO
| Logic | `Turnover = COGS ÷ AvgInventoryValue`; `DIO = AvgInventoryValue ÷ COGS × days`. Average = mean of period-start/end or monthly snapshots (stated). |
|---|---|
| Required | COGS (FIN-004 dependency), inventory valuation snapshots (ASSUMED) |
| Outcome | Value or CANNOT_CALCULATE if COGS or snapshots missing; avg inventory = 0 ⇒ UNDEFINED |
| Edge | Seasonality; valuation method (FIFO/average) must be stated |
| Tests | 840,000/140,000 = 6.0; DIO 60.8 days. |
| Status | configuration_dependent |

## INV-012 Stock Data Quality Gate (MANDATORY)
Checks per item; any failure blocks INV-006/007/008:
1. On-hand not null and ≥ 0
2. Unit of measure present and consistent between stock, sales, and purchases (e.g., not kg vs grams)
3. Lead time available (measured or owner-supplied)
4. Demand history ≥ minimum (INV-003)
5. No unresolved large reconciliation variance (> CONFIG % of stock, illustrative 10%) in the last count
6. Stock last updated within `MaxStaleDays` (CONFIG, illustrative 7 days) — if inventory updates are manual
| Outcome | `PASS` / `INSUFFICIENT_DATA` + list of failures |
|---|---|
| Explanation | "I can't give a reliable reorder recommendation for <product> because <failures>." |
| Tests | Missing lead time ⇒ fail (check 3); negative stock ⇒ fail (1); sales in units but stock in cartons ⇒ fail (2). |
| Status | proposed |

## INV-013 Supplier Delay Considerations
| Logic | If open PO `expected_date < today` or recent supplier OTIF < CONFIG (illustrative 85%): increase effective L by observed average delay (or recompute σ_L), and flag affected items. |
|---|---|
| Outcome | `SUPPLIER_DELAY_FLAG` + adjusted ROP shown alongside the standard one |
| Follow-up | Contact supplier, consider an alternate source (supplier concentration, Guide 8) |
| Edge | One-off delay (holiday) vs pattern; use ≥ 3 orders before calling a pattern |
| Tests | 2 of 3 POs late by avg 4 days ⇒ flag, L+4. |
| Status | configuration_dependent |

## Schema items to reconcile
Stock fields (on-hand/reserved/damaged), purchase orders and expected dates, lead-time fields, unit of measure, product cost fields, reorder settings per product, stock-count adjustment table, valuation snapshots.

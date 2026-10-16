---
document_id: BG-12
title: "Practical Business Case Studies and Decision Playbooks"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: case_studies
chapter: null
section: null
page_number: null
source_url: null
license_reuse_status: "Internal, project-owned; AI-assisted; no third-party text reproduced"
content_type: fictional_case_study
review_status: unreviewed
applicable_region: general
---

# Guide 12: Practical Business Case Studies and Decision Playbooks

> **ALL CASES ARE FICTIONAL.** Business names, people, and figures are invented for teaching. They are **not real research findings**, not benchmarks, and not evidence about any actual business. Thresholds mentioned are illustrative. Each case follows the same eight steps. Rule IDs refer to the ALLADIN rules library.

---

## Case 1 — Rising revenue but falling cash (fictional "Kavya Textiles")

| Step | Content |
|---|---|
| 1. Situation | Quarterly revenue rose from 400,000 (Q1) to 480,000 (Q2), +20%. Net profit for Q2 was 40,000. Yet the cash balance fell from 80,000 to 35,000. The owner asks, "How can we be growing and short of cash?" |
| 2. Data needed | Revenue by quarter (invoiced basis), net profit, receivables ageing, inventory values, payables, loan repayments, owner drawings, actual cash movements (bank), payment terms given to customers |
| 3. Calculations | Assume (simplification) all sales are on credit. Receivables 120,000 → 180,000; inventory 150,000 → 180,000; payables 90,000 → 95,000. Operating cash ≈ 40,000 − 60,000 (ΔAR) − 30,000 (ΔInventory) + 5,000 (ΔAP) = **−45,000**, matching the cash fall 80,000 → 35,000 (no financing assumed). DSO (90-day quarter): Q1 = 120,000 ÷ 400,000 × 90 = **27.0 days**; Q2 = 180,000 ÷ 480,000 × 90 = **33.75 days** |
| 4. Plausible explanations | Customers paying more slowly; new customers on longer terms; stock built ahead of expected demand; supplier terms unchanged while sales grew; owner drawings or loan repayments (not in profit) |
| 5. Can / cannot conclude | **Can:** profit and cash diverged because receivables and inventory grew faster than payables. **Cannot:** that customers are "bad payers" (no ageing data), that the stock build was unnecessary, or that cash will keep falling |
| 6. Next checks | Receivables ageing by customer; terms on new accounts; which items drove the inventory rise; bank reconciliation; non-P&L cash items (drawings, loan principal) |
| 7. Actions & trade-offs | Tighter terms or deposits on large new accounts (risk: lose customers); follow-up on overdue invoices (relationship cost); pause non-critical stock buying (stockout risk); short-term credit line (interest cost) |
| 8. Evaluate | Track DSO, operating cash flow, overdue share over the next 3 months versus the Q2 baseline; check revenue retention of customers whose terms changed |

---

## Case 2 — Increasing expenses and declining margins (fictional "Ravi Hardware")

| Step | Content |
|---|---|
| 1. Situation | Monthly revenue grew 200,000 → 210,000 (+5%) but profit seems lower. |
| 2. Data needed | Revenue, COGS by product/supplier, discounts, operating expenses by category, unit costs and selling prices, sales mix |
| 3. Calculations | COGS 120,000 → 135,000 (+12.5%); gross profit 80,000 → 75,000; **gross margin 40.0% → 35.7%** (75,000 ÷ 210,000). Operating expenses 50,000 → 55,000 (+10%); operating profit 30,000 → 20,000; **operating margin 15.0% → 9.5%** |
| 4. Plausible explanations | Supplier price increases not passed on; more discounting; mix shift toward lower-margin goods; stock cost recorded incorrectly; new expenses (e.g., delivery); one-off repairs |
| 5. Can / cannot conclude | **Can:** costs grew faster than revenue; margin fell by 4.3 points at gross level. **Cannot:** which cause, whether it is temporary, or that "staff are overspending" |
| 6. Next checks | Unit cost trend per top-10 products; average selling price; discount total; category mix; expense lines that rose (EXP-002); entry errors |
| 7. Actions & trade-offs | Renegotiate or switch suppliers (quality/reliability risk); price adjustment on affected items (volume loss); reduce blanket discounts (customer reaction). **Do not** cut costs protecting safety/quality without analysis |
| 8. Evaluate | Gross margin and average unit cost for the targeted products monthly; volume change after any price action versus prior-year same months |

---

## Case 3 — Frequent stockouts (fictional "Fresh Basket Kirana")

| Step | Content |
|---|---|
| 1. Situation | A 5 kg rice pack was out of stock on 9 of 30 days. The owner reorders when stock hits 40 units. |
| 2. Data needed | Daily sales units (including zero days), stock history, supplier lead times, open orders, pack/unit definitions |
| 3. Calculations | Average demand d = 12 units/day, σ_d = 5. Lead time L averages 6 days (observed 4–10), σ_L = 2. Expected lead-time demand = 12 × 6 = 72. Safety stock (95%, z = 1.65) = 1.65 × √(6 × 25 + 144 × 4) = 1.65 × √726 ≈ 1.65 × 26.9 ≈ **44.5 → 45**. **ROP ≈ 72 + 45 = 117**, versus the owner's 40. Cover at 40 units = 40 ÷ 12 = 3.3 days < 6-day lead time |
| 4. Plausible explanations | Reorder point too low for lead time; variable supplier delivery; stock record errors; unrecorded demand spikes |
| 5. Can / cannot conclude | **Can:** with these inputs, a reorder at 40 units cannot cover average lead-time demand. **Cannot:** that 117 is "correct" (assumes normal-ish demand and estimates from limited data) or what the best order quantity is |
| 6. Next checks | Verify stock accuracy by a count; confirm lead-time records; check whether demand was censored by the stockouts; look for open orders |
| 7. Actions & trade-offs | Raise the reorder point toward the calculated value (more cash and shelf space tied up); add a backup supplier; order smaller more often (more order costs) |
| 8. Evaluate | Stockout days per month and fill rate; stock cover; waste/spoilage if relevant, over 2–3 months |

---

## Case 4 — Excess inventory and slow-moving products (fictional "Lakshmi Gifts")

| Step | Content |
|---|---|
| 1. Situation | The shop bought heavily before a festival to get a bulk discount. Months later, the storeroom is full and cash is tight. |
| 2. Data needed | Stock by item with cost, last sale date, sales history, supplier return terms, shelf life/obsolescence, storage costs |
| 3. Calculations | Annual COGS 1,200,000; average inventory 600,000 ⇒ turnover **2.0**, DIO = 600,000 ÷ 1,200,000 × 365 = **182.5 days**. Items with no sale in 120 days: stock value 210,000 (35% of inventory). Illustrative carrying cost at 25% per year ⇒ 210,000 × 0.25 = **52,500/year** |
| 4. Plausible explanations | Over-forecast; discount-driven bulk buying; fashion/season ended; poor display; stockout-driven sales shifts |
| 5. Can / cannot conclude | **Can:** a large share of stock is slow-moving. **Cannot:** that it is worthless; the carrying-cost figure is illustrative and the true cost depends on the business |
| 6. Next checks | Verify records by counting; check seasonality (are the items sold at next festival?); supplier return/exchange options; shelf life |
| 7. Actions & trade-offs | Stop reordering these items; bundle or promote (margin loss); return to supplier (fees); hold for the season (cash tied up); write-down with an accountant if needed |
| 8. Evaluate | Slow-stock value and share monthly; inventory turnover and DIO; cash released versus margin given up |

---

## Case 5 — Declining sales in one category (fictional "Urban Footwear")

| Step | Content |
|---|---|
| 1. Situation | Total sales fell 6%, 500,000 → 470,000. The owner suspects "the market is weak". |
| 2. Data needed | Sales by category, units, prices, stock availability by size, returns, promotions, foot traffic if available |
| 3. Calculations | Sports shoes: 200,000 → 140,000 (**−30%**); other categories: 300,000 → 330,000 (+10%). Total: 140,000 + 330,000 = 470,000 ✓. Sports shoes lost 60,000; others gained 30,000 — the decline is concentrated in one category. Stock records show the popular sizes were out of stock 12 days; prices rose 8% |
| 4. Plausible explanations | Stockouts in key sizes; price increase; new competitor nearby; seasonal pattern; supplier quality issues; display changes |
| 5. Can / cannot conclude | **Can:** the decline is category-specific, not general. **Cannot:** which factor caused it, or that the price increase is responsible (several changes coincided) |
| 6. Next checks | Units versus price effect; sales on days in stock vs out of stock; same months last year; return reasons; competitor activity (evidence-based only) |
| 7. Actions & trade-offs | Fix availability of top sizes (cash); test price rollback on part of the range (margin); promotion (margin) |
| 8. Evaluate | Category sales per in-stock day; compare tested vs untested items; review after 6–8 weeks |

---

## Case 6 — Unusual transactions (fictional "Sharma Packaging")

| Step | Content |
|---|---|
| 1. Situation | ALLADIN flags two items: (a) an 85,000 "Repairs" expense; (b) two 12,500 invoices from the same vendor on the same day. |
| 2. Data needed | Expense history by category, vendor records, invoice numbers and documents, approvals, asset register |
| 3. Calculations | Repairs history: median 6,000, Q1 4,000, Q3 8,000, IQR 4,000. Upper fence = Q3 + 3 × IQR = **20,000**; 85,000 exceeds it and is **14.2× the median**. Duplicate-looking: same vendor, same amount, same date |
| 4. Plausible explanations | Generator replacement (capital expense recorded as repair); annual maintenance contract; split delivery billed twice legitimately; accidental double entry |
| 5. Can / cannot conclude | **Can:** both items differ from the usual pattern and deserve review. **Cannot:** that anything improper happened; that either is an error |
| 6. Next checks | Invoice and supporting documents; approval record; whether the item is an asset; vendor statement; invoice numbers |
| 7. Actions & trade-offs | If duplicate: reverse one entry and recover/offset payment (relationship); if capex: reclassify (changes profit presentation; accountant). Do not accuse staff or suppliers without evidence |
| 8. Evaluate | Flag resolution recorded with outcome; false-positive rate; threshold tuning after feedback |

---

## Case 7 — Inaccurate inventory records (fictional "Mehta Electricals")

| Step | Content |
|---|---|
| 1. Situation | The system shows 250 units of an item; a physical count finds 205. Reorder alerts have been unreliable. |
| 2. Data needed | System stock history, goods receipts, issues, returns, adjustments, count sheets, units of measure |
| 3. Calculations | Variance = 205 − 250 = **−45 units (−18%)**. Cycle count of 40 items: 31 matched ⇒ record accuracy = 31 ÷ 40 = **77.5%** |
| 4. Plausible explanations | Sales recorded without stock issue; returns not restocked; damaged goods not written off; receiving errors; unit-of-measure mix (pieces vs boxes); theft or loss; delayed entry |
| 5. Can / cannot conclude | **Can:** records are unreliable for this item and some others; reorder rules (INV-012) must not be trusted. **Cannot:** the cause or that theft occurred |
| 6. Next checks | Trace movements for the item since the last count; check negative-stock periods; compare receipts to purchase orders; check unit definitions |
| 7. Actions & trade-offs | Adjust the system with a documented reason; schedule cycle counts (staff time); tighten receiving/issuing procedures (friction); investigate losses via professional channels if a pattern emerges |
| 8. Evaluate | Record accuracy % each count; value of adjustments; stockouts or overstocks traced to bad records |

---

## Case 8 — Supplier delays (fictional "Green Valley Cafe Supplies")

| Step | Content |
|---|---|
| 1. Situation | A supplier promises delivery in 7 days. The business has had several late deliveries. |
| 2. Data needed | PO dates, promised dates, receipt dates, quantities received, reasons for delay, alternate suppliers |
| 3. Calculations | Last five deliveries took 9, 12, 8, 14, 10 days: mean = 53 ÷ 5 = **10.6 days**; sample SD ≈ **2.4**; on-time (≤ 7 days) = **0 of 5**. With demand d = 20/day and σ_d = 6, planning with L = 10.6 and σ_L = 2.4 gives lead-time demand = 212 and safety stock (95%) = 1.65 × √(10.6 × 36 + 400 × 5.8) ≈ 1.65 × 52 ≈ **86**, so **ROP ≈ 298** (versus about 166 if the 7-day promise were trusted with no variability: 140 + 26) |
| 4. Plausible explanations | Supplier capacity problems; transport issues; seasonal congestion; the business ordering late or with unclear specifications |
| 5. Can / cannot conclude | **Can:** actual lead time is much longer than promised in this small sample. **Cannot:** that the supplier is "unreliable" long-term (n = 5) or why |
| 6. Next checks | More order history; reasons for late shipments; the supplier's own explanation; compare other suppliers' lead times |
| 7. Actions & trade-offs | Raise ROP (more stock/cash); discuss service-level agreement; add a secondary supplier (switching costs, price); expedite critical items (fees) |
| 8. Evaluate | OTIF %, lead-time mean and SD, stockout days for affected items over the next quarter |

---

## Case 9 — Revenue forecast with high uncertainty (fictional "Anand Crafts")

| Step | Content |
|---|---|
| 1. Situation | The owner wants a forecast for next month; only 10 months of data exist, and revenue swings widely. |
| 2. Data needed | Monthly revenue (consistent basis), known events/promotions, number of trading days |
| 3. Calculations | Monthly revenue (thousands): 120, 95, 130, 80, 150, 110, 70, 160, 100, 140. Walk-forward on months 4–10: **naive** (previous month) absolute errors 50, 70, 40, 40, 90, 60, 40 = 390 over actuals 810 ⇒ **WAPE ≈ 48%**. **3-month moving average** absolute errors ≈ 35.0, 48.3, 10.0, 43.3, 50.0, 13.3, 30.0 = 230 ⇒ **WAPE ≈ 28%**. A complex model would need to beat 28% on chronological validation (FCT-002) |
| 4. Plausible explanations | Irregular orders, festivals, craft fairs, stockouts, small customer count |
| 5. Can / cannot conclude | **Can:** the series is volatile; a simple average beat the naive baseline here. **Cannot:** claim seasonality (needs ≥ 2 years), claim a precise forecast, or call any model "best" |
| 6. Next checks | Annotate events; check missing dates; gather more history; consider weekly granularity |
| 7. Actions & trade-offs | Plan with a range (e.g., around the moving average ± typical error) and a downside scenario; keep flexible costs (limits growth investment); collect data |
| 8. Evaluate | Compare forecasts with actuals each month (FCT-007); recompute WAPE; re-evaluate models after 24 months |

---

## Case 10 — Incomplete or contradictory ERP records (fictional "Patel Traders")

| Step | Content |
|---|---|
| 1. Situation | The owner asks for "profit last year". ALLADIN finds: expenses recorded for only 7 of 12 months; 30% of expenses uncategorised; 12 items with negative stock; sales headers total 500,000 but line items total 460,000 (8% gap); some invoices "paid" with no payment record. |
| 2. Data needed | Complete expense records, product costs/COGS, reconciled invoice lines and headers, payment records, stock counts |
| 3. Calculations | Expense coverage = 7 ÷ 12 = 58% of months. Header–line mismatch = (500,000 − 460,000) ÷ 500,000 = **8.0%** (beyond an illustrative 0.5% tolerance; SAL-002). Data-completeness gate fails (DQ-001, HLT-006) |
| 4. Plausible explanations | Late data entry; migration issues; discounts at header level; deleted lines; stock issues recorded without receipts; manual workarounds |
| 5. Can / cannot conclude | **Can:** report revenue on a stated basis **with a warning** about the 8% discrepancy; list missing items. **Cannot:** state profit, margins, cash position, or inventory health. ALLADIN should answer "insufficient data" (FIN-005, FIN-006, HLT-008) |
| 6. Next checks | Enter missing months; categorise expenses; reconcile lines to headers; resolve negative stock; link payments to invoices |
| 7. Actions & trade-offs | Pause decisions that depend on profit until data improves; prioritise data fixes by impact (time cost); an accountant can help reconstruct records (cost) |
| 8. Evaluate | Data-completeness percentage by dimension; number of unresolved discrepancies; date when full metrics become computable |

---

## Using these cases
These cases show the *method*: separate facts from interpretation, compute indicators with defined rules, state what cannot be concluded, check alternatives, weigh trade-offs, and measure results. Real businesses differ; do not apply any figure or threshold in a case to a real company without calibration.

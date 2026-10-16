---
document_id: BG-08
title: "Operations and Supply-Chain Management"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: operations
chapter: null
section: null
page_number: null
source_url: null
license_reuse_status: "Internal, project-owned; AI-assisted; no third-party text reproduced"
content_type: AI_assisted_draft
review_status: unreviewed
applicable_region: general
---

# Guide 8: Operations and Supply-Chain Management

> All figures are **fictional**; thresholds illustrative.

## 1. Order-to-cash process

Customer enquiry/quote → order → credit check → stock reservation → pick/pack → delivery → invoice → payment collection → reconciliation. Each hand-off is a place where delays and errors occur. Key checks: order captured correctly, stock reserved, invoice matches delivery, payment matched to invoice. Related metrics: order cycle time, invoice accuracy, DSO (Guide 2).

## 2. Procure-to-pay process

Need identified → purchase requisition → supplier selection → purchase order → goods receipt → invoice receipt → **three-way match** (PO, goods receipt, invoice) → approval → payment. Controls: approvals by value, separation of duties where staffing allows, supplier master-data checks, matching before payment. Metrics: PO cycle time, invoice match rate, early/late payment rate.

## 3. Order fulfilment

Measure: **on-time delivery** (delivered by promised date ÷ orders), **in-full** (complete quantity ÷ orders), **OTIF** (both), order accuracy, and fulfilment cycle time (order to delivery).
**Perfect-order rate** (illustrative multiplicative): on-time 95% × complete 98% × damage-free 99% = 0.95 × 0.98 × 0.99 ≈ **92.2%**. Small failures compound.

## 4. Supplier selection and evaluation

Criteria: price, quality, reliability (OTIF), lead time and variability, payment terms, financial stability, capacity, compliance, flexibility, communication. Use a **supplier scorecard** with weights (CONFIG) and evidence. **Fictional example:** OTIF 40%, quality 30%, price 20%, responsiveness 10%; Supplier X scores 90, 80, 70, 60 ⇒ 36 + 24 + 14 + 6 = **80**. Reevaluate regularly; one score hides trade-offs.

## 5. Lead-time monitoring

Record order date, promised date, receipt date. Compute mean, spread (standard deviation), and late share per supplier/item. Rising variability raises safety stock (Guide 3). Watch for drift over time and seasonal effects.

## 6. Delivery performance

Customer view: delivery vs promise. Supplier view: receipt vs promise. Track late reasons (weather, supplier, internal). Delivery promises should be set using actual lead times, not hopes.

## 7. Bottlenecks

A bottleneck is the step limiting throughput. Find it by looking for queues, waiting inventory, overtime, and long step times. Improving a non-bottleneck step does not raise output. Methods: process mapping, time sampling, queue observation. Check for data: step timestamps are required.

## 8. Quality control

Measures: defect rate (defects ÷ units inspected), return rate, complaint rate, first-pass yield. Methods: incoming inspection, sampling, checklists, root-cause review of defects (Guide 7). Cost of poor quality includes returns, rework, replacements, and reputational damage. Do not cut quality controls for short-term savings (Guide 5).

## 9. Returns and cancellations

Capture reason codes (damaged, wrong item, not as described, customer changed mind, late delivery). Track rates by product, supplier, channel. Feed supplier-caused returns into supplier evaluation. Ensure stock is updated for returns (restocked, quarantined, scrapped) to keep inventory accurate (Guide 3).

## 10. Operational efficiency and process improvement

Reduce waiting, rework, handling, duplicate data entry, and over-processing. Cycle: define metric → measure baseline → change one thing → measure again → standardise if it worked. Automation helps only if the process is clear and the data is clean.

## 11. Basic risk management

Identify, assess, respond, monitor (Guide 7 §6). Typical operational risks: supplier failure, stock errors, single-person dependence, equipment failure, data loss, payment fraud, compliance lapses. Maintain simple contingency plans and backups.

## 12. Supplier concentration

**Concentration** = share of purchases from top supplier(s). Illustrative flags (CONFIG): top supplier > 40% of purchases or sole-source for a critical item. Mitigation: qualify a secondary supplier, safety stock for critical items, longer-term agreements. Trade-offs: volume discounts and relationship benefits vs dependency risk.

## 13. Practical process metrics

| Metric | Formula | Notes |
|---|---|---|
| OTIF % | Orders on time and in full ÷ total orders | Define "on time" tolerance |
| Order cycle time | Delivery date − order date | Median and 90th percentile |
| Supplier lead time | Receipt − PO date | Mean and SD |
| Defect rate | Defective units ÷ units inspected | Needs inspection data |
| Return rate | Returned units ÷ units sold | By reason code |
| Invoice match rate | Invoices matching PO and receipt ÷ invoices | Control quality |
| Stockout rate | Stockout days ÷ days (per key item) | Needs daily stock history |
| Process step time | End − start per step | Needs timestamps |

## 14. What ALLADIN can and cannot say
ALLADIN can compute these metrics only if the ERP records the needed dates and statuses. If fulfilment dates or supplier receipt dates are missing, it should say the metric cannot be computed and suggest what to record.

## 15. Related
Guides 2, 3, 7, 12; rules INV-004, INV-013, DQ rules.

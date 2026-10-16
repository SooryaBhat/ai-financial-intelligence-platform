---
document_id: BR-01
title: "Financial Calculation Rules"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: financial_calculations
content_type: AI_assisted_draft
review_status: unreviewed
license_reuse_status: "Internal, project-owned; AI-assisted"
applicable_region: general
---

# Business Rules 01: Financial Calculation Rules (FIN-001 to FIN-015)

> **Status:** all rules are `proposed` or `configuration_dependent`; **none is validated**. Field names marked **(ASSUMED)** have **not** been verified against the real Supabase schema. Thresholds are illustrative defaults. Related explanations: Guides 1, 2, 5, 6.

## Global conventions (MANDATORY unless marked CONFIG)

| ID | Convention |
|---|---|
| G-1 | **Tenant scope:** every query filters by the authenticated user's `company_id`, enforced in the backend/DB layer (see AST-001). The company ID is never taken from user text. |
| G-2 | **Soft deletes:** exclude records where `deleted_at IS NOT NULL` (ASSUMED field) or `is_deleted = true`. |
| G-3 | **Status filters:** revenue uses only statuses that mean *completed/invoiced* sales; cancelled, draft, quote, pending-order records are excluded. The exact status values are **CONFIG** per schema. Every revenue answer states which status basis it used (order value / invoiced / completed sale / cash collected). These are never interchangeable. |
| G-4 | **Period:** half-open interval `[start, end)` in the company's configured timezone (**CONFIG**, field `companies.timezone` ASSUMED; default `Asia/Kolkata` only if explicitly configured). A date-only request means start-of-day to the start of the next day. `start < end` required, else error `INVALID_DATE_RANGE`. |
| G-5 | **Currency:** one currency per calculation. If records span multiple currencies without conversion rates ⇒ outcome `CANNOT_CALCULATE_MIXED_CURRENCY`. |
| G-6 | **Rounding:** compute in full precision (decimal type, never binary float for money); round only for display to 2 decimals; percentages to 1 decimal. |
| G-7 | **Zero / negative denominators:** if denominator = 0 ⇒ result `UNDEFINED` (never 0, never infinity). If denominator < 0 where a ratio is meaningless ⇒ `UNDEFINED_NEGATIVE_DENOMINATOR`. Explain why. |
| G-8 | **Taxes:** state whether amounts are tax-inclusive or exclusive. Indirect taxes collected for authorities (e.g., GST/VAT) are not revenue; if the schema cannot separate them ⇒ flag `TAX_BASIS_UNKNOWN`. `[INDIA-SPECIFIC: SOURCE NEEDED for GST treatment]` |
| G-9 | **Empty period:** if no qualifying records ⇒ "No matching records found for <period>" with totals shown as 0 **only** for count/sum and `UNDEFINED` for ratios. Never fabricate activity. |
| G-10 | **Evidence:** each result carries `period`, `status_basis`, `record_count`, `filters`, `excluded_counts`, `data_quality_flags`. |

---

## FIN-001 Total Revenue
| Field | Specification |
|---|---|
| Domain | Financial |
| Purpose | Sum of completed sales value for a period |
| Preconditions | Authenticated company; valid period; sales table accessible |
| Required fields | `sales.company_id`, `sales.sale_date` (or invoice_date), `sales.total_amount`, `sales.status`, `sales.deleted_at`, `sales.currency` — **all ASSUMED** |
| Logic | `Revenue = Σ sales.total_amount WHERE company_id=:cid AND status ∈ COMPLETED_STATUSES AND deleted_at IS NULL AND sale_date ∈ [start,end)` |
| Config | `COMPLETED_STATUSES` (CONFIG, mapped to the business's accounting basis; examples may include `completed` or `invoiced` only when their semantics are verified). Do **not** include `paid` automatically: payment status describes cash collection and does not by itself determine revenue recognition. Tax-inclusive flag (CONFIG). |
| Outcome | Number + currency + record count; or `NO_RECORDS` |
| Severity | info |
| Follow-up | Offer comparison with prior period (FIN-010) |
| Exceptions | Date field choice (order date vs invoice date vs delivery date) must be stated. Under an accrual basis, a valid earned/invoiced sale may count even when unpaid or partially paid; under a cash-collected measure, count settled collections by payment date instead. Do not use `paid` as a universal revenue-recognition rule. |
| Data-quality checks | Null/negative amounts; duplicate invoice numbers; future-dated sales; statuses not in known list; currency missing |
| User explanation | "Revenue for <period> was <X> from <n> completed sales (basis: <status basis>, <tax basis>). Cancelled and deleted records were excluded." |
| Evidence | Query filters, record count, excluded counts |
| Tests | T1: three completed sales 100/200/300 ⇒ 600. T2: add cancelled 500 ⇒ still 600. T3: empty period ⇒ NO_RECORDS. |
| Status | proposed |

## FIN-002 Net Revenue
| Field | Specification |
|---|---|
| Domain | Financial |
| Purpose | Revenue after refunds, returns, and discounts, avoiding double-count |
| Preconditions | FIN-001 computable; knowledge of whether `total_amount` is already net of discounts |
| Required fields | `sales.discount_amount`, `refunds.amount`, `refunds.refund_date`, `refunds.sale_id`, `refunds.status` — **ASSUMED, may not exist** |
| Logic | `NetRevenue = GrossRevenue − Σ discounts (only if total_amount is gross of discounts) − Σ refunds_in_period (status=processed)` |
| Config | `AMOUNT_IS_NET_OF_DISCOUNT` (CONFIG boolean); refund timing basis: by refund date (default) vs original sale date |
| Outcome | Net revenue, or `CANNOT_CALCULATE_RELIABLY` if refunds/discount treatment unknown |
| Severity | info (high if refunds ≥ configured % of revenue: CONFIG, illustrative 10%) |
| Follow-up | If refund share high, investigate return reasons (Guide 4) |
| Exceptions | Refund for a sale in a previous period reduces current-period net revenue under the by-refund-date basis; negative net revenue possible |
| DQ checks | Refund > original sale; refund without sale; discount > gross amount |
| User explanation | "Net revenue = revenue <X> minus refunds <R> minus discounts <D>. Refunds are counted in the month they were processed." |
| Evidence | Components shown separately |
| Tests | Revenue 1000, refunds 100, discount already netted ⇒ 900. Refund 1200 on 1000 revenue ⇒ −200 plus warning. No refunds table ⇒ CANNOT_CALCULATE_RELIABLY (state missing field). |
| Status | configuration_dependent |

## FIN-003 Total Expenses
| Field | Specification |
|---|---|
| Domain | Financial |
| Purpose | Sum of expenses in a period |
| Preconditions | Expense records with date, amount, status |
| Required fields | `expenses.company_id`, `expenses.expense_date`, `expenses.amount`, `expenses.category`, `expenses.status`, `expenses.deleted_at` — **ASSUMED** |
| Logic | `Expenses = Σ amount WHERE status ∈ COUNTED_EXPENSE_STATUSES AND deleted_at IS NULL AND expense_date ∈ [start,end)` |
| Config | `COUNTED_EXPENSE_STATUSES` (e.g. ['approved','paid']); whether drafts count (default no); basis: incurred vs paid (must be stated) |
| Outcome | Total, by-category breakdown, record count |
| Severity | info |
| Follow-up | Compare with revenue/budget; see EXP rules |
| Exceptions | Capital purchases may need separating (capex vs opex); inventory purchases are not an expense until sold (COGS) — flag if inventory purchases are stored as expenses |
| DQ checks | Uncategorised expenses; negative amounts (reversals) handled explicitly; duplicates (ANO rules) |
| User explanation | "Recorded expenses for <period> total <X> across <n> records, <k>% uncategorised. This is based on <expense date basis>." |
| Evidence | Filters, counts |
| Tests | 3 approved (100,50,25) + 1 draft 500 ⇒ 175. Uncategorised share flagged. |
| Status | proposed |

## FIN-004 Gross Profit
| Field | Specification |
|---|---|
| Purpose | Net revenue minus cost of goods sold |
| Preconditions | FIN-002 (or FIN-001 with stated limitation) and a reliable COGS |
| Required fields | COGS source: **either** `sale_items.unit_cost × quantity` (ASSUMED) **or** expenses categorised `cogs` (CONFIG mapping) |
| Logic | `GrossProfit = NetRevenue − COGS` |
| Config | COGS method (item cost snapshot / category / not available) |
| Outcome | Value; or `CANNOT_CALCULATE_RELIABLY: COGS not available` |
| Severity | info |
| Follow-up | If COGS missing, ask owner to supply product cost |
| Exceptions | Services businesses may have no COGS; using current product cost instead of cost at sale time misstates historical profit |
| DQ checks | Cost missing/zero for sold items; cost > price (negative margin) flagged for review not error |
| Explanation | "Gross profit = net revenue <X> − cost of goods sold <C> = <G>. Cost data covers <p>% of sold items." |
| Evidence | COGS coverage % |
| Tests | Rev 1000, COGS 600 ⇒ 400. COGS coverage 40% ⇒ result flagged low confidence / not reported as final. |
| Status | configuration_dependent |

## FIN-005 Operating Profit
| Logic | `OperatingProfit = GrossProfit − OperatingExpenses`, where OperatingExpenses = expenses in categories mapped `operating` (CONFIG mapping) excluding COGS, interest, tax, capex, owner drawings. |
|---|---|
| Required fields | Expense category-to-class mapping (ASSUMED/CONFIG); depreciation if tracked |
| Preconditions | FIN-004 computable; all expense categories mapped |
| Outcome | Value, or `CANNOT_CALCULATE_RELIABLY` if unmapped categories exceed CONFIG tolerance (illustrative 5% of expense value) |
| Severity | info; high if negative for configured consecutive periods (CONFIG) |
| Follow-up | Review largest operating expense categories (EXP rules) |
| Exceptions | Capex wrongly recorded as expense understates profit; one-off items should be shown separately |
| DQ checks | Unmapped categories; missing depreciation (state if excluded) |
| Explanation | "Operating profit = gross profit <G> − operating expenses <E> = <O>. <n> expense categories were unmapped and excluded/included as stated." |
| Evidence | Mapping table version |
| Tests | G 400, opex 250 ⇒ 150. Unmapped 30% ⇒ CANNOT_CALCULATE_RELIABLY. |
| Status | configuration_dependent |

## FIN-006 Net Profit
| Logic | `NetProfit = OperatingProfit − Interest − Tax ± OtherIncomeExpense` (each by category mapping). If tax is not recorded, report **"profit before tax"** and say tax is not included. |
|---|---|
| Required fields | Interest, tax, other-income categories (ASSUMED) |
| Preconditions | FIN-005; interest/tax data availability known |
| Outcome | Net profit or profit-before-tax with explicit label |
| Severity | info/high if negative persistent (CONFIG) |
| Follow-up | Suggest accountant review for tax figures |
| Exceptions | Do not estimate tax unless tenant configures a rate; if configured, label as estimate |
| DQ checks | Missing categories; negative tax (refund) |
| Explanation | "Net profit = <X> after interest <I> and tax <T>." or "Profit before tax = <X>; tax is not recorded." |
| Evidence | Components |
| Tests | O 150, interest 20, tax 30 ⇒ 100. No tax data ⇒ labelled profit before tax 130. |
| Status | configuration_dependent |

## FIN-007 / FIN-008 / FIN-009 Margins
| Rule | Formula | Denominator |
|---|---|---|
| FIN-007 Gross profit margin | GrossProfit ÷ NetRevenue | Net revenue (or revenue if net unavailable, stated) |
| FIN-008 Operating margin | OperatingProfit ÷ NetRevenue | same |
| FIN-009 Net margin | NetProfit ÷ NetRevenue | same |

| Common field | Specification |
|---|---|
| Preconditions | Numerator rule computable; denominator > 0 |
| Handling | Denominator 0 ⇒ UNDEFINED (G-7). Negative profit ⇒ negative margin, shown as such. |
| Config | Warning thresholds are **CONFIG** per industry; no universal standard. Illustrative only: gross margin drop > 5 percentage points vs prior period ⇒ medium alert |
| Outcome | Percentage (1 dp) + comparison with prior period in percentage points |
| Severity | info/medium |
| Follow-up | If margin fell: check price/discount (SAL), cost increases (EXP), product mix (Guide 4/5) |
| Exceptions | Very low revenue periods produce unstable margins; use ≥ CONFIG minimum revenue (illustrative: 10 sales) before alerting |
| DQ checks | Same as numerator rules |
| Explanation | "Gross margin was <m>% versus <p>% last period (change <d> pts). Margin shows profit per unit of revenue; a change can come from prices, costs, or mix." |
| Evidence | Numerator, denominator, period |
| Tests | 400/1000 ⇒ 40.0%. Revenue 0 ⇒ UNDEFINED. Profit −50, revenue 500 ⇒ −10.0%. |
| Status | configuration_dependent |

## FIN-010 Period-over-Period Change
| Field | Specification |
|---|---|
| Logic | `Change = Current − Prior`; `PctChange = Change ÷ ABS(Prior)` if Prior ≠ 0 |
| Preconditions | Both periods valid, same metric and basis, comparable length (or normalised per day, stated) |
| Outcome | Absolute and % change; if Prior = 0 and Current > 0 ⇒ "new activity (no prior base)"; both 0 ⇒ "no change (no activity)"; Prior < 0 ⇒ % shown with caution note |
| Severity | info; alert thresholds CONFIG (illustrative ±20% with minimum base) |
| Follow-up | Offer driver analysis (product/category/customer) |
| Exceptions | Calendar effects (days, holidays, partial current month), one-offs. A partial current period must not be compared with a full prior period unless normalised and labelled |
| DQ checks | Period completeness; missing days |
| Explanation | "<Metric> changed from <P> to <C> (<±x>%). Periods compared: <A> vs <B>." |
| Tests | 120 vs 100 ⇒ +20.0%. Prior 0, current 50 ⇒ no % shown. Partial month vs full month ⇒ warning. |
| Status | proposed |

## FIN-011 Growth Rate
| Field | Specification |
|---|---|
| Logic | Simple: FIN-010 PctChange. Compound (n periods): `CGR = (V_end ÷ V_start)^(1/n) − 1` where V_start > 0, V_end > 0, n ≥ 1 |
| Preconditions | ≥ 2 periods; positive values for compound growth |
| Outcome | Rate, or `CANNOT_CALCULATE` if non-positive endpoints |
| Config | Minimum periods (illustrative 6) before calling it a "trend" |
| Exceptions | Endpoint sensitivity; seasonality (compare same months year over year) |
| Explanation | "Average monthly growth between <A> and <B> was <g>%. This depends on the two endpoint months." |
| Tests | 100→121 over 2 periods ⇒ 10.0%. Start 0 ⇒ CANNOT_CALCULATE. |
| Status | proposed |
(Remaining standard fields — Domain: Financial; Severity: info; DQ checks: as FIN-010; Evidence: endpoints and n.)

## FIN-012 Cash-Flow Calculation
| Field | Specification |
|---|---|
| Purpose | Net cash flow when actual cash movements exist |
| Required fields | `payments.amount`, `payments.direction` (in/out), `payments.payment_date`, `payments.status` — **ASSUMED; may not exist** |
| Logic | `NetCashFlow = Σ inflows(status=settled) − Σ outflows(status=settled)` in period; `ClosingCash = OpeningCash + NetCashFlow` only if a verified opening balance exists |
| Outcome | `CANNOT_CALCULATE: cash movements not recorded` if missing. **Never infer cash from sales and expenses.** |
| Severity | high if closing cash negative or below CONFIG minimum |
| Follow-up | Reconcile to bank statement; 13-week forecast (Guide 2) |
| Exceptions | Unreconciled transfers, loans/owner funding categorised separately |
| DQ checks | Payments without invoice; bank reconciliation date |
| Explanation | "Recorded cash movements for <period>: in <I>, out <O>, net <N>." |
| Tests | In 500, out 300 ⇒ +200. No payments table ⇒ CANNOT_CALCULATE. |
| Status | configuration_dependent |

## FIN-013 Accounts Receivable and Payable
| Field | Specification |
|---|---|
| Logic | `AR = Σ (invoice_total − payments_received) for open invoices ≥ 0`; `AP = Σ (bill_total − payments_made)` for open bills; ageing buckets by `as_of_date − due_date` (CONFIG buckets 0–30, 31–60, 61–90, 90+) |
| Required fields | `invoices`, `bills`, due dates, payment allocation — **ASSUMED, not verified** |
| Outcome | Totals + ageing; `CANNOT_CALCULATE` if no invoice/payment linkage |
| Severity | medium/high if overdue share > CONFIG (illustrative 30% overdue > 60 days) |
| Follow-up | Contact top overdue customers; review terms |
| Exceptions | Credit notes, advance payments, disputed invoices |
| DQ checks | Overpayments; invoices without due date |
| Explanation | "Customers owe <X>, of which <Y> is more than 60 days overdue." |
| Tests | Invoice 1000 paid 400 ⇒ AR 600; due 70 days ago ⇒ 61–90 bucket. |
| Status | configuration_dependent |

## FIN-014 Working Capital
| Logic | `WC = CurrentAssets − CurrentLiabilities`, requiring a **balance sheet**. Optional: net operating working capital = AR + Inventory − AP (state clearly) |
|---|---|
| Preconditions | Balance-sheet or equivalent verified data; current/non-current classification |
| Outcome | Value or `CANNOT_CALCULATE: no balance-sheet data`. Do not compute from sales/expenses. |
| Severity | high if negative (CONFIG) |
| Follow-up | Review cash conversion (Guide 2) |
| Exceptions | Loan classification; inflated inventory/receivables quality |
| Explanation | "Working capital is <W> as at <date>, using current assets <A> and current liabilities <L>." |
| Tests | 440 − 120 ⇒ 320; missing liabilities ⇒ CANNOT_CALCULATE. |
| Status | configuration_dependent |

## FIN-015 Budget-versus-Actual Variance
| Logic | `Variance = Actual − Budget`; `Var% = Variance ÷ ABS(Budget)` if Budget ≠ 0. Sign convention: for revenue, positive = favourable; for expenses, positive = unfavourable. State it. |
|---|---|
| Required fields | `budgets.company_id`, `period`, `category`, `amount` — **ASSUMED, may not exist** |
| Preconditions | Budget for the same period/category/basis |
| Outcome | Variance table or `CANNOT_CALCULATE: no budget` |
| Severity | CONFIG thresholds (illustrative: |Var%| > 10% medium, > 25% high) |
| Follow-up | Investigate drivers (timing vs real overrun) |
| Exceptions | Budget 0 ⇒ Var% undefined; timing differences |
| Explanation | "Marketing spend was <A> against a budget of <B>: <V> (<p>%) <over/under>." |
| Tests | Expense actual 120 vs budget 100 ⇒ +20 (20%, unfavourable). Budget 0 ⇒ % undefined. |
| Status | configuration_dependent |

---

## Items needing reconciliation with the real schema
Sales table/status vocabulary; sale date semantics; discount/tax columns; refunds table; expense category taxonomy and class mapping; payments table; invoices/bills; budgets; balance-sheet source; timezone setting; soft-delete column names; currency fields.

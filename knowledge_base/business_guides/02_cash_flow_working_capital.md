---
document_id: BG-02
title: "Cash-Flow Management and Working Capital"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: cash_flow
chapter: null
section: null
page_number: null
source_url: null
license_reuse_status: "Internal, project-owned; AI-assisted; no third-party text reproduced"
content_type: AI_assisted_draft
review_status: unreviewed
applicable_region: general
---

# Guide 2: Cash-Flow Management and Working Capital

> All figures are **fictional**. Thresholds are illustrative. Not financial advice.

## 1. Cash inflows and outflows

| Inflows | Outflows |
|---|---|
| Customer payments (cash sales, collections of receivables) | Supplier payments |
| Loan proceeds, owner capital | Salaries and wages |
| Sale of assets | Rent, utilities, taxes |
| Interest received | Loan repayments and interest |
| Refunds from suppliers | Equipment purchases, owner drawings |

**Net cash flow = total inflows − total outflows (in a period).** Cash balance = opening cash + net cash flow.

## 2. Operating, investing, and financing cash flows

| Category | Examples | Healthy pattern (general idea) |
|---|---|---|
| Operating | Collections from customers, payments to suppliers/employees | Positive over time for a sustainable business |
| Investing | Buying/selling equipment, property | Often negative in growth phases |
| Financing | Taking/repaying loans, owner contributions | Positive early; repayments later |

A business that is only funded by new loans to pay running costs has a problem even if the total cash balance looks fine.

## 3. Why a profitable business can run short of cash

Profit counts a sale when earned; cash arrives later. Meanwhile you pay for stock, wages, and rent now.

| Cause | Mechanism |
|---|---|
| Growing receivables | Sales made on credit are not yet collected |
| Inventory build-up | Cash is converted into stock that has not sold |
| Paying suppliers faster than customers pay you | Funding gap |
| Large asset purchases or loan repayments | Cash out, not an expense in P&L (repayments) or spread (assets) |
| Taxes and annual payments falling due | Lumpy outflows |
| Rapid growth | More stock and receivables needed before revenue arrives |

**Example (Guide 1, fictional):** profit 52,500 but operating cash flow 7,500 because receivables rose 40,000 and inventory rose 30,000.

## 4. Cash-flow forecasting

**Method (direct, short-term, e.g., 13 weeks or 3 months):**
1. Start with opening cash (from bank/cash records).
2. Forecast **collections** from open invoices (by due date and customer payment history) and from expected new sales.
3. Forecast **payments**: payables due, payroll, rent, taxes, loan instalments, planned purchases.
4. Closing cash = opening + collections − payments. Repeat for each period.
5. Compare with actual each period and refine.

**Fictional 3-month example (currency units, base case):**

| | Month 1 | Month 2 | Month 3 |
|---|---|---|---|
| Opening cash | 100,000 | 90,000 | 85,000 |
| Collections | 180,000 | 170,000 | 150,000 |
| Payments | (190,000) | (175,000) | (160,000) |
| **Closing cash** | **90,000** | **85,000** | **75,000** |

A sales forecast (Guide 9) is an *input* but not a cash forecast: it must be converted using payment terms and timing.

## 5. Working capital

`Working capital = current assets − current liabilities`

- Current assets: cash, receivables, inventory (expected to convert to cash within about a year).
- Current liabilities: payables, short-term loans, taxes and wages due.
- **Net operating working capital** (often more useful) ≈ receivables + inventory − payables.
- Positive working capital is not proof of liquidity: slow-moving stock and doubtful receivables inflate it.

**Fictional balance sheet (Guide 1):** current assets = 90,000 + 150,000 + 200,000 = 440,000; current liabilities = 120,000 (assuming the loan is long-term) → working capital = 320,000. If the 180,000 loan were due within a year, working capital = 440,000 − 300,000 = 140,000. *Classification matters.*

## 6. Receivables collection

- Set clear payment terms and state them on invoices.
- Invoice promptly and accurately (errors delay payment).
- Track **ageing**; follow up before due date and immediately after.
- Offer prepayment or early-payment discounts only after computing the cost (a 2% discount for paying 20 days early is a high annualised cost of funds).
- Credit limits for risky customers; deposits for large orders.
- **Trade-offs:** strict terms may lose customers; lenient terms increase funding need and bad-debt risk.

## 7. Payables management

- Know due dates; pay on the due date (not early, not late) unless the discount justifies early payment.
- Negotiate terms with key suppliers.
- **Trade-offs:** stretching payables improves cash but may harm supplier relationships, cause supply interruptions, or breach contracts/laws on payment periods `[SOURCE NEEDED: check applicable payment-term rules]`.

## 8. Cash-conversion cycle (CCC)

Components (using period totals; annual figures use 365 days):

| Metric | Formula | Meaning |
|---|---|---|
| DSO (days sales outstanding) | Average receivables ÷ credit revenue × days | Days to collect |
| DIO (days inventory outstanding) | Average inventory ÷ COGS × days | Days stock sits |
| DPO (days payables outstanding) | Average trade payables ÷ purchases on credit × days | Days you take to pay suppliers |
| **CCC** | **DSO + DIO − DPO** | Days cash is tied up in operations |

**Fictional example:** annual credit revenue 1,200,000; COGS 840,000; average receivables 150,000; average inventory 140,000; average payables 70,000.
- DSO = 150,000 ÷ 1,200,000 × 365 = 45.6 days
- DIO = 140,000 ÷ 840,000 × 365 = 60.8 days
- DPO = 70,000 ÷ 840,000 × 365 = 30.4 days (illustrative proxy using COGS because credit purchases are not supplied; a production calculation should use credit purchases where available)
- **CCC = 45.6 + 60.8 − 30.4 = 76.0 days**

**Limitations:** needs credit-sales and COGS data; mixing cash and credit sales understates DSO's meaning; averages hide seasonality; payables should preferably relate to purchases on credit, not only COGS. If credit-purchase data is unavailable, COGS may be used only as a clearly labelled proxy; DPO and CCC then become approximate. Use consistent period-end vs average balances.

## 9. Liquidity and short-term obligations

- **Current ratio** = current assets ÷ current liabilities.
- **Quick ratio** = (cash + receivables) ÷ current liabilities (excludes inventory).
- **Cash runway** (months) = cash ÷ average monthly **net cash burn**, only when net burn is positive.
- Compare cash against **obligations in the next 30/60/90 days**, not against total liabilities.
- Ratios depend on data completeness; see Guide 6.

## 10. Seasonal cash requirements

If sales peak in a few months, stock must be bought **before** the peak and customers may pay **after** it. Identify the "trough" in the forecast (lowest cash point), arrange funding (credit line, supplier terms, saved reserve) **before** the shortfall. Seasonality needs at least two years of history to be reliable (Guide 9).

## 11. Cash reserves and contingency planning

- Typical aim: reserve to cover some number of months of fixed obligations. **The appropriate number depends on the industry, volatility, and access to credit; there is no universal figure** (illustrative default for configuration only: 1–3 months of fixed costs).
- Identify "trigger" events (customer loss, supplier price rise, delayed payments) and pre-plan responses.
- Maintain contact with lenders before you need credit.

## 12. Cash-flow warning signs

| Sign | Possible meaning | What to check |
|---|---|---|
| Revenue up, operating cash down | Collections slowing or stock build-up | AR ageing, inventory changes |
| Rising DSO | Customers paying later | Largest overdue customers |
| Rising DIO | Overstocking or slow sales | Slow-moving items (Guide 3) |
| Falling DPO | Paying suppliers faster | Terms changed? |
| Frequent overdrafts or late payments | Liquidity strain | 13-week forecast |
| Reliance on new debt for operating costs | Structural problem | Operating cash flow trend |
| Large single customer overdue | Concentration risk | Terms, credit insurance |

These are **signals to investigate**, not proof of a problem.

## 13. Scenario planning

**Scenario A — 20% of each month's collections arrive one month late** (using the base case above):

| | Month 1 | Month 2 | Month 3 |
|---|---|---|---|
| Collections | 144,000 | 172,000 | 154,000 |
| Payments | (190,000) | (175,000) | (160,000) |
| Closing cash | 54,000 | 51,000 | 45,000 |

Workings: M1 = 180,000 × 0.8 = 144,000. M2 = 170,000 × 0.8 + 36,000 = 172,000. M3 = 150,000 × 0.8 + 34,000 = 154,000. Closing: 100,000 + 144,000 − 190,000 = 54,000; + 172,000 − 175,000 = 51,000; + 154,000 − 160,000 = 45,000. (The 30,000 delayed from Month 3 arrives in Month 4.)

**Scenario B — costs rise 5%:** payments become 199,500 / 183,750 / 168,000 → closing 80,500 / 66,750 / 48,750 if collections are as in the base case. Check: 100,000 + 180,000 − 199,500 = 80,500; + 170,000 − 183,750 = 66,750; + 150,000 − 168,000 = 48,750.

Run scenarios on the **lowest-cash point**, and decide in advance the action at each trigger level.

## 14. Practical improvement options and trade-offs

| Option | Benefit | Trade-off / risk |
|---|---|---|
| Faster invoicing | Earlier cash | Needs process discipline |
| Early-payment discount | Faster collection | Margin cost; some pay early and still stretch |
| Deposits / advance payments | Reduces credit risk | May deter some customers |
| Negotiate longer supplier terms | More float | Possible price increase or relationship cost |
| Reduce inventory | Frees cash | Stockout risk, lost sales |
| Invoice finance / credit line | Bridges gaps | Interest and fees; dependence |
| Delay non-essential capex | Preserves cash | May postpone efficiency gains |
| Raise prices | Improves margin | Volume loss possible |

Any option's effect should be **estimated with real data** and monitored afterwards (Guide 7).

## 15. What ALLADIN can and cannot say

- With sales, expense, and payment data, ALLADIN can compute collections and payments and flag growing receivables.
- Without payment/cash data, ALLADIN **cannot** state the cash balance or runway; it must say so.
- Forecast cash positions are estimates, not guarantees.

## 16. Related documents
Guide 1, 3, 6, 9; rules `FIN-012`–`FIN-014`, `HLT` liquidity dimension.

---
document_id: BG-01
title: "Accounting Fundamentals and Financial Statements"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: accounting
chapter: null
section: null
page_number: null
source_url: null
license_reuse_status: "Internal, project-owned; AI-assisted; no third-party text reproduced"
content_type: AI_assisted_draft
review_status: unreviewed
applicable_region: general
---

# Guide 1: Accounting Fundamentals and Financial Statements

> **Status:** AI-assisted general explanation, not professional accounting advice. All numbers are **fictional**. Local rules (tax, GST, company law, accounting standards) differ by country; none are asserted here. `[INDIA-SPECIFIC: SOURCE NEEDED]` for anything India-specific.

## 1. Why this guide exists

ALLADIN reports revenue, expenses, and profit. Those words have precise meanings. If ALLADIN (or an owner) uses them loosely, conclusions go wrong: a business can show a "profit" and have no cash, or show high sales and low profit. This guide defines the terms the other guides and the rules library rely on.

## 2. Basic bookkeeping concepts

- **Transaction:** an event with money value (a sale, a purchase, a salary payment).
- **Ledger / account:** a running record for one kind of thing (Sales, Rent, Cash, Inventory).
- **Double entry:** every transaction affects at least two accounts so that the books stay balanced. Buying stock for cash: Inventory goes up, Cash goes down.
- **Chart of accounts:** the list of account categories. Consistent categories are what make expense and profit analysis possible.
- **Source documents:** invoices, receipts, bank statements. Records without a source document are harder to defend or audit.

**The accounting equation** (always true if the books are complete):

`Assets = Liabilities + Equity`

## 3. The three financial statements

| Statement | Question it answers | Covers |
|---|---|---|
| Income statement (profit & loss) | Did the business earn a profit **over a period**? | A period (month, quarter, year) |
| Balance sheet | What does the business own and owe **at a date**? | A single date |
| Cash-flow statement | Where did cash come from and go **over a period**? | A period |

### 3.1 Income statement

| Line | Meaning |
|---|---|
| Revenue (sales) | Value of goods/services delivered in the period (see accrual vs cash below) |
| − Cost of goods sold (COGS) | Direct cost of the goods actually sold |
| **= Gross profit** | Revenue − COGS |
| − Operating expenses | Rent, salaries, utilities, marketing, etc. |
| **= Operating profit** | Gross profit − operating expenses |
| − Interest, − tax (± other income) | Financing and tax effects |
| **= Net profit** | What remains for the owners |

**Fictional example — "Meera's Stationery" (FICTIONAL), one year, currency units):**

| Line | Amount |
|---|---|
| Revenue | 500,000 |
| COGS | (300,000) |
| **Gross profit** | **200,000** (margin 40%) |
| Rent | (40,000) |
| Salaries | (60,000) |
| Utilities | (10,000) |
| Other operating | (10,000) |
| **Operating profit** | **80,000** (margin 16%) |
| Interest | (10,000) |
| Profit before tax | 70,000 |
| Tax (assumed 25% for this example only) | (17,500) |
| **Net profit** | **52,500** (margin 10.5%) |

Check: 500,000 − 300,000 = 200,000; 200,000 − 120,000 = 80,000; 80,000 − 10,000 = 70,000; 70,000 − 17,500 = 52,500.

### 3.2 Balance sheet

| Assets (what it owns) | Amount | Liabilities & equity | Amount |
|---|---|---|---|
| Cash | 90,000 | Accounts payable | 120,000 |
| Accounts receivable | 150,000 | Bank loan | 180,000 |
| Inventory | 200,000 | **Total liabilities** | **300,000** |
| Equipment | 160,000 | Equity (owner's capital + retained earnings) | 300,000 |
| **Total assets** | **600,000** | **Total liabilities + equity** | **600,000** |

- **Assets:** resources expected to bring future benefit (cash, receivables, inventory, equipment).
- **Liabilities:** obligations to others (payables, loans, taxes due, customer advances).
- **Equity:** what is left for the owners after liabilities: `Equity = Assets − Liabilities`.

### 3.3 Cash-flow statement

Groups cash movements into **operating**, **investing** (buying/selling long-term assets), and **financing** (loans, owner capital, repayments, dividends). See Guide 2.

### 3.4 How the three statements connect

1. Net profit from the income statement increases **equity** (retained earnings) on the balance sheet.
2. Balance-sheet changes explain why profit differs from cash: more receivables, more inventory, fewer payables all **absorb cash**.
3. The closing cash on the cash-flow statement equals the **cash line** on the balance sheet.

**Worked example (same fictional business, for the year):**

| Item | Amount |
|---|---|
| Net profit | 52,500 |
| Increase in receivables (customers owe more) | (40,000) |
| Increase in inventory (more stock bought) | (30,000) |
| Increase in payables (suppliers paid later) | +25,000 |
| **Operating cash flow (indirect method, simplified)** | **7,500** |

The business earned 52,500 profit but generated only 7,500 of operating cash. (No depreciation or other non-cash items are included in this simplified example.)

## 4. Revenue versus cash received; expenses versus cash paid

| Event | Income-statement effect (accrual) | Cash effect |
|---|---|---|
| Sell 100,000 on credit, delivered Jan 28 | Revenue 100,000 in January | 0 in January |
| Customer pays 60,000 on Feb 20 | none | +60,000 in February |
| Buy 30,000 stock on credit in March; pay in May | not an expense until sold (it becomes COGS when sold) | 0 in March; −30,000 in May |
| Pay 12,000 annual insurance in January | 1,000 per month expense (spread over 12 months) | −12,000 in January |

**Rule of thumb:** revenue/expenses describe *economic activity*; cash describes *money movement*. Never use one to answer the other's question.

## 5. Accrual versus cash accounting

| | Cash basis | Accrual basis |
|---|---|---|
| Revenue recognised | When cash is received | When earned (goods delivered / service performed) |
| Expense recognised | When cash is paid | When incurred / matched to the revenue it helps earn |
| Pros | Simple; matches bank balance | Better picture of performance; shows receivables/payables |
| Cons | Can hide obligations and timing distortions | More complex; profit can differ from cash |

Which basis a business may or must use depends on local law and size. `[SOURCE NEEDED: confirm for the relevant jurisdiction]`. **ALLADIN implication:** the rules library requires each metric to declare whether it is order-based, invoice-based, or cash-based (see business rules FIN and SAL domains).

## 6. Gross, operating, and net profit

| Measure | Formula | What it tells you | What it hides |
|---|---|---|---|
| Gross profit | Revenue − COGS | Whether products earn more than they cost | Overheads |
| Operating profit | Gross profit − operating expenses | Core business performance | Financing, tax |
| Net profit | Operating profit − interest − tax ± other | Bottom line to owners | One-offs may distort |

Margins = profit ÷ revenue. If revenue is 0, margin is **undefined** (not 0%).

## 7. Receivables and payables

- **Accounts receivable (AR):** money customers owe you. Asset. Risk: late or non-payment.
- **Accounts payable (AP):** money you owe suppliers. Liability. Risk: late payment damages supplier trust; paying too early drains cash.
- **Ageing report:** lists AR/AP by how overdue they are (0–30, 31–60, 61–90, 90+ days). Needed for collection and cash planning.

## 8. Reporting periods and cut-off

- A **reporting period** has an exact start and end date/time in a stated timezone.
- **Cut-off:** deciding which period a transaction belongs to. A sale delivered 31 January belongs in January even if invoiced 2 February (accrual basis).
- **Common cut-off errors:** counting February deliveries in January to hit a target; recording an expense in the month it was paid rather than incurred; mixing timezones so late-night sales fall in the wrong day.
- Compare only **equal-length, comparable periods** (e.g., 28-day February vs 31-day January needs normalisation or a per-day view).

## 9. Common accounting mistakes

| Mistake | Consequence |
|---|---|
| Mixing personal and business spending | Profit and tax figures unreliable |
| Treating owner's drawings as expenses (or vice versa) | Misstated profit/equity |
| Recording purchases of long-term assets as ordinary expenses | Profit understated in one period, overstated later |
| Forgetting returns, discounts, cancellations | Revenue overstated |
| Inconsistent expense categories | Trend analysis meaningless |
| No reconciliation with bank statements | Undetected missing or duplicate entries |
| Deleting instead of voiding/reversing records | No audit trail |
| Duplicate entry of the same invoice | Revenue/expense overstated |
| Ignoring unpaid invoices | Cash problems appear "suddenly" |

## 10. How to interpret financial statements

Work in this order:
1. **Completeness:** are all periods, accounts, and statuses included? Are there drafts or unposted records?
2. **Income statement:** margins and their trend, not just the profit figure.
3. **Balance sheet:** liquidity (can short-term assets cover short-term obligations?), debt level, size of receivables and inventory relative to sales.
4. **Cash flow:** is operating cash flow broadly in line with profit over time? Persistent gaps need explanation (growth in receivables/inventory, or poor collections).
5. **Compare** with prior periods and, if available, budget or comparable businesses. A single period alone says little.
6. **Question the numbers:** one large one-off item can dominate a small business's month.

## 11. What you cannot conclude from an incomplete income statement

| If the data has only… | You **can** say | You **cannot** say |
|---|---|---|
| Sales and expense records, no COGS | Revenue total; recorded expense total | Gross profit, true profit margin |
| Revenue but only some expense categories | Revenue; a partial cost view | That the business is profitable |
| One month of data | That month's figures | A trend, seasonality, or "growth" |
| Orders (not invoices or payments) | Order demand | Recognised revenue or cash collected |
| Expenses recorded when paid | Cash-out timing | The expense actually incurred in that month |
| No balance sheet | Profit-and-loss performance | Liquidity, debt, working capital, net worth |
| No cash records | Profit (if complete) | Cash position or runway |

**ALLADIN implication:** when required components are missing, report **"insufficient data"** and name what is missing rather than computing a figure that looks complete.

## 12. Quick checklist for a monthly review

- [ ] All sales and purchases for the period entered, with correct dates
- [ ] Refunds, discounts, cancellations recorded
- [ ] Bank/cash reconciled to the books
- [ ] Receivables and payables ageing reviewed
- [ ] Expense categories consistent
- [ ] Inventory count compared to the system (see Guide 3)
- [ ] Unusual items investigated and annotated

## 13. Where to get professional help

Consult a qualified accountant for: tax filings, statutory compliance, choosing accounting policies, depreciation, valuation of stock, audits, and anything that will be shown to banks, investors, or authorities.

## 14. Related documents

Guide 2 (cash flow), Guide 5 (expenses and profitability), Guide 6 (ratios); business rules `FIN-001`–`FIN-015`, `DQ` rules.

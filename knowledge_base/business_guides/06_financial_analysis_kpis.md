---
document_id: BG-06
title: "Financial Analysis and Business Performance"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: financial_analysis
chapter: null
section: null
page_number: null
source_url: null
license_reuse_status: "Internal, project-owned; AI-assisted; no third-party text reproduced"
content_type: AI_assisted_draft
review_status: unreviewed
applicable_region: general
---

# Guide 6: Financial Analysis and Business Performance

> Ratios below use the **fictional** business from Guide 1 (revenue 500,000; COGS 300,000; operating profit 80,000; interest 10,000; net profit 52,500; cash 90,000; receivables 150,000; inventory 200,000; total assets 600,000; payables 120,000; loan 180,000 treated as long-term; equity 300,000). No ratio has a universal "good" value; compare with the business's own history and comparable businesses.

## 1. How to use ratios

A ratio compares two numbers. It is a **signal**, not a verdict. Use several together, check data completeness, compare periods, and understand the drivers.

## 2. Ratio reference

| Ratio | Formula | Data needed | Example | Interpretation | Limitations |
|---|---|---|---|---|---|
| **Liquidity** | | | | | |
| Current ratio | Current assets ÷ current liabilities | Balance sheet | 440,000 ÷ 120,000 = 3.67 | Ability to cover obligations due within ~a year | Inflated by slow stock/bad receivables; depends on classification |
| Quick ratio | (Cash + receivables) ÷ current liabilities | Balance sheet | (90,000 + 150,000) ÷ 120,000 = 2.0 | Liquidity without inventory | Receivable quality matters |
| Cash ratio | Cash ÷ current liabilities | Balance sheet | 90,000 ÷ 120,000 = 0.75 | Most conservative | Too low/high depends on cash cycle |
| **Profitability** | | | | | |
| Gross margin | Gross profit ÷ revenue | P&L with COGS | 200,000 ÷ 500,000 = 40.0% | Profit after direct costs | COGS completeness |
| Operating margin | Operating profit ÷ revenue | P&L | 80,000 ÷ 500,000 = 16.0% | Core profitability | Expense classification |
| Net margin | Net profit ÷ revenue | P&L | 52,500 ÷ 500,000 = 10.5% | Bottom line | One-offs, tax |
| Return on assets | Net profit ÷ total assets (average preferred) | P&L + balance sheet | 52,500 ÷ 600,000 = 8.75% | Profit from asset base | Asset valuation, year-end vs average |
| Return on equity | Net profit ÷ equity | same | 52,500 ÷ 300,000 = 17.5% | Return to owners | Leverage inflates it; small/negative equity unstable |
| **Efficiency** | | | | | |
| Receivables turnover | Credit revenue ÷ average receivables | Credit sales, AR | 500,000 ÷ 150,000 = 3.33 (assumes all credit) | Collection speed (DSO ≈ 365 ÷ 3.33 = 109.5 days, high) | Cash sales distort; need credit sales |
| Inventory turnover | COGS ÷ average inventory | COGS, inventory | 300,000 ÷ 200,000 = 1.5 (DIO ≈ 243 days, very high for this example) | Stock efficiency | Industry-specific |
| Asset turnover | Revenue ÷ average total assets | P&L, BS | 500,000 ÷ 600,000 = 0.83 | Revenue per asset unit | Industry-specific |
| **Leverage** | | | | | |
| Debt-to-equity | Total liabilities ÷ equity | Balance sheet | 300,000 ÷ 300,000 = 1.0 | Reliance on borrowed funds | Definitions vary (interest-bearing debt only vs all liabilities) |
| Interest coverage | Operating profit ÷ interest expense | P&L | 80,000 ÷ 10,000 = 8.0 | Capacity to pay interest | Volatile profits |

Ratios requiring balance-sheet data **cannot be computed** if ALLADIN holds no balance-sheet data.

## 3. Growth and trend measures

Revenue growth, profit trend, margin change in **percentage points**, moving averages. Use at least several periods before calling something a trend.

## 4. Working-capital analysis

Net operating working capital = receivables + inventory − payables = 150,000 + 200,000 − 120,000 = 230,000, or 46% of revenue. Rising faster than revenue means growth is cash-hungry (Guide 2).

## 5. Budget variance

See Guide 5 and rule FIN-015. Review material variances and their causes; separate timing from permanent.

## 6. KPI selection

Good KPIs are tied to a decision, measurable with reliable data, comparable over time, and few in number. **Illustrative starter set** for a small trading business: revenue, gross margin, operating expenses as % of revenue, operating cash flow, receivables overdue > 60 days, stock cover days for top items, stockout incidents, forecast error. Choose according to business model; avoid vanity metrics.

## 7. Dashboard interpretation

Check the **period**, the **basis** (order/invoiced/cash), the **data completeness**, scale of axes, and whether comparison periods are comparable. A green indicator reflects only the configured threshold.

## 8. Financial risk signals

Falling margins, rising DSO/DIO, declining cash with rising profit, increasing overdue receivables, growing reliance on debt, one customer or supplier dominating, repeated stockouts, large unreconciled differences. Signals prompt investigation.

## 9. Comparing performance across periods

Same length (or per day), same basis, same definitions, adjusted for seasonality, with one-offs identified. Prefer year-over-year for seasonal businesses.

## 10. Accounting-data limitations

Estimates (depreciation, provisions), judgement in classification, timing differences, incomplete records, different accounting policies across businesses, historical cost versus current value, and no coverage of non-financial factors (quality, relationships).

## 11. Combining indicators

Never rely on a single score. Example: strong net margin (10.5%) with DIO of 243 days and DSO of 110 days indicates profitable on paper but cash-tied-up operations. Interpret ratios as a set (liquidity + profitability + efficiency + risk).

## 12. Practical performance review (monthly)

1. Confirm data completeness. 2. Revenue and margin vs prior period and budget. 3. Expense categories with largest changes. 4. Cash and receivables. 5. Inventory health. 6. Forecast vs actual. 7. Anomalies reviewed. 8. Decide actions and owners; schedule follow-up measurement.

## 13. Related
Guides 1, 2, 5, 7; rule document 07 (business-health scorecard), `FIN` rules.

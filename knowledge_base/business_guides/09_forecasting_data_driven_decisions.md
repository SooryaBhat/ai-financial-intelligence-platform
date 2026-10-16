---
document_id: BG-09
title: "Forecasting and Data-Driven Business Decisions"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: forecasting
chapter: null
section: null
page_number: null
source_url: null
license_reuse_status: "Internal, project-owned; AI-assisted; no third-party text reproduced"
content_type: AI_assisted_draft
review_status: unreviewed
applicable_region: general
---

# Guide 9: Forecasting and Data-Driven Business Decisions

> All figures are **fictional**. A forecast is an estimate. No model is "best" merely because it is complex or fits training data well.

## 1. Historical data requirements

Reliable forecasting needs: a consistent target definition (order value vs invoiced revenue vs completed sales), regular time stamps, complete periods (no silent gaps), correct statuses (exclude cancelled/deleted), and enough history: illustrative minimums are 12 months for a non-seasonal monthly forecast and at least 24 months before claiming seasonality (rule FCT-001). Short or messy history means wide uncertainty.

## 2. Naive baselines

Always compare against simple methods:
- **Naive:** next period = last period.
- **Seasonal naive:** next period = same period last cycle (e.g., same month last year).
- **Moving average:** mean of last k periods. Example: last three months 100, 120, 110 ⇒ forecast 110.
A complex model that cannot beat these is not adding value (FCT-002).

## 3. Exponential smoothing

`F(t+1) = α × Y(t) + (1 − α) × F(t)`, 0 < α < 1. **Example** α = 0.3, F = 100, actual Y = 120 ⇒ next F = 0.3 × 120 + 0.7 × 100 = 106. If next actual is 90 ⇒ F = 0.3 × 90 + 0.7 × 106 = 101.2. Higher α reacts faster to change but follows noise. Variants add trend and seasonality (Holt, Holt-Winters).

## 4. Trend and seasonality

Trend: long-run direction. Seasonality: repeating calendar pattern. Decompose or use models that handle them. Seasonal indices need multiple cycles; with one cycle you cannot separate seasonality from one-off events. Calendar effects (number of days, holidays, festival dates that move yearly) matter.

## 5. Regression and tree-based methods

Regression with lag and calendar features, or tree-based models (e.g., gradient boosting, random forest), can capture non-linear effects. They need careful feature design (only information available at forecast time), and they **cannot extrapolate** beyond the range seen in training (trees predict within past ranges). More flexible models overfit small samples. Require walk-forward validation.

## 6. Forecast horizon

Accuracy declines with horizon. Choose the horizon based on the decision (reordering needs lead-time-length horizon; budgeting needs months). Limit horizon relative to history (FCT-005). Report the horizon in every forecast.

## 7. Training, validation, test; leakage

Split **chronologically**: oldest = training, middle = validation (model selection), most recent = test (final, used once). Random splits leak the future into training.

**Time-series leakage examples:** using this month's total to predict this month's weekly values; scaling with statistics from the whole dataset; features such as "average of next 3 months"; filling gaps with future values; choosing a model on the test set then reporting that test score as unbiased.

## 8. Walk-forward validation

Repeat: train on data up to origin t, forecast the next h periods, compare with actuals, move origin forward. Average errors across origins. This mimics real use and gives an error estimate with some spread.

## 9. Error metrics

Example: actuals A = 100, 120, 90, 110; forecasts F = 110, 115, 100, 105.
- Absolute errors: 10, 5, 10, 5 (sum 30). **MAE** = 30 ÷ 4 = **7.5**.
- Squared errors: 100, 25, 100, 25 (sum 250). **RMSE** = √(250 ÷ 4) = √62.5 ≈ **7.91** (penalises large errors more).
- **WAPE** = Σ|A − F| ÷ ΣA = 30 ÷ 420 ≈ **7.1%** (stable when some periods are small).
- **MAPE** = mean(|A − F| ÷ A) = (10.0% + 4.2% + 11.1% + 4.5%) ÷ 4 ≈ 7.5%.
**Why MAPE can mislead:** undefined when an actual is 0; explodes for near-zero actuals; asymmetric (over-forecasts penalised less than under-forecasts in bounded terms). Prefer WAPE/MAE; consider MASE (error relative to a naive forecast) for comparison across series; for intermittent demand use specialised metrics.

## 10. Forecast uncertainty

A point forecast hides uncertainty. Provide an interval or range (e.g., from residual spread or quantile models) and state its level. Wide intervals are information: they indicate that decisions should be robust. Intervals are themselves estimates and can be too narrow.

## 11. Sparse data and short histories

Aggregate to a longer period (weekly or monthly), use simple methods, pool similar items (with care for tenant data isolation), or say "insufficient data". Do not present precise numbers from 6 data points.

## 12. Missing dates and inconsistent records

Distinguish **no sales** (true zero) from **missing records** (system outage, unrecorded days). Check calendar of business-open days. Inconsistent statuses, duplicated invoices, back-dated entries, and mixed units distort forecasts; fix data before modelling (DQ rules).

## 13. Outliers and one-time events

Identify (large orders, closures, promotions, data errors). Document the cause. Options: keep, cap, or model as event; show forecast with and without. Do not remove inconvenient data silently.

## 14. Forecast versus actual

Track error each period (FCT-007). Compare model against baseline continuously. When error rises, check data changes, new products, price changes, regime shifts; retrain or fall back to baseline.

## 15. Turning forecasts into decisions

A forecast is one input.
| Decision | Forecast used for | Also need |
|---|---|---|
| Reorder stock | Demand over lead time | Current position, lead time, safety stock, MOQ, cash (Guide 3) |
| Cash planning | Sales timing | Payment terms, collections history, fixed obligations (Guide 2) |
| Hiring/capacity | Volume range | Productivity, cost, flexibility |
| Budget | Revenue range | Cost behaviour, risk appetite |
Plan using ranges and scenarios; decide trigger points to revise. State: "This is an estimate; typical past error was about X%."

## 16. Do not overclaim

Do not call a model "best" based on training fit, complexity, or a single test period. Report holdout results honestly, mention the baseline comparison, uncertainty, and data limits. Do not promise outcomes.

## 17. Related
Guides 2, 3, 6; rules FCT-001 to FCT-012, HLT-007.

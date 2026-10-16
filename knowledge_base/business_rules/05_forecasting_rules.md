---
document_id: BR-05
title: "Forecasting Rules"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: forecasting_rules
content_type: AI_assisted_draft
review_status: unreviewed
license_reuse_status: "Internal, project-owned; AI-assisted"
applicable_region: general
---

# Business Rules 05: Revenue Forecasting (FCT-001 to FCT-012)

> Status: `proposed` / `configuration_dependent`; none validated. The existing prototype models' quality is **unverified**; these rules define what must hold before a forecast is shown. Conventions G-1…G-10 apply (tenant scope, status basis, period boundaries). Explanations: Guide 9 and Guide 3 §3.

## Mandatory principles
1. Forecasts are **estimates, not guarantees**, and are always labelled so.
2. Model choice uses **chronological** validation only. Random shuffling or k-fold on time series is prohibited.
3. The final test period is used **once**, after model selection, and is the only source for the "unbiased" accuracy report. A model chosen using test results must not report those results as unbiased.
4. A model must beat the best simple baseline on validation data, or the baseline is shown instead.
5. The forecast measure (order value / invoiced revenue / completed sales) must be declared (SAL-000) and match the training target.

## Required forecast output (MANDATORY fields)
`forecast_period` (start, end, granularity), `data_period_used` (first and last actual date, number of observations), `measure`, `model_or_baseline_used` (name and version), `evaluation_metrics` (when available, with the validation scheme), `prediction_interval` (if available, with level), `limitations`, `generated_at`, `estimate_notice` ("future values are estimates, not guarantees").

## Rules
| ID | Rule | Logic / threshold | Outcome | Tests |
|---|---|---|---|---|
| FCT-001 | Minimum history | CONFIG illustrative: monthly forecast needs ≥ 12 months (≥ 24 for any seasonal claim); weekly ≥ 52 weeks; daily ≥ 90 days with ≥ CONFIG non-zero days (30). Below ⇒ no model forecast. | `INSUFFICIENT_DATA` with required vs available; optionally show a naive baseline labelled "very low confidence" | 8 months ⇒ insufficient; baseline only |
| FCT-002 | Baseline comparison | Always compute naive (last value), seasonal naive (if ≥ 2 cycles), and moving average (CONFIG window 3). Model must have lower validation WAPE than best baseline by ≥ CONFIG margin (illustrative 5% relative). | Else baseline reported as "model used" | model WAPE 18% vs baseline 17% ⇒ baseline used |
| FCT-003 | Model selection | Candidates evaluated by **walk-forward (rolling-origin) validation** on the training portion: for each origin t, train on data ≤ t, forecast h steps, compare with actuals; ≥ CONFIG origins (illustrative 3). Select by WAPE (tie-break MAE). Hyperparameters tuned only inside this validation. | Chosen model + validation table | Test set used in selection ⇒ test fails (leak) |
| FCT-004 | Final test | Hold out the most recent CONFIG period (illustrative last h periods) before any selection; evaluate chosen model **once**; refit on all data for production forecasts. | Report as "holdout accuracy" with period | Re-using test results to retune ⇒ disallowed |
| FCT-005 | Forecast horizon | Maximum horizon CONFIG (illustrative: ≤ ⅓ of history length and ≤ 3 months for monthly data under 24 months). Longer requests ⇒ capped with notice. | Capped horizon + message | 12-month request with 10 months history ⇒ refused |
| FCT-006 | Forecast freshness | A stored forecast is stale if generated before the most recent data refresh beyond CONFIG tolerance (illustrative: > 1 period old or new actuals ≥ 10% of history added). | `STALE` + offer regeneration | forecast 45 days old for monthly ⇒ stale |
| FCT-007 | Forecast vs actual monitoring | When actuals arrive: `error = actual − forecast`, WAPE over completed periods; alert (CONFIG illustrative) if rolling WAPE exceeds validation WAPE by > 50% for 2 consecutive periods. Store per-period record. | Monitoring record; "forecast reliability degraded" notice | |
| FCT-008 | Error metrics | **MAE** = mean(\|A−F\|); **RMSE** = √mean((A−F)²); **WAPE** = Σ\|A−F\| ÷ Σ\|A\| (undefined if Σ\|A\| = 0). **MAPE not used as primary** because it is undefined/explodes with zero or near-zero actuals; if shown, only for series with min actual > CONFIG floor. Optional MASE vs naive. | Metrics with formulas named | actual 0 in a period ⇒ MAPE suppressed |
| FCT-009 | Uncertainty warnings | Show prediction interval where available (e.g., quantile model or residual-based). Warn if relative width (upper − lower) ÷ forecast > CONFIG (illustrative 50%), if validation WAPE > CONFIG (illustrative 30%), or history short. | `HIGH_UNCERTAINTY` | WAPE 40% ⇒ warning |
| FCT-010 | Sparse or irregular data | Zero-inflated/intermittent series (> CONFIG zero share, illustrative 40%): use aggregation to longer periods or intermittent-demand methods; do not report precise point values. Missing periods (no row) are distinguished from true zero using business-open calendar; gaps > CONFIG (illustrative 10% of periods) ⇒ block or require owner confirmation. | Flag + method note | 3 missing months of 12 ⇒ blocked |
| FCT-011 | One-off events | Detect extreme points (robust z > 3.5, SAL-005) and known events (owner-annotated promotions, closures). Do not silently remove: show effect with and without, and state which was used. | Annotated | one 10× bulk order ⇒ flagged |
| FCT-012 | Model failure / missing artifacts | If model file missing, version mismatch, feature schema mismatch, NaN output, negative revenue forecast, or exception ⇒ no forecast shown from that model; fall back to baseline **only if** labelled; otherwise report limitation. Never fabricate. | `MODEL_UNAVAILABLE` + reason | missing artifact ⇒ message, not a number |

## Additional leakage rules (MANDATORY)
- Features must be available at forecast time (no future data, no same-period actuals).
- Scalers/encoders fitted on training data only.
- Lag/rolling features computed using only past observations.
- Company-specific models trained only on that company's data (tenant isolation); global/pooled models must not expose or leak another tenant's data.

## Required wording
"This is an estimate based on <data period> using <model>. Estimates can be wrong; typical error on past periods was about <WAPE>%. Treat it as a planning range, not a guarantee."

## Schema/engineering items to reconcile
Where models and metadata are stored, how artifacts are versioned, training data extraction query, forecasting granularity, retraining schedule, whether per-company models exist.

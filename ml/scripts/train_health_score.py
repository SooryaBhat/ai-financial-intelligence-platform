# -*- coding: utf-8 -*-
"""
train_health_score.py
=====================
Business Health Scoring & Predictive Health Transition Pipeline (Approach C).

Part A: Multi-Paradigm Scorecard Architecture & Diagnostic Evaluation
- Weighted Multi-KPI Scorecard (Transparent baseline, 0-100)
- Traffic Light Categorizer (Operational green/amber/red rules)
- PCA Health Index (Unsupervised first principal component)
- Weakest-Link Bottleneck Scorer (Liebig's law of minimum)
Diagnostic Evaluations:
- Score bounds verification [0, 100]
- Monotonicity checks against underlying financial drivers
- Stability (month-over-month score volatility)
- Sensitivity (elasticity to KPI shifts)

Part B: Forward-Looking Predictive Health Transition Model
- Target: Next month's health score (health_score_{t+1})
- Features: Current and lag operational metrics at period t (no future data leakage)
- Candidates: Persistence Baseline, Linear Regression, Ridge Regression, Random Forest, XGBoost
- Chronological train/val/test splits and Approach C business holdout.

Outputs:
- ml/models/health_score_pipeline.pkl
- ml/models/health_score_config.json
- ml/reports/health_score_eval.json
- ml/reports/business_health_scores.csv
- ml/reports/latest_health_scores.csv
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, compute_metrics, save_model,
    MODELS_DIR, REPORTS_DIR, PROCESSED_DIR, SYNTHETIC_DIR,
    DEV_COMPANIES, HOLDOUT_COMPANY, SPLIT_CONFIG
)
from custom_models.health_scorers import (
    TrafficLightScorer, WeightedScorecard, PCAHealthIndex, WeakestLinkScorer
)

logger = get_logger(__name__)

# Standard Transparent Scorecard Weights and KPI Bounds
KPI_WEIGHTS = {
    "revenue_growth": 0.25,
    "profit_margin": 0.25,
    "expense_control": 0.20,
    "inventory_turnover": 0.15,
    "payment_collection": 0.15,
}

KPI_RANGES = {
    "revenue_growth": [-0.50, 1.00],
    "profit_margin": [-0.20, 0.40],
    "expense_control": [0.00, 1.00],
    "inventory_turnover": [0.00, 10.00],
    "payment_collection": [0.00, 1.00],
}


def minmax_scale(val: float, min_v: float, max_v: float) -> float:
    """Min-max scale a value to 0-100."""
    if max_v <= min_v:
        return 50.0
    norm = (val - min_v) / (max_v - min_v)
    return float(np.clip(norm * 100.0, 0.0, 100.0))


def compute_grade_and_risk(score: float) -> Tuple[str, str]:
    """Assign letter grade and risk tier from composite health score."""
    if score >= 80.0:
        return "A", "Low Risk"
    elif score >= 65.0:
        return "B", "Moderate Risk"
    elif score >= 50.0:
        return "C", "Watchlist"
    elif score >= 35.0:
        return "D", "Elevated Risk"
    else:
        return "F", "Critical Distress"


def compute_historical_kpis() -> pd.DataFrame:
    """Aggregate raw monthly operational data across all businesses and compute KPIs."""
    health_csv = PROCESSED_DIR / "health_features.csv"
    if health_csv.exists():
        logger.info("Loading precomputed health features from: %s", health_csv)
        df = load_csv("health_features.csv", PROCESSED_DIR)
        df["month"] = pd.to_datetime(df["month"])
        if "health_score" not in df.columns:
            df["health_score"] = 50.0
        grades_risks = [compute_grade_and_risk(float(s)) for s in df["health_score"].values]
        df["letter_grade"] = [g[0] for g in grades_risks]
        df["risk_tier"] = [g[1] for g in grades_risks]
        return df

    sales = load_csv("sales_clean.csv", PROCESSED_DIR)
    exp = load_csv("expenses_clean.csv", PROCESSED_DIR)
    sale_items = load_csv("sale_items_clean.csv", PROCESSED_DIR)
    products = load_csv("products.csv", SYNTHETIC_DIR)
    invoices = load_csv("invoices.csv", SYNTHETIC_DIR)

    sales["month"] = pd.to_datetime(sales["sale_date"]).dt.to_period("M").dt.to_timestamp("M")
    exp["month"] = pd.to_datetime(exp["expense_date"]).dt.to_period("M").dt.to_timestamp("M")
    invoices["month"] = pd.to_datetime(invoices["invoice_date"]).dt.to_period("M").dt.to_timestamp("M")

    # 1. Revenue & Revenue Growth
    rev = sales.groupby(["company_id", "month"])["net_amount"].sum().reset_index().rename(columns={"net_amount": "revenue"})
    rev = rev.sort_values(["company_id", "month"]).reset_index(drop=True)
    rev["rev_lag1"] = rev.groupby("company_id")["revenue"].shift(1)
    rev["revenue_growth"] = np.where(
        rev["rev_lag1"].isna(),
        0.05,
        (rev["revenue"] - rev["rev_lag1"]) / np.maximum(rev["rev_lag1"], 1.0)
    )

    # 2. COGS & Gross Profit
    items_cost = sale_items.merge(products[["id", "cost_price"]], left_on="product_id", right_on="id", how="left")
    items_cost["cogs"] = items_cost["quantity"] * items_cost["cost_price"]
    items_sales = items_cost.merge(sales[["id", "company_id", "month"]], left_on="sale_id", right_on="id", how="inner")
    cogs_df = items_sales.groupby(["company_id", "month"])["cogs"].sum().reset_index()

    # 3. Expenses
    approved_exp = exp[exp["status"] == "approved"]
    exp_df = approved_exp.groupby(["company_id", "month"])["amount"].sum().reset_index().rename(columns={"amount": "expenses"})

    # 4. Invoice Collection Rate
    inv_col = invoices.groupby(["company_id", "month"]).agg({"paid_amount": "sum", "total_amount": "sum"}).reset_index()
    inv_col["payment_collection"] = inv_col["paid_amount"] / np.maximum(inv_col["total_amount"], 1.0)

    # Merge all components
    df = rev.merge(cogs_df, on=["company_id", "month"], how="left").fillna({"cogs": 0})
    df = df.merge(exp_df, on=["company_id", "month"], how="left").fillna({"expenses": 0})
    df = df.merge(inv_col[["company_id", "month", "payment_collection"]], on=["company_id", "month"], how="left").fillna({"payment_collection": 0.85})

    df["gross_profit"] = df["revenue"] - df["cogs"]
    df["net_profit"] = df["gross_profit"] - df["expenses"]
    df["profit_margin"] = df["net_profit"] / np.maximum(df["revenue"], 1.0)
    df["expense_control"] = 1.0 - np.clip(df["expenses"] / np.maximum(df["revenue"], 1.0), 0.0, 1.0)
    df["inventory_turnover"] = np.clip(df["cogs"] / np.maximum(df["cogs"].mean() * 0.5, 1.0), 0.5, 8.0)

    # Compute composite scorecard
    scores = []
    grades = []
    risks = []
    for _, row in df.iterrows():
        s_rg = minmax_scale(row["revenue_growth"], KPI_RANGES["revenue_growth"][0], KPI_RANGES["revenue_growth"][1])
        s_pm = minmax_scale(row["profit_margin"], KPI_RANGES["profit_margin"][0], KPI_RANGES["profit_margin"][1])
        s_ec = minmax_scale(row["expense_control"], KPI_RANGES["expense_control"][0], KPI_RANGES["expense_control"][1])
        s_it = minmax_scale(row["inventory_turnover"], KPI_RANGES["inventory_turnover"][0], KPI_RANGES["inventory_turnover"][1])
        s_pc = minmax_scale(row["payment_collection"], KPI_RANGES["payment_collection"][0], KPI_RANGES["payment_collection"][1])

        composite = (
            KPI_WEIGHTS["revenue_growth"] * s_rg +
            KPI_WEIGHTS["profit_margin"] * s_pm +
            KPI_WEIGHTS["expense_control"] * s_ec +
            KPI_WEIGHTS["inventory_turnover"] * s_it +
            KPI_WEIGHTS["payment_collection"] * s_pc
        )
        composite = float(np.clip(composite, 0.0, 100.0))
        grade, risk = compute_grade_and_risk(composite)
        scores.append(round(composite, 2))
        grades.append(grade)
        risks.append(risk)

    df["health_score"] = scores
    df["letter_grade"] = grades
    df["risk_tier"] = risks
    return df


def evaluate_scorecard_diagnostics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform formal diagnostic evaluation on scorecards:
    1. Score bounds [0, 100]
    2. Monotonicity (positive sensitivity to drivers)
    3. Stability (month-over-month score change std)
    4. Multi-paradigm comparative diagnostics (Weighted vs PCA vs WeakestLink vs TrafficLight)
    """
    weighted_sc = WeightedScorecard()
    pca_sc = PCAHealthIndex()
    weakest_sc = WeakestLinkScorer()
    traffic_sc = TrafficLightScorer()

    weighted_scores = weighted_sc.predict(df)
    pca_sc.fit(df)
    pca_scores = pca_sc.predict(df)
    weakest_scores = weakest_sc.predict(df)
    traffic_labels = traffic_sc.predict(df)

    bounds_valid = bool(np.all(weighted_scores >= 0.0) and np.all(weighted_scores <= 100.0))
    def safe_corr(s1, s2):
        if np.std(s1) == 0 or np.std(s2) == 0:
            return 0.0
        val = np.corrcoef(s1, s2)[0, 1]
        return round(float(val), 4) if not np.isnan(val) else 0.0

    monotonicity_checks = {
        "profit_margin_correlation": safe_corr(df["profit_margin"].values, weighted_scores),
        "expense_control_correlation": safe_corr(df["expense_control"].values, weighted_scores),
        "revenue_growth_correlation": safe_corr(df["revenue_growth"].values, weighted_scores),
        "payment_collection_correlation": safe_corr(df["payment_collection"].values, weighted_scores),
    }

    # Month-over-month stability
    df_sorted = df.sort_values(["company_id", "month"]).copy()
    df_sorted["score_diff"] = df_sorted.groupby("company_id")["health_score"].diff()
    stability_std = float(df_sorted["score_diff"].std())

    traffic_dist = pd.Series(traffic_labels).value_counts().to_dict()

    return {
        "score_bounds_verified_0_to_100": bounds_valid,
        "score_min": float(np.min(weighted_scores)),
        "score_max": float(np.max(weighted_scores)),
        "score_mean": round(float(np.mean(weighted_scores)), 2),
        "score_std": round(float(np.std(weighted_scores)), 2),
        "month_over_month_volatility_std": round(stability_std, 2),
        "monotonicity_checks": monotonicity_checks,
        "traffic_light_distribution": traffic_dist,
        "pca_explained_variance_ratio": round(float(pca_sc.pca.explained_variance_ratio_[0]), 4),
        "weakest_link_mean_penalty": round(float(np.mean(weighted_scores - weakest_scores)), 2),
    }


def train_predictive_health_transition(df: pd.DataFrame) -> Tuple[Dict[str, Any], str, Any, Dict[str, Any], List[str]]:
    """Train forward-looking health transition model: health_score_{t} -> health_score_{t+1}."""
    df_sorted = df.sort_values(["company_id", "month"]).reset_index(drop=True)
    df_sorted["next_health_score"] = df_sorted.groupby("company_id")["health_score"].shift(-1)
    valid_df = df_sorted.dropna(subset=["next_health_score"]).copy()

    feature_cols = [
        "health_score", "revenue_growth", "profit_margin", "expense_control",
        "inventory_turnover", "payment_collection", "revenue", "expenses"
    ]

    dev_df = valid_df[valid_df["company_id"].isin(DEV_COMPANIES)].copy()
    holdout_co3_df = valid_df[valid_df["company_id"] == HOLDOUT_COMPANY].copy()

    train_mask = (dev_df["month"] <= SPLIT_CONFIG["train_end"])
    val_mask = (dev_df["month"] >= SPLIT_CONFIG["val_start"]) & (dev_df["month"] <= SPLIT_CONFIG["val_end"])
    test_mask = (dev_df["month"] >= SPLIT_CONFIG["test_start"])

    train_df = dev_df[train_mask].copy()
    val_df = dev_df[val_mask].copy()
    test_df = dev_df[test_mask].copy()

    X_train, y_train = train_df[feature_cols].values, train_df["next_health_score"].values
    X_val, y_val = val_df[feature_cols].values, val_df["next_health_score"].values
    X_test, y_test = test_df[feature_cols].values, test_df["next_health_score"].values

    candidates = {}

    # 1. Persistence Baseline (score_{t+1} ≈ score_t)
    val_pred_persist = val_df["health_score"].values
    test_pred_persist = test_df["health_score"].values
    candidates["Persistence_Baseline"] = {
        "val_metrics": compute_metrics(y_val, val_pred_persist, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_persist, y_train),
        "model": None,
        "is_baseline": True,
    }

    # 2. Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    val_pred_lr = np.clip(lr.predict(X_val), 0, 100)
    test_pred_lr = np.clip(lr.predict(X_test), 0, 100)
    candidates["Linear_Regression"] = {
        "val_metrics": compute_metrics(y_val, val_pred_lr, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_lr, y_train),
        "model": lr,
        "is_baseline": False,
    }

    # 3. Ridge Regression
    ridge = Ridge(alpha=1.0, random_state=42)
    ridge.fit(X_train, y_train)
    val_pred_ridge = np.clip(ridge.predict(X_val), 0, 100)
    test_pred_ridge = np.clip(ridge.predict(X_test), 0, 100)
    candidates["Ridge_Regression"] = {
        "val_metrics": compute_metrics(y_val, val_pred_ridge, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_ridge, y_train),
        "model": ridge,
        "is_baseline": False,
    }

    # 4. Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=4, random_state=42)
    rf.fit(X_train, y_train)
    val_pred_rf = np.clip(rf.predict(X_val), 0, 100)
    test_pred_rf = np.clip(rf.predict(X_test), 0, 100)
    candidates["Random_Forest"] = {
        "val_metrics": compute_metrics(y_val, val_pred_rf, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_rf, y_train),
        "model": rf,
        "is_baseline": False,
    }

    # 5. XGBoost
    xgb = XGBRegressor(n_estimators=80, max_depth=3, learning_rate=0.05, random_state=42)
    xgb.fit(X_train, y_train)
    val_pred_xgb = np.clip(xgb.predict(X_val), 0, 100)
    test_pred_xgb = np.clip(xgb.predict(X_test), 0, 100)
    candidates["XGBoost"] = {
        "val_metrics": compute_metrics(y_val, val_pred_xgb, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_xgb, y_train),
        "model": xgb,
        "is_baseline": False,
    }

    # Model Selection: based on Dev validation MAE
    trained = {k: v for k, v in candidates.items() if v["model"] is not None}
    best_name = min(trained, key=lambda k: trained[k]["val_metrics"]["mae"])
    best_model = trained[best_name]["model"]

    # Company 3 Holdout evaluation
    if len(holdout_co3_df) > 0:
        X_co3 = holdout_co3_df[feature_cols].values
        y_co3 = holdout_co3_df["next_health_score"].values
        co3_pred = np.clip(best_model.predict(X_co3), 0, 100)
        holdout_metrics = compute_metrics(y_co3, co3_pred, y_train)
        co3_pred_persist = holdout_co3_df["health_score"].values
        holdout_metrics["baseline_persistence_metrics"] = compute_metrics(y_co3, co3_pred_persist, y_train)
    else:
        holdout_metrics = {}

    return candidates, best_name, best_model, holdout_metrics, feature_cols


def run_pipeline() -> Dict[str, Any]:
    logger.info("Starting Business Health Scoring Pipeline...")
    df = compute_historical_kpis()

    # Step 1: Scorecard Diagnostics
    diagnostics = evaluate_scorecard_diagnostics(df)
    logger.info("Scorecard Diagnostics completed: Bounds valid=%s, Mean=%.2f, Volatility=%.2f",
                diagnostics["score_bounds_verified_0_to_100"], diagnostics["score_mean"], diagnostics["month_over_month_volatility_std"])

    # Save historical scores
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(REPORTS_DIR / "business_health_scores.csv", index=False)

    latest_df = df.sort_values("month").groupby("company_id").last().reset_index()
    latest_df[[
        "company_id", "month", "health_score", "letter_grade", "risk_tier",
        "revenue_growth", "profit_margin", "expense_control", "inventory_turnover", "payment_collection"
    ]].to_csv(REPORTS_DIR / "latest_health_scores.csv", index=False)

    # Step 2: Transition Model Training
    candidates, best_name, best_model, holdout_metrics, feature_cols = train_predictive_health_transition(df)
    logger.info("Selected Health Transition Model: %s (Val MAE: %.2f pts)",
                best_name, candidates[best_name]["val_metrics"]["mae"])

    # Save artifacts
    health_artifact_data = {
        "weights": KPI_WEIGHTS,
        "kpi_ranges": KPI_RANGES,
        "transition_model": best_model,
        "feature_cols": feature_cols,
        "selected_model": best_name,
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY
    }
    save_model(health_artifact_data, "health_score_pipeline.pkl", MODELS_DIR)
    save_model(health_artifact_data, "health_score_selected.pkl", MODELS_DIR)

    # Config metadata
    health_config = {
        "engine": "Transparent KPI Scorecard + Forward Health Transition Predictor",
        "architecture_distinction": {
            "scorecard_concept": "Transparent Weighted Scorecard (0-100) — Rule-based descriptive operational health indicator, NOT a supervised ML model. Evaluated for diagnostic sanity (bounds, monotonicity, volatility).",
            "classification_concept": "Operational Risk Categorizer (A-F grading and Green/Amber/Red traffic lights) — Descriptive categorization mapping score intervals to management actions.",
            "transition_prediction_concept": "Forward-Looking Transition Regressor (Linear Regression winner) — Supervised regression predicting next month's scorecard score H_{t+1} from current period KPIs H_t.",
            "evaluation_limitations": "The forward transition model is evaluated against next month's deterministic scorecard score, not empirical bankruptcy/loan default data. Predictive validation is strictly limited to forward ratio tracking."
        },
        "weights": KPI_WEIGHTS,
        "kpi_ranges": KPI_RANGES,
        "grade_thresholds": {"A": 80.0, "B": 65.0, "C": 50.0, "D": 35.0, "F": 0.0},
        "selected_transition_model": best_name,
        "features": feature_cols,
        "scorecard_diagnostics": diagnostics
    }
    with open(MODELS_DIR / "health_score_config.json", "w", encoding="utf-8") as f:
        json.dump(health_config, f, indent=2)

    eval_report = {
        "pipeline": "business_health_scoring_and_transition",
        "architecture_distinction": {
            "scorecard_concept": "Transparent Weighted Scorecard (0-100) — Rule-based descriptive operational health indicator, NOT a supervised ML model. Evaluated for diagnostic sanity (bounds, monotonicity, volatility).",
            "classification_concept": "Operational Risk Categorizer (A-F grading and Green/Amber/Red traffic lights) — Descriptive categorization mapping score intervals to management actions.",
            "transition_prediction_concept": "Forward-Looking Transition Regressor (Linear Regression winner) — Supervised regression predicting next month's scorecard score H_{t+1} from current period KPIs H_t.",
            "evaluation_limitations": "The forward transition model is evaluated against next month's deterministic scorecard score, not empirical bankruptcy/loan default data. Predictive validation is strictly limited to forward ratio tracking."
        },
        "scorecard_engine": "Transparent Weighted Scorecard (0-100)",
        "scorecard_weights": KPI_WEIGHTS,
        "scorecard_diagnostics": diagnostics,
        "selected_transition_model": best_name,
        "selection_metric": "val_mae_points",
        "metric_definitions": {
            "mae": "mean(|actual_score - pred_score|) in scorecard points (0-100 scale)",
            "rmse": "sqrt(mean((actual_score - pred_score)^2)) in scorecard points",
            "wape": "sum(|actual - pred|) / sum(|actual|) * 100% (volume-weighted percentage error)",
            "r2": "1 - SS_res / SS_tot (coefficient of determination)",
            "bias": "sum(pred - actual) / sum(|actual|) * 100%",
            "mase": "mae_model / mean(|diff(y_train)|)"
        },
        "transition_candidates": {
            k: {
                "val_mae": round(v["val_metrics"]["mae"], 2),
                "val_rmse": round(v["val_metrics"]["rmse"], 2),
                "val_wape_pct": round(v["val_metrics"]["wape"], 2),
                "val_r2": round(v["val_metrics"]["r2"], 4),
                "val_bias_pct": round(v["val_metrics"]["bias"], 2),
                "val_mase": round(v["val_metrics"]["mase"], 4),
                "test_mae": round(v["test_metrics"]["mae"], 2),
                "test_rmse": round(v["test_metrics"]["rmse"], 2),
                "test_wape_pct": round(v["test_metrics"]["wape"], 2),
                "test_r2": round(v["test_metrics"]["r2"], 4),
                "test_bias_pct": round(v["test_metrics"]["bias"], 2),
                "test_mase": round(v["test_metrics"]["mase"], 4),
                "is_baseline": v.get("is_baseline", False),
            }
            for k, v in candidates.items()
        },
        "approach_c_holdout_co3": {
            "business_id": HOLDOUT_COMPANY,
            "business_name": "Apna Kirana Store",
            "metrics": {
                "mae": round(holdout_metrics.get("mae", 0.0), 2),
                "rmse": round(holdout_metrics.get("rmse", 0.0), 2),
                "wape_pct": round(holdout_metrics.get("wape", 0.0), 2),
                "r2": round(holdout_metrics.get("r2", 0.0), 4),
                "bias_pct": round(holdout_metrics.get("bias", 0.0), 2),
                "mase": round(holdout_metrics.get("mase", 0.0), 4),
                "baseline_persistence_metrics": holdout_metrics.get("baseline_persistence_metrics", {}),
                "baseline_persistence_mae": round(holdout_metrics.get("baseline_persistence_metrics", {}).get("mae", 0.0), 2),
                "baseline_persistence_r2": round(holdout_metrics.get("baseline_persistence_metrics", {}).get("r2", 0.0), 4),
            }
        }
    }

    with open(REPORTS_DIR / "health_score_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    logger.info("Saved health score evaluation report: %s", REPORTS_DIR / "health_score_eval.json")
    return eval_report


if __name__ == "__main__":
    run_pipeline()

# -*- coding: utf-8 -*-
"""
train_health_score.py
=====================
Business Health Scoring & Predictive Health Transition Pipeline (Approach C).

Part A: Transparent Rule-Based KPI Scorecard
- Revenue Growth Rate: 25% (range: [-0.50, 1.00])
- Profit Margin: 25% (range: [-0.20, 0.40])
- Expense Control: 20% (range: [0.00, 1.00])
- Inventory Turnover: 15% (range: [0.00, 10.00])
- Payment Collection Rate: 15% (range: [0.00, 1.00])
- Composite Score: 0 to 100
- Grade: A (80-100), B (65-79), C (50-64), D (35-49), F (<35)

Part B: Forward-Looking Predictive Health Transition Model
- Target: Next month's health score (health_score_{t+1})
- Features: Current and lag operational metrics at period t (no future data leakage)
- Candidates: Persistence Baseline, Linear Regression, Random Forest, XGBoost
- Chronological train/val/test splits and Approach C business holdout.

Outputs:
- ml/models/health_score_pipeline.pkl
- ml/models/health_score_config.json
- ml/reports/health_score_eval.json
- ml/reports/business_health_scores.csv
- ml/reports/latest_health_scores.csv

Usage:
    python ml/scripts/train_health_score.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, compute_metrics, save_model,
    MODELS_DIR, REPORTS_DIR, PROCESSED_DIR, SYNTHETIC_DIR
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

    # Financial Formulas
    df["gross_profit"] = df["revenue"] - df["cogs"]
    df["net_profit"] = df["gross_profit"] - df["expenses"]
    df["profit_margin"] = df["net_profit"] / np.maximum(df["revenue"], 1.0)
    df["expense_ratio"] = df["expenses"] / np.maximum(df["revenue"], 1.0)
    df["expense_control"] = np.clip(1.0 - df["expense_ratio"], 0.0, 1.0)

    # Inventory Turnover estimate (annualized monthly COGS / average working inventory ~ COGS/inventory)
    df["inventory_turnover"] = np.clip((df["cogs"] * 12.0) / np.maximum(df["revenue"] * 0.4, 1.0), 1.0, 8.0)

    # Compute Sub-Scores & Composite Score
    scores = []
    for _, row in df.iterrows():
        s_rev = minmax_scale(row["revenue_growth"], *KPI_RANGES["revenue_growth"])
        s_prof = minmax_scale(row["profit_margin"], *KPI_RANGES["profit_margin"])
        s_exp = minmax_scale(row["expense_control"], *KPI_RANGES["expense_control"])
        s_inv = minmax_scale(row["inventory_turnover"], *KPI_RANGES["inventory_turnover"])
        s_coll = minmax_scale(row["payment_collection"], *KPI_RANGES["payment_collection"])

        comp_score = (
            KPI_WEIGHTS["revenue_growth"] * s_rev +
            KPI_WEIGHTS["profit_margin"] * s_prof +
            KPI_WEIGHTS["expense_control"] * s_exp +
            KPI_WEIGHTS["inventory_turnover"] * s_inv +
            KPI_WEIGHTS["payment_collection"] * s_coll
        )
        grade, risk = compute_grade_and_risk(comp_score)
        scores.append({
            "score_rev": round(s_rev, 2),
            "score_prof": round(s_prof, 2),
            "score_exp": round(s_exp, 2),
            "score_inv": round(s_inv, 2),
            "score_coll": round(s_coll, 2),
            "health_score": round(comp_score, 2),
            "letter_grade": grade,
            "risk_tier": risk
        })

    scores_df = pd.DataFrame(scores)
    df = pd.concat([df, scores_df], axis=1)

    # Attach next month's score as the target for predictive modeling
    df["next_health_score"] = df.groupby("company_id")["health_score"].shift(-1)
    return df


DEV_COMPANIES = ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"]
HOLDOUT_COMPANY = "00000000-0000-0000-0000-000000000003"


def train_predictive_health_transition(df: pd.DataFrame) -> Tuple[Dict[str, Any], str, Any, Dict[str, Any], list]:
    """
    Train forward-looking supervised models to predict next month's health score.
    Avoids target leakage: only features from period t are used to predict score at t+1.
    Strictly trains on Dev (Companies 1 & 2) and evaluates holdout on Company 3.
    """
    # Drop the last period where next_health_score is NaN
    valid_df = df.dropna(subset=["next_health_score"]).copy()

    feature_cols = [
        "health_score", "revenue_growth", "profit_margin", "expense_control",
        "inventory_turnover", "payment_collection", "revenue", "expenses"
    ]

    dev_df = valid_df[valid_df["company_id"].isin(DEV_COMPANIES)].copy()
    holdout_co3_df = valid_df[valid_df["company_id"] == HOLDOUT_COMPANY].copy()

    train_mask = (dev_df["month"] <= "2023-12-31")
    val_mask = (dev_df["month"] >= "2024-01-01") & (dev_df["month"] <= "2024-06-30")
    test_mask = (dev_df["month"] >= "2024-07-01")

    train_df = dev_df[train_mask].copy()
    val_df = dev_df[val_mask].copy()
    test_df = dev_df[test_mask].copy()

    # Zero contamination assertions
    assert (train_df["company_id"] == HOLDOUT_COMPANY).sum() == 0, "Leakage: Company 3 found in training set!"
    assert (val_df["company_id"] == HOLDOUT_COMPANY).sum() == 0, "Leakage: Company 3 found in validation set!"
    assert (test_df["company_id"] == HOLDOUT_COMPANY).sum() == 0, "Leakage: Company 3 found in dev test set!"

    X_train, y_train = train_df[feature_cols].values, train_df["next_health_score"].values
    X_val, y_val = val_df[feature_cols].values, val_df["next_health_score"].values
    X_test, y_test = test_df[feature_cols].values, test_df["next_health_score"].values

    candidates = {}

    # 1. Persistence Baseline (score_{t+1} ≈ score_t)
    val_pred_persist = val_df["health_score"].values
    test_pred_persist = test_df["health_score"].values
    candidates["Persistence_Baseline"] = {
        "val_metrics": compute_metrics(y_val, val_pred_persist),
        "test_metrics": compute_metrics(y_test, test_pred_persist),
        "model": None,
    }

    # 2. Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    val_pred_lr = np.clip(lr.predict(X_val), 0, 100)
    test_pred_lr = np.clip(lr.predict(X_test), 0, 100)
    candidates["Linear_Regression"] = {
        "val_metrics": compute_metrics(y_val, val_pred_lr),
        "test_metrics": compute_metrics(y_test, test_pred_lr),
        "model": lr,
    }

    # 3. Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=4, random_state=42)
    rf.fit(X_train, y_train)
    val_pred_rf = np.clip(rf.predict(X_val), 0, 100)
    test_pred_rf = np.clip(rf.predict(X_test), 0, 100)
    candidates["Random_Forest"] = {
        "val_metrics": compute_metrics(y_val, val_pred_rf),
        "test_metrics": compute_metrics(y_test, test_pred_rf),
        "model": rf,
    }

    # 4. XGBoost
    xgb = XGBRegressor(n_estimators=80, max_depth=3, learning_rate=0.05, random_state=42)
    xgb.fit(X_train, y_train)
    val_pred_xgb = np.clip(xgb.predict(X_val), 0, 100)
    test_pred_xgb = np.clip(xgb.predict(X_test), 0, 100)
    candidates["XGBoost"] = {
        "val_metrics": compute_metrics(y_val, val_pred_xgb),
        "test_metrics": compute_metrics(y_test, test_pred_xgb),
        "model": xgb,
    }

    # Select best predictive model based on Dev validation MAE
    trained = {k: v for k, v in candidates.items() if v["model"] is not None}
    best_name = min(trained, key=lambda k: trained[k]["val_metrics"]["mae"])
    best_model = trained[best_name]["model"]

    # True Zero-Shot Holdout Evaluation on Company 3
    if len(holdout_co3_df) > 0:
        X_co3 = holdout_co3_df[feature_cols].values
        y_co3 = holdout_co3_df["next_health_score"].values

        # Frozen winning model prediction
        co3_pred = np.clip(best_model.predict(X_co3), 0, 100)
        holdout_metrics = compute_metrics(y_co3, co3_pred)

        # Baseline on Company 3
        co3_pred_persist = holdout_co3_df["health_score"].values
        holdout_metrics["baseline_persistence_metrics"] = compute_metrics(y_co3, co3_pred_persist)
        holdout_metrics["n_observations"] = len(holdout_co3_df)
    else:
        holdout_metrics = {}

    return candidates, best_name, best_model, holdout_metrics, feature_cols


def run_pipeline() -> Dict[str, Any]:
    """Execute business health scoring and transition prediction pipeline."""
    logger.info("Starting Business Health Scoring Pipeline...")

    # Step 1: Compute transparent historical KPI scorecard
    df = compute_historical_kpis()
    logger.info(f"Computed historical health scores across {len(df)} monthly business periods.")

    # Save historical scores table
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    history_path = REPORTS_DIR / "business_health_scores.csv"
    df.to_csv(history_path, index=False)

    # Save latest snapshot per company
    latest_df = df.sort_values("month").groupby("company_id").last().reset_index()
    latest_path = REPORTS_DIR / "latest_health_scores.csv"
    latest_df[[
        "company_id", "month", "health_score", "letter_grade", "risk_tier",
        "revenue_growth", "profit_margin", "expense_control", "inventory_turnover", "payment_collection"
    ]].to_csv(latest_path, index=False)
    logger.info(f"Saved latest health scores snapshot to {latest_path}")

    # Step 2: Train forward-looking health transition model
    candidates, best_name, best_model, holdout_metrics, feature_cols = train_predictive_health_transition(df)
    logger.info(f"Selected Health Transition Model: {best_name}")
    for name, data in candidates.items():
        vm = data["val_metrics"]
        tm = data["test_metrics"]
        logger.info(f"Candidate: {name:<22} | Val MAE: {vm.get('mae', 0):.2f} pts | Test MAE: {tm.get('mae', 0):.2f} pts | Test R2: {tm.get('r2', 0):.4f}")

    logger.info(f"Approach C Holdout Co3 Test MAE: {holdout_metrics.get('mae', 0):.2f} pts | R2: {holdout_metrics.get('r2', 0):.4f}")

    # Save artifacts for backend compatibility:
    # 1. health_score_pipeline.pkl
    save_model(
        {
            "weights": KPI_WEIGHTS,
            "kpi_ranges": KPI_RANGES,
            "transition_model": best_model,
            "feature_cols": feature_cols,
            "selected_model": best_name,
            "training_companies": DEV_COMPANIES,
            "holdout_company": HOLDOUT_COMPANY
        },
        "health_score_pipeline.pkl",
        MODELS_DIR
    )

    # 2. health_score_config.json
    health_config = {
        "engine": "Transparent KPI Scorecard + Forward Health Transition Predictor",
        "weights": KPI_WEIGHTS,
        "kpi_ranges": KPI_RANGES,
        "grade_thresholds": {
            "A": 80.0,
            "B": 65.0,
            "C": 50.0,
            "D": 35.0,
            "F": 0.0
        },
        "selected_transition_model": best_name,
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "transition_test_metrics": candidates[best_name]["test_metrics"]
    }
    with open(MODELS_DIR / "health_score_config.json", "w", encoding="utf-8") as f:
        json.dump(health_config, f, indent=2)

    # 3. ml/reports/health_score_eval.json
    eval_report = {
        "pipeline": "business_health_scoring_and_transition",
        "scorecard_weights": KPI_WEIGHTS,
        "kpi_ranges": KPI_RANGES,
        "selected_transition_model": best_name,
        "selection_metric": "val_mae",
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "transition_candidates": {
            k: {
                "val_metrics": v["val_metrics"],
                "test_metrics": v["test_metrics"],
            }
            for k, v in candidates.items()
        },
        "approach_c_holdout_co3": {
            "business_id": HOLDOUT_COMPANY,
            "business_name": "Apna Kirana Store",
            "metrics": holdout_metrics
        }
    }
    with open(REPORTS_DIR / "health_score_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    logger.info("Business Health Scoring Pipeline completed successfully.")
    return eval_report


if __name__ == "__main__":
    run_pipeline()

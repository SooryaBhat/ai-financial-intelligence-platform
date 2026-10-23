# -*- coding: utf-8 -*-
"""
train_profit.py
===============
Train, compare, and evaluate net profit prediction models (Approach C).

Financial Definition:
1. Gross Revenue = sum(sales.net_amount)
2. Cost of Goods Sold (COGS) = sum(sale_items.quantity * products.cost_price)
3. Gross Profit = Gross Revenue - COGS
4. Operating Expenses = sum(expenses.amount)
5. Net Profit (Target) = Gross Profit - Operating Expenses
6. Profit Margin % = (Net Profit / Gross Revenue) * 100

Candidate models:
- Mean Baseline
- Historical Baseline (profit_lag1)
- Linear Regression
- Random Forest Regressor
- XGBoost Regressor
- LightGBM Regressor

Features:
- profit_lag1, profit_lag2, profit_lag3, profit_lag6,
  profit_roll3, profit_roll6,
  revenue_lag1, revenue_lag2, revenue_lag3,
  expense_ratio_lag1, expense_ratio_lag2,
  month_num, quarter, year, is_q4

Approach C Business Holdout:
- Train shared model on Companies 1 & 2, evaluate holdout generalization on Company 3 (Apna Kirana).

Saves artifacts:
- ml/models/profit_prediction_xgboost.pkl
- ml/models/profit_feature_meta.json
- ml/reports/profit_prediction_eval.json
- ml/reports/profit_summary.csv

Usage:
    python ml/scripts/train_profit.py
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
from lightgbm import LGBMRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, compute_metrics, save_model,
    MODELS_DIR, REPORTS_DIR, PROCESSED_DIR, SYNTHETIC_DIR
)

logger = get_logger(__name__)

FEATURE_COLS = [
    "profit_lag1", "profit_lag2", "profit_lag3", "profit_lag6",
    "profit_roll3", "profit_roll6",
    "revenue_lag1", "revenue_lag2", "revenue_lag3",
    "expense_ratio_lag1", "expense_ratio_lag2",
    "month_num", "quarter", "year", "is_q4"
]


DEV_COMPANIES = ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"]
HOLDOUT_COMPANY = "00000000-0000-0000-0000-000000000003"


def load_and_split_profit_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load profit features and split strictly: Dev (Companies 1 & 2) vs Holdout (Company 3)."""
    df = load_csv("profit_features.csv", PROCESSED_DIR)
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values(["company_id", "month"]).reset_index(drop=True)

    # Dev businesses: strictly Companies 1 & 2
    dev_df = df[df["company_id"].isin(DEV_COMPANIES)].copy()

    # Chronological splits within Dev
    train_mask = (dev_df["month"] <= "2023-12-31")
    val_mask = (dev_df["month"] >= "2024-01-01") & (dev_df["month"] <= "2024-06-30")
    test_mask = (dev_df["month"] >= "2024-07-01")

    train_df = dev_df[train_mask].copy()
    val_df = dev_df[val_mask].copy()
    test_df = dev_df[test_mask].copy()

    # Company 3 holdout
    holdout_co3_df = df[df["company_id"] == HOLDOUT_COMPANY].copy()

    # Zero leakage assertions
    assert (train_df["company_id"] == HOLDOUT_COMPANY).sum() == 0, "Leakage: Company 3 found in training set!"
    assert (val_df["company_id"] == HOLDOUT_COMPANY).sum() == 0, "Leakage: Company 3 found in validation set!"
    assert (test_df["company_id"] == HOLDOUT_COMPANY).sum() == 0, "Leakage: Company 3 found in dev test set!"

    return train_df, val_df, test_df, holdout_co3_df


def train_and_evaluate_candidates(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    holdout_co3_df: pd.DataFrame,
) -> Tuple[Dict[str, Any], str, Any, Dict[str, Any], Any]:
    """Train candidates for profit prediction strictly on Dev and evaluate on Holdout."""
    X_train, y_train = train_df[FEATURE_COLS].values, train_df["net_profit"].values
    X_val, y_val = val_df[FEATURE_COLS].values, val_df["net_profit"].values
    X_test, y_test = test_df[FEATURE_COLS].values, test_df["net_profit"].values

    candidates = {}

    # 1. Historical Baseline (Lag 1)
    val_pred_lag1 = val_df["profit_lag1"].values
    test_pred_lag1 = test_df["profit_lag1"].values
    candidates["Historical_Baseline"] = {
        "val_metrics": compute_metrics(y_val, val_pred_lag1),
        "test_metrics": compute_metrics(y_test, test_pred_lag1),
        "model": None,
    }

    # 2. Mean Baseline
    mean_val = float(np.mean(y_train))
    val_pred_mean = np.full_like(y_val, mean_val)
    test_pred_mean = np.full_like(y_test, mean_val)
    candidates["Mean_Baseline"] = {
        "val_metrics": compute_metrics(y_val, val_pred_mean),
        "test_metrics": compute_metrics(y_test, test_pred_mean),
        "model": None,
    }

    # 3. Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    val_pred_lr = lr.predict(X_val)
    test_pred_lr = lr.predict(X_test)
    candidates["Linear_Regression"] = {
        "val_metrics": compute_metrics(y_val, val_pred_lr),
        "test_metrics": compute_metrics(y_test, test_pred_lr),
        "model": lr,
    }

    # 4. Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X_train, y_train)
    val_pred_rf = rf.predict(X_val)
    test_pred_rf = rf.predict(X_test)
    candidates["Random_Forest"] = {
        "val_metrics": compute_metrics(y_val, val_pred_rf),
        "test_metrics": compute_metrics(y_test, test_pred_rf),
        "model": rf,
    }

    # 5. XGBoost
    xgb = XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    xgb.fit(X_train, y_train)
    val_pred_xgb = xgb.predict(X_val)
    test_pred_xgb = xgb.predict(X_test)
    candidates["XGBoost"] = {
        "val_metrics": compute_metrics(y_val, val_pred_xgb),
        "test_metrics": compute_metrics(y_test, test_pred_xgb),
        "model": xgb,
    }

    # 6. LightGBM
    lgb = LGBMRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
        verbose=-1
    )
    lgb.fit(X_train, y_train)
    val_pred_lgb = lgb.predict(X_val)
    test_pred_lgb = lgb.predict(X_test)
    candidates["LightGBM"] = {
        "val_metrics": compute_metrics(y_val, val_pred_lgb),
        "test_metrics": compute_metrics(y_test, test_pred_lgb),
        "model": lgb,
    }

    # Model Selection: Strictly based on Dev validation WAPE
    trained_models = {k: v for k, v in candidates.items() if v["model"] is not None}
    best_name = min(trained_models, key=lambda k: trained_models[k]["val_metrics"]["wape"])
    best_model = trained_models[best_name]["model"]

    # True Zero-Shot Evaluation on Holdout Company 3
    if len(holdout_co3_df) > 0:
        X_co3 = holdout_co3_df[FEATURE_COLS].values
        y_co3 = holdout_co3_df["net_profit"].values

        # Frozen winning model prediction
        co3_pred = best_model.predict(X_co3)
        holdout_metrics = compute_metrics(y_co3, co3_pred)

        # Baselines on Company 3
        co3_pred_lag1 = holdout_co3_df["profit_lag1"].values
        co3_pred_mean = np.full_like(y_co3, mean_val)
        holdout_metrics["baseline_lag1_metrics"] = compute_metrics(y_co3, co3_pred_lag1)
        holdout_metrics["baseline_mean_metrics"] = compute_metrics(y_co3, co3_pred_mean)
        holdout_metrics["n_observations"] = len(holdout_co3_df)
    else:
        holdout_metrics = {}

    models_dict = {
        "rf": rf,
        "xgb": xgb,
        "lr": lr,
        "lgb": lgb
    }

    return candidates, best_name, best_model, holdout_metrics, models_dict


def generate_profit_summary(df: pd.DataFrame, model: Any) -> pd.DataFrame:
    """Generate comprehensive monthly profit summary with financial decomposition."""
    summary_df = df[["company_id", "month", "net_profit"]].copy()
    summary_df["predicted_net_profit"] = model.predict(df[FEATURE_COLS].values)
    summary_df["variance"] = summary_df["predicted_net_profit"] - summary_df["net_profit"]
    summary_df["pct_variance"] = np.round((summary_df["variance"] / np.abs(summary_df["net_profit"] + 1e-6)) * 100, 2)
    return summary_df


def run_pipeline() -> Dict[str, Any]:
    """Execute profit prediction pipeline."""
    logger.info("Starting Profit Prediction Pipeline...")

    train_df, val_df, test_df, holdout_co3_df = load_and_split_profit_data()
    logger.info(f"Profit splits - Train: {train_df.shape}, Val: {val_df.shape}, Test: {test_df.shape}, Holdout Co3: {holdout_co3_df.shape}")

    candidates, best_name, best_model, holdout_metrics, models_dict = train_and_evaluate_candidates(
        train_df, val_df, test_df, holdout_co3_df
    )

    logger.info(f"Selected Profit Model: {best_name}")
    for name, data in candidates.items():
        vm = data["val_metrics"]
        tm = data["test_metrics"]
        logger.info(f"Candidate: {name:<22} | Val WAPE: {vm.get('wape', 0):.2f}% | Test WAPE: {tm.get('wape', 0):.2f}% | Test R2: {tm.get('r2', 0):.4f}")

    logger.info(f"Approach C Holdout Co3 WAPE: {holdout_metrics.get('wape', 0):.2f}% | R2: {holdout_metrics.get('r2', 0):.4f}")

    # Generate and save profit summary
    all_df = pd.concat([train_df, val_df, test_df]).sort_values(["company_id", "month"]).reset_index(drop=True)
    profit_summary = generate_profit_summary(all_df, best_model)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = REPORTS_DIR / "profit_summary.csv"
    profit_summary.to_csv(summary_path, index=False)
    logger.info(f"Saved profit summary to {summary_path}")

    # Save artifacts with true algorithm identities:
    # 1. Genuine Random Forest artifact
    save_model(
        {"model": models_dict["rf"], "feature_cols": FEATURE_COLS, "algorithm": "RandomForestRegressor"},
        "profit_prediction_random_forest.pkl",
        MODELS_DIR
    )

    # 2. Genuine XGBoost artifact (strictly contains actual XGBRegressor)
    save_model(
        {"model": models_dict["xgb"], "feature_cols": FEATURE_COLS, "algorithm": "XGBRegressor"},
        "profit_prediction_xgboost.pkl",
        MODELS_DIR
    )

    # 3. Genuine Linear Regression artifact
    save_model(
        {"model": models_dict["lr"], "feature_cols": FEATURE_COLS, "algorithm": "LinearRegression"},
        "profit_prediction_linear_regression.pkl",
        MODELS_DIR
    )

    # 4. Canonical Selected Model artifact (winner)
    save_model(
        {
            "model": best_model,
            "feature_cols": FEATURE_COLS,
            "algorithm": best_name,
            "selection_metric": "val_wape",
            "val_wape": candidates[best_name]["val_metrics"]["wape"],
            "test_wape": candidates[best_name]["test_metrics"]["wape"],
            "training_companies": DEV_COMPANIES,
            "holdout_company": HOLDOUT_COMPANY
        },
        "profit_prediction_selected.pkl",
        MODELS_DIR
    )

    # 5. Metadata
    feature_meta = {
        "pipeline": "profit_prediction",
        "target": "net_profit",
        "financial_definition": "Gross Revenue - COGS - Operating Expenses",
        "horizon": "1 month ahead",
        "features": FEATURE_COLS,
        "selected_model": best_name,
        "selected_artifact": "profit_prediction_selected.pkl",
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "algorithm_artifacts": {
            "random_forest": "profit_prediction_random_forest.pkl",
            "xgboost": "profit_prediction_xgboost.pkl",
            "linear_regression": "profit_prediction_linear_regression.pkl"
        },
        "test_metrics": candidates[best_name]["test_metrics"],
        "approach_c_holdout_co3_metrics": holdout_metrics
    }
    with open(MODELS_DIR / "profit_feature_meta.json", "w", encoding="utf-8") as f:
        json.dump(feature_meta, f, indent=2)

    # 3. ml/reports/profit_prediction_eval.json
    eval_report = {
        "pipeline": "profit_prediction",
        "financial_definition": "Gross Revenue - COGS - Operating Expenses",
        "selected_model": best_name,
        "selection_metric": "val_wape",
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "features": FEATURE_COLS,
        "candidates": {
            k: {
                "val_metrics": v["val_metrics"],
                "test_metrics": v["test_metrics"],
            }
            for k, v in candidates.items()
        },
        "approach_c_holdout_co3": {
            "business_id": "00000000-0000-0000-0000-000000000003",
            "business_name": "Apna Kirana Store",
            "metrics": holdout_metrics
        }
    }
    with open(REPORTS_DIR / "profit_prediction_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    logger.info("Profit Prediction Pipeline completed successfully.")
    return eval_report


if __name__ == "__main__":
    run_pipeline()

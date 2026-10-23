# -*- coding: utf-8 -*-
"""
train_expenses.py
=================
Train, compare, and evaluate operating expense forecasting models (Approach C).

Target: Monthly operating expense (total_expense) per category.
Candidate models:
- Naive Baseline (Lag 1)
- Seasonal-Naive Baseline (Lag 6 / Historical mean)
- Linear Regression
- XGBoost Regressor
- LightGBM Regressor
- SARIMA (for aggregate operational expenses)

Features:
- lag_1, lag_2, lag_3, lag_6,
  roll3_mean, roll6_mean, roll3_std,
  txn_count, avg_expense,
  month_num, quarter, year, is_q4, is_q1

Approach C Business Holdout:
- Train shared model on Companies 1 & 2, evaluate holdout generalization on Company 3 (Apna Kirana).

Outputs:
- ml/models/expense_prediction_xgboost.pkl
- ml/models/expense_prediction_linear_regression.pkl
- ml/models/expense_feature_meta.json
- ml/reports/expense_prediction_eval.json
- ml/reports/expense_variance_by_category.csv

Usage:
    python ml/scripts/train_expenses.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, compute_metrics, save_model,
    MODELS_DIR, REPORTS_DIR, PROCESSED_DIR
)

logger = get_logger(__name__)

FEATURE_COLS = [
    "lag_1", "lag_2", "lag_3", "lag_6",
    "roll3_mean", "roll6_mean", "roll3_std",
    "txn_count_lag1", "avg_expense_lag1",
    "month_num", "quarter", "year", "is_q4", "is_q1"
]


DEV_COMPANIES = ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"]
HOLDOUT_COMPANY = "00000000-0000-0000-0000-000000000003"


def load_and_split_expense_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load expense features and split strictly: Dev (Companies 1 & 2) vs Holdout (Company 3)."""
    df = load_csv("expense_features.csv", PROCESSED_DIR)
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values(["company_id", "category", "month"]).reset_index(drop=True)

    # Dev businesses: strictly Companies 1 & 2
    dev_df = df[df["company_id"].isin(DEV_COMPANIES)].copy()

    # Chronological splits within Dev (2022-07 to 2024-12)
    train_mask = (dev_df["month"] <= "2023-12-31")
    val_mask = (dev_df["month"] >= "2024-01-01") & (dev_df["month"] <= "2024-06-30")
    test_mask = (dev_df["month"] >= "2024-07-01")

    train_df = dev_df[train_mask].copy()
    val_df = dev_df[val_mask].copy()
    test_df = dev_df[test_mask].copy()

    # Company 3 holdout (Apna Kirana)
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
) -> Tuple[Dict[str, Any], str, Any, Dict[str, Any], Any, Any]:
    """Train candidate models for expense forecasting strictly on Dev and evaluate on Holdout."""
    X_train, y_train = train_df[FEATURE_COLS].values, train_df["total_expense"].values
    X_val, y_val = val_df[FEATURE_COLS].values, val_df["total_expense"].values
    X_test, y_test = test_df[FEATURE_COLS].values, test_df["total_expense"].values

    candidates = {}

    # 1. Naive Baseline (Lag 1)
    val_pred_naive = val_df["lag_1"].values
    test_pred_naive = test_df["lag_1"].values
    candidates["Naive_Baseline"] = {
        "val_metrics": compute_metrics(y_val, val_pred_naive),
        "test_metrics": compute_metrics(y_test, test_pred_naive),
        "model": None,
    }

    # 2. Seasonal-Naive Baseline (Lag 6)
    val_pred_snaive = val_df["lag_6"].values
    test_pred_snaive = test_df["lag_6"].values
    candidates["Seasonal_Naive"] = {
        "val_metrics": compute_metrics(y_val, val_pred_snaive),
        "test_metrics": compute_metrics(y_test, test_pred_snaive),
        "model": None,
    }

    # 3. Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    val_pred_lr = np.maximum(0, lr.predict(X_val))
    test_pred_lr = np.maximum(0, lr.predict(X_test))
    candidates["Linear_Regression"] = {
        "val_metrics": compute_metrics(y_val, val_pred_lr),
        "test_metrics": compute_metrics(y_test, test_pred_lr),
        "model": lr,
    }

    # 4. XGBoost
    xgb = XGBRegressor(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    xgb.fit(X_train, y_train)
    val_pred_xgb = np.maximum(0, xgb.predict(X_val))
    test_pred_xgb = np.maximum(0, xgb.predict(X_test))
    candidates["XGBoost"] = {
        "val_metrics": compute_metrics(y_val, val_pred_xgb),
        "test_metrics": compute_metrics(y_test, test_pred_xgb),
        "model": xgb,
    }

    # 5. LightGBM
    lgb = LGBMRegressor(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
        verbose=-1
    )
    lgb.fit(X_train, y_train)
    val_pred_lgb = np.maximum(0, lgb.predict(X_val))
    test_pred_lgb = np.maximum(0, lgb.predict(X_test))
    candidates["LightGBM"] = {
        "val_metrics": compute_metrics(y_val, val_pred_lgb),
        "test_metrics": compute_metrics(y_test, test_pred_lgb),
        "model": lgb,
    }

    # 6. SARIMA on aggregated monthly total company expenses
    try:
        monthly_total_train = train_df.groupby("month")["total_expense"].sum().asfreq("ME", method="ffill")
        monthly_total_val = val_df.groupby("month")["total_expense"].sum().asfreq("ME", method="ffill")
        monthly_total_test = test_df.groupby("month")["total_expense"].sum().asfreq("ME", method="ffill")

        sarima = SARIMAX(monthly_total_train, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0), enforce_stationarity=False, enforce_invertibility=False)
        sarima_fit = sarima.fit(disp=False)
        val_pred_sarima = np.maximum(0, sarima_fit.forecast(steps=len(monthly_total_val)))
        test_pred_sarima = np.maximum(0, sarima_fit.forecast(steps=len(monthly_total_test)))

        candidates["SARIMA_Aggregated"] = {
            "val_metrics": compute_metrics(monthly_total_val.values, val_pred_sarima.values),
            "test_metrics": compute_metrics(monthly_total_test.values, test_pred_sarima.values),
            "model": sarima_fit,
        }
    except Exception as e:
        logger.warning(f"SARIMA training warning: {e}")

    # Model Selection: Strictly based on Dev validation WAPE among category-level models
    cat_models = {k: v for k, v in candidates.items() if v["model"] is not None and k != "SARIMA_Aggregated"}
    best_name = min(cat_models, key=lambda k: cat_models[k]["val_metrics"]["wape"])
    best_model = cat_models[best_name]["model"]

    # True Zero-Shot Evaluation on Holdout Company 3
    if len(holdout_co3_df) > 0:
        X_co3 = holdout_co3_df[FEATURE_COLS].values
        y_co3 = holdout_co3_df["total_expense"].values

        # Frozen winning model prediction
        co3_pred = np.maximum(0, best_model.predict(X_co3))
        holdout_metrics = compute_metrics(y_co3, co3_pred)

        # Baseline predictions on Company 3
        co3_pred_naive = holdout_co3_df["lag_1"].values
        co3_pred_snaive = holdout_co3_df["lag_6"].values
        holdout_metrics["baseline_naive_metrics"] = compute_metrics(y_co3, co3_pred_naive)
        holdout_metrics["baseline_snaive_metrics"] = compute_metrics(y_co3, co3_pred_snaive)
        holdout_metrics["n_observations"] = len(holdout_co3_df)
    else:
        holdout_metrics = {}

    return candidates, best_name, best_model, holdout_metrics, xgb, lr


def compute_expense_variance_by_category(df: pd.DataFrame, model: Any) -> pd.DataFrame:
    """Compute variance analysis table comparing actual vs predicted expenses by category."""
    df_eval = df.copy()
    df_eval["predicted_expense"] = np.round(np.maximum(0, model.predict(df_eval[FEATURE_COLS].values)), 2)
    df_eval["variance"] = np.round(df_eval["predicted_expense"] - df_eval["total_expense"], 2)

    cat_variance = df_eval.groupby("category").agg({
        "total_expense": "sum",
        "predicted_expense": "sum",
        "variance": "sum"
    }).reset_index()

    cat_variance["pct_variance"] = np.round(
        (cat_variance["variance"] / np.maximum(cat_variance["total_expense"], 1.0)) * 100, 2
    )
    cat_variance = cat_variance.sort_values("total_expense", ascending=False).reset_index(drop=True)
    return cat_variance


def run_pipeline() -> Dict[str, Any]:
    """Execute operating expense forecasting pipeline."""
    logger.info("Starting Operating Expense Forecasting Pipeline...")

    train_df, val_df, test_df, holdout_co3_df = load_and_split_expense_data()
    logger.info(f"Expense splits - Train: {train_df.shape}, Val: {val_df.shape}, Test: {test_df.shape}, Holdout Co3: {holdout_co3_df.shape}")

    candidates, best_name, best_model, holdout_metrics, xgb_model, lr_model = train_and_evaluate_candidates(
        train_df, val_df, test_df, holdout_co3_df
    )

    logger.info(f"Selected Expense Model: {best_name}")
    for name, data in candidates.items():
        vm = data["val_metrics"]
        tm = data["test_metrics"]
        logger.info(f"Candidate: {name:<22} | Val WAPE: {vm.get('wape', 0):.2f}% | Test WAPE: {tm.get('wape', 0):.2f}% | Test R2: {tm.get('r2', 0):.4f}")

    logger.info(f"Approach C Holdout Co3 WAPE: {holdout_metrics.get('wape', 0):.2f}% | R2: {holdout_metrics.get('r2', 0):.4f}")

    # Generate and save expense variance by category
    all_df = pd.concat([train_df, val_df, test_df]).reset_index(drop=True)
    cat_variance = compute_expense_variance_by_category(all_df, best_model)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    variance_path = REPORTS_DIR / "expense_variance_by_category.csv"
    cat_variance.to_csv(variance_path, index=False)
    logger.info(f"Saved category expense variance report to {variance_path}")

    # Save artifacts for backend compatibility:
    # 1. expense_prediction_xgboost.pkl
    save_model(
        {"model": xgb_model, "feature_cols": FEATURE_COLS},
        "expense_prediction_xgboost.pkl",
        MODELS_DIR
    )

    # 2. expense_prediction_linear_regression.pkl
    save_model(
        {"model": lr_model, "feature_cols": FEATURE_COLS, "algorithm": "LinearRegression"},
        "expense_prediction_linear_regression.pkl",
        MODELS_DIR
    )

    # 3. Canonical Selected Model artifact (winner)
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
        "expense_prediction_selected.pkl",
        MODELS_DIR
    )

    # 3. expense_feature_meta.json
    feature_meta = {
        "pipeline": "operating_expense_forecasting",
        "target": "total_expense",
        "horizon": "1 month ahead per expense category",
        "features": FEATURE_COLS,
        "selected_model": best_name,
        "selected_artifact": "expense_prediction_selected.pkl",
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "test_metrics": candidates[best_name]["test_metrics"],
        "approach_c_holdout_co3_metrics": holdout_metrics
    }
    with open(MODELS_DIR / "expense_feature_meta.json", "w", encoding="utf-8") as f:
        json.dump(feature_meta, f, indent=2)

    # 4. ml/reports/expense_prediction_eval.json
    eval_report = {
        "pipeline": "operating_expense_forecasting",
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
            "business_id": HOLDOUT_COMPANY,
            "business_name": "Apna Kirana Store",
            "metrics": holdout_metrics
        }
    }
    with open(REPORTS_DIR / "expense_prediction_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    logger.info("Operating Expense Forecasting Pipeline completed successfully.")
    return eval_report


if __name__ == "__main__":
    run_pipeline()

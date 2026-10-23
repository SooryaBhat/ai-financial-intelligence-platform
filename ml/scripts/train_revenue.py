# -*- coding: utf-8 -*-
"""
train_revenue.py
================
Train, compare, and evaluate revenue forecasting candidate models (Approach C).

Candidate models evaluated under fair chronological splits:
1. Naive Baseline (Lag 1)
2. Seasonal-Naive Baseline (Lag 12)
3. Linear Regression
4. Random Forest Regressor
5. XGBoost Regressor
6. LightGBM Regressor
7. SARIMAX (Platform Time-Series)
8. ALLADIN Adaptive Global Forecaster (AAGF - Custom Model)

Chronological Splits:
- Train: up to 2023-12-31 (24 months)
- Validation: 2024-01-01 to 2024-06-30 (6 months, model selection strictly performed here)
- Test: 2024-07-01 to 2024-12-31 (6 months, out-of-sample final evaluation)

Approach C Business Holdout:
- Models trained strictly on Companies 1 & 2; evaluated on held-out Company 3 (Apna Kirana Store).

Outputs:
- Artifacts named by their true algorithm identity:
  - ml/models/revenue_forecasting_linear_regression.pkl
  - ml/models/revenue_forecasting_xgboost.pkl
  - ml/models/revenue_forecasting_aagf.pkl
  - ml/models/revenue_forecasting_sarima.pkl
  - ml/models/revenue_forecasting_selected.pkl (canonical winner)
- Reports:
  - ml/reports/revenue_forecasting_eval.json
  - ml/models/revenue_feature_meta.json
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
from statsmodels.tsa.statespace.sarimax import SARIMAX

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, compute_metrics, save_model,
    MODELS_DIR, REPORTS_DIR, PROCESSED_DIR
)
from aagf_model import ALLADINAdaptiveGlobalForecaster

logger = get_logger(__name__)

FEATURE_COLS = [
    "lag_1", "lag_2", "lag_3", "lag_6", "lag_12",
    "roll3_mean", "roll6_mean", "month_num", "quarter"
]


DEV_COMPANIES = ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"]
HOLDOUT_COMPANY = "00000000-0000-0000-0000-000000000003"


def load_and_split_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load revenue features and perform strict development (Co 1 & 2) and unseen holdout (Co 3) splits.
    Step 4: Companies 1 & 2 are used exclusively for model development (train, val, dev-test).
    Company 3 is strictly held-out and completely excluded from model fitting and tuning.
    """
    feat_df = load_csv("revenue_features.csv", PROCESSED_DIR)
    feat_df["month"] = pd.to_datetime(feat_df["month"])
    feat_df = feat_df.sort_values(["company_id", "month"]).reset_index(drop=True)

    # Development split (Companies 1 & 2 strictly)
    dev_df = feat_df[feat_df["company_id"].isin(DEV_COMPANIES)].copy()
    train_df = dev_df[dev_df["month"] <= "2023-12-31"].copy()
    val_df = dev_df[(dev_df["month"] >= "2024-01-01") & (dev_df["month"] <= "2024-06-30")].copy()
    test_df = dev_df[dev_df["month"] >= "2024-07-01"].copy()

    # Strictly Held-Out Company 3 (Apna Kirana Store)
    holdout_co3_df = feat_df[feat_df["company_id"] == HOLDOUT_COMPANY].copy()

    return train_df, val_df, test_df, holdout_co3_df


def train_and_evaluate_candidates(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    holdout_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Train all candidate models, evaluate on validation and test sets, and select best."""
    X_train, y_train = train_df[FEATURE_COLS].values, train_df["revenue"].values
    X_val, y_val = val_df[FEATURE_COLS].values, val_df["revenue"].values
    X_test, y_test = test_df[FEATURE_COLS].values, test_df["revenue"].values
    X_holdout, y_holdout = holdout_df[FEATURE_COLS].values, holdout_df["revenue"].values

    candidates = {}

    # 1. Baselines
    val_pred_naive = val_df["lag_1"].values
    test_pred_naive = test_df["lag_1"].values
    candidates["Naive_Baseline"] = {
        "val_metrics": compute_metrics(y_val, val_pred_naive),
        "test_metrics": compute_metrics(y_test, test_pred_naive),
        "model": None,
    }

    val_pred_snaive = val_df["lag_12"].values
    test_pred_snaive = test_df["lag_12"].values
    candidates["Seasonal_Naive"] = {
        "val_metrics": compute_metrics(y_val, val_pred_snaive),
        "test_metrics": compute_metrics(y_test, test_pred_snaive),
        "model": None,
    }

    # 2. Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    candidates["Linear_Regression"] = {
        "val_metrics": compute_metrics(y_val, lr.predict(X_val)),
        "test_metrics": compute_metrics(y_test, lr.predict(X_test)),
        "model": lr,
    }

    # 3. Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)
    candidates["Random_Forest"] = {
        "val_metrics": compute_metrics(y_val, rf.predict(X_val)),
        "test_metrics": compute_metrics(y_test, rf.predict(X_test)),
        "model": rf,
    }

    # 4. XGBoost (genuine model)
    xgb = XGBRegressor(n_estimators=120, max_depth=4, learning_rate=0.05, subsample=0.85, random_state=42)
    xgb.fit(X_train, y_train)
    candidates["XGBoost"] = {
        "val_metrics": compute_metrics(y_val, xgb.predict(X_val)),
        "test_metrics": compute_metrics(y_test, xgb.predict(X_test)),
        "model": xgb,
    }

    # 5. LightGBM
    lgb = LGBMRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, verbose=-1)
    lgb.fit(X_train, y_train)
    candidates["LightGBM"] = {
        "val_metrics": compute_metrics(y_val, lgb.predict(X_val)),
        "test_metrics": compute_metrics(y_test, lgb.predict(X_test)),
        "model": lgb,
    }

    # 6. Custom Model: ALLADIN Adaptive Global Forecaster (AAGF)
    aagf = ALLADINAdaptiveGlobalForecaster(name="AAGF-Revenue", random_state=42)
    aagf.fit(train_df, y_train, val_df, y_val)
    val_pred_aagf = aagf.predict(val_df)
    test_pred_aagf = aagf.predict(test_df)
    candidates["AAGF_Custom"] = {
        "val_metrics": compute_metrics(y_val, val_pred_aagf),
        "test_metrics": compute_metrics(y_test, test_pred_aagf),
        "model": aagf,
        "weights": aagf.weights.tolist(),
    }

    # 7. SARIMAX on aggregated monthly series
    sarima_model = None
    try:
        ts_train = train_df.groupby("month")["revenue"].sum().sort_index()
        ts_val = val_df.groupby("month")["revenue"].sum().sort_index()
        ts_test = test_df.groupby("month")["revenue"].sum().sort_index()
        sarima = SARIMAX(ts_train.values, order=(1, 1, 1), seasonal_order=(1, 1, 0, 12), enforce_stationarity=False, enforce_invertibility=False)
        sarima_res = sarima.fit(disp=False)
        sarima_model = sarima_res
        sarima_val_pred = sarima_res.forecast(steps=len(ts_val))
        sarima_test_pred = sarima_res.forecast(steps=len(ts_val) + len(ts_test))[len(ts_val):]
        candidates["SARIMA"] = {
            "val_metrics": compute_metrics(ts_val.values, sarima_val_pred),
            "test_metrics": compute_metrics(ts_test.values, sarima_test_pred),
            "model": sarima_res,
        }
    except Exception as e:
        logger.warning("SARIMA fitting encountered: %s", e)

    # Model Selection: Strictly based on validation WAPE on Companies 1 & 2
    supervised_candidates = {k: v for k, v in candidates.items() if v["model"] is not None and k != "SARIMA"}
    selected_name = min(supervised_candidates.keys(), key=lambda k: supervised_candidates[k]["val_metrics"]["wape"])
    selected_model = supervised_candidates[selected_name]["model"]

    # Step 4 Zero-Shot Holdout Evaluation on Company 3 (Apna Kirana)
    # The production selected model trained strictly on Dev Companies (1 & 2) is evaluated on Company 3
    if selected_name == "AAGF_Custom":
        holdout_pred = selected_model.predict(holdout_df)
    else:
        holdout_pred = selected_model.predict(X_holdout)

    holdout_metrics = compute_metrics(y_holdout, holdout_pred)
    holdout_naive_pred = holdout_df["lag_1"].values
    holdout_naive_metrics = compute_metrics(y_holdout, holdout_naive_pred)

    return {
        "candidates": candidates,
        "selected_model_name": selected_name,
        "selected_model": selected_model,
        "lr_model": lr,
        "xgb_model": xgb,
        "aagf_model": aagf,
        "sarima_model": sarima_model,
        "holdout_metrics": holdout_metrics,
        "holdout_naive_metrics": holdout_naive_metrics,
    }


def save_revenue_artifacts(results: Dict[str, Any]) -> None:
    """Save all individual models by their true identities, plus the canonical winner."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Genuine Linear Regression artifact
    save_model(
        {"model": results["lr_model"], "feature_cols": FEATURE_COLS, "algorithm": "LinearRegression"},
        "revenue_forecasting_linear_regression.pkl",
        MODELS_DIR
    )

    # 2. Genuine XGBoost artifact (contains actual XGBRegressor!)
    save_model(
        {"model": results["xgb_model"], "feature_cols": FEATURE_COLS, "algorithm": "XGBRegressor"},
        "revenue_forecasting_xgboost.pkl",
        MODELS_DIR
    )

    # 3. Custom AAGF artifact
    save_model(
        {
            "model": results["aagf_model"],
            "feature_cols": results["aagf_model"].feature_cols,
            "weights": results["aagf_model"].weights.tolist(),
            "algorithm": "ALLADINAdaptiveGlobalForecaster"
        },
        "revenue_forecasting_aagf.pkl",
        MODELS_DIR
    )

    # 4. Genuine SARIMA artifact
    if results.get("sarima_model") is not None:
        save_model(results["sarima_model"], "revenue_forecasting_sarima.pkl", MODELS_DIR)

    # 5. Canonical Selected Model artifact (Winner of validation selection)
    selected_name = results["selected_model_name"]
    selected_model = results["selected_model"]
    selected_feat_cols = results["aagf_model"].feature_cols if selected_name == "AAGF_Custom" else FEATURE_COLS

    save_model(
        {
            "model": selected_model,
            "feature_cols": selected_feat_cols,
            "algorithm": selected_name,
            "selection_metric": "val_wape",
            "val_wape": results["candidates"][selected_name]["val_metrics"]["wape"],
            "test_wape": results["candidates"][selected_name]["test_metrics"]["wape"],
        },
        "revenue_forecasting_selected.pkl",
        MODELS_DIR
    )

    # 6. Feature metadata
    meta = {
        "task": "revenue_forecasting",
        "selected_model": selected_name,
        "selected_artifact": "revenue_forecasting_selected.pkl",
        "features": selected_feat_cols,
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "training_period": "2022-07-31 to 2023-12-31",
        "validation_period": "2024-01-01 to 2024-06-30",
        "dev_test_period": "2024-07-01 to 2024-12-31",
        "algorithm_artifacts": {
            "linear_regression": "revenue_forecasting_linear_regression.pkl",
            "xgboost": "revenue_forecasting_xgboost.pkl",
            "aagf_custom": "revenue_forecasting_aagf.pkl",
            "sarima": "revenue_forecasting_sarima.pkl"
        },
        "selection_rationale": "Validation WAPE on Dev Companies (1 & 2) 2024-01-01 to 2024-06-30",
        "synthetic_data_evaluation_only": True
    }
    with open(MODELS_DIR / "revenue_feature_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # 7. Comprehensive evaluation report
    report = {
        "pipeline": "revenue_forecasting",
        "strategy": "Global Models trained on Dev Companies 1 & 2 with zero-shot holdout evaluation on Company 3",
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "selected_model": selected_name,
        "selection_metric": "val_wape_pct",
        "candidates": {
            k: {
                "val_wape_pct": round(v["val_metrics"]["wape"], 2),
                "val_rmse": round(v["val_metrics"]["rmse"], 2),
                "val_mae": round(v["val_metrics"]["mae"], 2),
                "val_r2": round(v["val_metrics"]["r2"], 4),
                "test_wape_pct": round(v["test_metrics"]["wape"], 2),
                "test_rmse": round(v["test_metrics"]["rmse"], 2),
                "test_r2": round(v["test_metrics"]["r2"], 4),
                "details": {"blend_weights": v.get("weights")} if "weights" in v else {}
            }
            for k, v in results["candidates"].items()
        },
        "approach_c_holdout_company3_metrics": {
            "wape_pct": round(results["holdout_metrics"]["wape"], 2),
            "rmse": round(results["holdout_metrics"]["rmse"], 2),
            "mae": round(results["holdout_metrics"]["mae"], 2),
            "r2": round(results["holdout_metrics"]["r2"], 4),
            "naive_baseline_wape_pct": round(results["holdout_naive_metrics"]["wape"], 2),
            "naive_baseline_r2": round(results["holdout_naive_metrics"]["r2"], 4),
        },
    }
    report_path = REPORTS_DIR / "revenue_forecasting_eval.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info("Saved revenue evaluation report: %s", report_path)


def run_pipeline() -> Dict[str, Any]:
    logger.info("Running Revenue Forecasting Pipeline (Pipeline 1) with AAGF and Fair Comparison...")
    train_df, val_df, test_df, holdout_df = load_and_split_data()
    results = train_and_evaluate_candidates(train_df, val_df, test_df, holdout_df)
    save_revenue_artifacts(results)
    return results


if __name__ == "__main__":
    run_pipeline()

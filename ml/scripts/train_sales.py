# -*- coding: utf-8 -*-
"""
train_sales.py
==============
Train, compare, and evaluate product-level and category-level sales forecasting models (Approach C).

Candidate models evaluated:
1. Naive Baseline (Lag 1)
2. Seasonal-Naive Baseline (Lag 12)
3. Moving Average Baseline (Roll 3)
4. Linear Regression
5. Ridge Regression
6. Random Forest Regressor
7. XGBoost Regressor
8. LightGBM Regressor
9. Croston's Intermittent Demand Method
10. Syntetos-Boylan Approximation (SBA)
11. Product Profile Forecaster (Custom Hierarchical Model)
12. ALLADIN Adaptive Global Forecaster (AAGF - Custom Ensemble)

Target: Monthly unit sales (quantity) per SKU or Category.
Chronological splits strictly separate Train, Validation, and Test:
- Train: up to 2025-06-30 (42 months)
- Validation: 2025-07-01 to 2025-12-31 (6 months)
- Dev Test: 2026-01-01 to 2026-10-31 (10 months)

Outputs:
- ml/models/sales_forecasting_linear_regression_product.pkl
- ml/models/sales_forecasting_xgb_product.pkl
- ml/models/sales_forecasting_lgb_product.pkl
- ml/models/sales_forecasting_aagf_product.pkl
- ml/models/sales_forecasting_product_profile.pkl
- ml/models/sales_forecasting_selected.pkl (canonical winner)
- ml/models/sales_forecasting_xgb_category.pkl
- ml/models/sales_feature_meta.json
- ml/reports/sales_forecasting_eval.json
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
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, compute_metrics, save_model,
    MODELS_DIR, REPORTS_DIR, PROCESSED_DIR, SYNTHETIC_DIR,
    DEV_COMPANIES, HOLDOUT_COMPANY, SPLIT_CONFIG
)
from aagf_model import ALLADINAdaptiveGlobalForecaster
from custom_models.intermittent_demand import CrostonMethod, SBAMethod
from custom_models.product_profile_model import ProductProfileForecaster

logger = get_logger(__name__)

FEATURE_COLS = [
    "lag_1", "lag_2", "lag_3", "lag_12",
    "roll3_mean", "roll6_mean", "roll3_std",
    "month_num", "quarter", "year", "is_q4", "is_q1"
]


def load_and_split_product_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load product sales features and generate strict development (Co 1 & 2) and holdout (Co 3) splits.
    Companies 1 & 2 are used exclusively for model development (train, val, dev-test).
    Company 3 is strictly held-out and completely excluded from model fitting and tuning.
    """
    df = load_csv("sales_features.csv", PROCESSED_DIR)
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values(["company_id", "product_id", "month"]).reset_index(drop=True)

    # Strictly Companies 1 & 2 for development
    dev_df = df[df["company_id"].isin(DEV_COMPANIES)].copy()
    train_mask = (dev_df["month"] <= SPLIT_CONFIG["train_end"])
    val_mask = (dev_df["month"] >= SPLIT_CONFIG["val_start"]) & (dev_df["month"] <= SPLIT_CONFIG["val_end"])
    test_mask = (dev_df["month"] >= SPLIT_CONFIG["test_start"])

    train_df = dev_df[train_mask].copy()
    val_df = dev_df[val_mask].copy()
    test_df = dev_df[test_mask].copy()

    # Strictly Held-out Company 3 (Apna Kirana Store)
    holdout_co3_df = df[df["company_id"] == HOLDOUT_COMPANY].copy()

    return train_df, val_df, test_df, holdout_co3_df


def build_category_features() -> pd.DataFrame:
    """Build aggregated category-level monthly sales features."""
    items = load_csv("sale_items_clean.csv", PROCESSED_DIR)
    sales = load_csv("sales_clean.csv", PROCESSED_DIR)
    products = load_csv("products.csv", SYNTHETIC_DIR)

    items_sales = items.merge(sales[["id", "company_id", "sale_date"]], left_on="sale_id", right_on="id", how="inner")
    items_cat = items_sales.merge(products[["id", "category_id"]], left_on="product_id", right_on="id", how="inner")
    items_cat["month"] = pd.to_datetime(items_cat["sale_date"]).dt.to_period("M").dt.to_timestamp("M")

    cat_monthly = items_cat.groupby(["company_id", "category_id", "month"])["quantity"].sum().reset_index()
    cat_monthly = cat_monthly.sort_values(["company_id", "category_id", "month"]).reset_index(drop=True)

    records = []
    for (cid, cat_id), group in cat_monthly.groupby(["company_id", "category_id"]):
        group = group.sort_values("month").reset_index(drop=True)
        q = group["quantity"]

        for i in range(len(group)):
            m = group.loc[i, "month"]
            row = {
                "company_id": cid,
                "category_id": cat_id,
                "month": m,
                "quantity": group.loc[i, "quantity"],
                "lag_1": q.iloc[i-1] if i >= 1 else q.iloc[0],
                "lag_2": q.iloc[i-2] if i >= 2 else q.iloc[0],
                "lag_3": q.iloc[i-3] if i >= 3 else q.iloc[0],
                "lag_12": q.iloc[i-12] if i >= 12 else (q.iloc[i-1] if i >= 1 else q.iloc[0]),
                "roll3_mean": q.iloc[max(0, i-3):i].mean() if i >= 1 else q.iloc[0],
                "roll6_mean": q.iloc[max(0, i-6):i].mean() if i >= 1 else q.iloc[0],
                "roll3_std": (q.iloc[max(0, i-3):i].std() if i >= 2 else 0.0) or 0.0,
                "month_num": float(m.month),
                "quarter": float(m.quarter),
                "year": float(m.year),
                "is_q4": 1.0 if m.quarter == 4 else 0.0,
                "is_q1": 1.0 if m.quarter == 1 else 0.0,
            }
            records.append(row)

    cat_df = pd.DataFrame(records).fillna(0.0)
    return cat_df


def train_and_evaluate_product_candidates(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    holdout_co3_df: pd.DataFrame,
) -> Tuple[Dict[str, Any], str, Any, Dict[str, Any], Dict[str, Any]]:
    """Train candidates for product sales forecasting and select the best."""
    X_train, y_train = train_df[FEATURE_COLS].values, train_df["quantity"].values
    X_val, y_val = val_df[FEATURE_COLS].values, val_df["quantity"].values
    X_test, y_test = test_df[FEATURE_COLS].values, test_df["quantity"].values

    candidates = {}

    # 1. Naive Baseline (Lag 1)
    val_pred_naive = val_df["lag_1"].values
    test_pred_naive = test_df["lag_1"].values
    candidates["Naive_Baseline"] = {
        "val_metrics": compute_metrics(y_val, val_pred_naive, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_naive, y_train),
        "model": None,
        "is_baseline": True,
    }

    # 2. Seasonal-Naive Baseline (Lag 12)
    val_pred_snaive = val_df["lag_12"].values
    test_pred_snaive = test_df["lag_12"].values
    candidates["Seasonal_Naive"] = {
        "val_metrics": compute_metrics(y_val, val_pred_snaive, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_snaive, y_train),
        "model": None,
        "is_baseline": True,
    }

    # 3. Moving Average Baseline (Roll 3)
    val_pred_ma = val_df["roll3_mean"].values
    test_pred_ma = test_df["roll3_mean"].values
    candidates["Moving_Average_3m"] = {
        "val_metrics": compute_metrics(y_val, val_pred_ma, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_ma, y_train),
        "model": None,
        "is_baseline": True,
    }

    # 4. Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    val_pred_lr = np.maximum(0, lr.predict(X_val))
    test_pred_lr = np.maximum(0, lr.predict(X_test))
    candidates["Linear_Regression"] = {
        "val_metrics": compute_metrics(y_val, val_pred_lr, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_lr, y_train),
        "model": lr,
        "is_baseline": False,
    }

    # 5. Ridge Regression
    ridge = Ridge(alpha=1.0, random_state=42)
    ridge.fit(X_train, y_train)
    val_pred_ridge = np.maximum(0, ridge.predict(X_val))
    test_pred_ridge = np.maximum(0, ridge.predict(X_test))
    candidates["Ridge_Regression"] = {
        "val_metrics": compute_metrics(y_val, val_pred_ridge, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_ridge, y_train),
        "model": ridge,
        "is_baseline": False,
    }

    # 6. Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    val_pred_rf = np.maximum(0, rf.predict(X_val))
    test_pred_rf = np.maximum(0, rf.predict(X_test))
    candidates["Random_Forest"] = {
        "val_metrics": compute_metrics(y_val, val_pred_rf, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_rf, y_train),
        "model": rf,
        "is_baseline": False,
    }

    # 7. XGBoost
    xgb = XGBRegressor(n_estimators=120, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42)
    xgb.fit(X_train, y_train)
    val_pred_xgb = np.maximum(0, xgb.predict(X_val))
    test_pred_xgb = np.maximum(0, xgb.predict(X_test))
    candidates["XGBoost"] = {
        "val_metrics": compute_metrics(y_val, val_pred_xgb, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_xgb, y_train),
        "model": xgb,
        "is_baseline": False,
    }

    # 8. LightGBM
    lgb = LGBMRegressor(n_estimators=120, max_depth=5, learning_rate=0.05, subsample=0.8, random_state=42, verbose=-1)
    lgb.fit(X_train, y_train)
    val_pred_lgb = np.maximum(0, lgb.predict(X_val))
    test_pred_lgb = np.maximum(0, lgb.predict(X_test))
    candidates["LightGBM"] = {
        "val_metrics": compute_metrics(y_val, val_pred_lgb, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_lgb, y_train),
        "model": lgb,
        "is_baseline": False,
    }

    # 9. CatBoost
    cb = CatBoostRegressor(iterations=120, depth=5, learning_rate=0.05, verbose=0, random_seed=42)
    cb.fit(X_train, y_train)
    val_pred_cb = np.maximum(0, cb.predict(X_val))
    test_pred_cb = np.maximum(0, cb.predict(X_test))
    candidates["CatBoost"] = {
        "val_metrics": compute_metrics(y_val, val_pred_cb, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_cb, y_train),
        "model": cb,
        "is_baseline": False,
    }

    # 9. Croston's Method
    croston = CrostonMethod(alpha=0.15)
    croston.fit(None, y_train)
    val_pred_croston = np.maximum(0, croston.predict(np.zeros(len(y_val))))
    test_pred_croston = np.maximum(0, croston.predict(np.zeros(len(y_test))))
    candidates["Croston_Method"] = {
        "val_metrics": compute_metrics(y_val, val_pred_croston, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_croston, y_train),
        "model": croston,
        "is_baseline": False,
    }

    # 10. SBA Method
    sba = SBAMethod(alpha=0.15)
    sba.fit(None, y_train)
    val_pred_sba = np.maximum(0, sba.predict(np.zeros(len(y_val))))
    test_pred_sba = np.maximum(0, sba.predict(np.zeros(len(y_test))))
    candidates["SBA_Method"] = {
        "val_metrics": compute_metrics(y_val, val_pred_sba, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_sba, y_train),
        "model": sba,
        "is_baseline": False,
    }

    # 11. Product Profile Forecaster (Custom Hierarchical)
    ppf = ProductProfileForecaster(alpha=1.0, random_state=42)
    ppf.fit(train_df, y_train)
    val_pred_ppf = np.maximum(0, ppf.predict(val_df))
    test_pred_ppf = np.maximum(0, ppf.predict(test_df))
    candidates["Product_Profile_Forecaster"] = {
        "val_metrics": compute_metrics(y_val, val_pred_ppf, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_ppf, y_train),
        "model": ppf,
        "is_baseline": False,
    }

    # 12. Custom Model: ALLADIN Adaptive Global Forecaster (AAGF)
    aagf_prod = ALLADINAdaptiveGlobalForecaster(name="AAGF-ProductSales", random_state=42)
    aagf_prod.fit(train_df, y_train, val_df, y_val, feature_cols=FEATURE_COLS)
    val_pred_aagf = np.maximum(0, aagf_prod.predict(val_df))
    test_pred_aagf = np.maximum(0, aagf_prod.predict(test_df))
    candidates["AAGF_Custom"] = {
        "val_metrics": compute_metrics(y_val, val_pred_aagf, y_train),
        "test_metrics": compute_metrics(y_test, test_pred_aagf, y_train),
        "model": aagf_prod,
        "weights": aagf_prod.weights.tolist(),
        "is_baseline": False,
    }

    # Model Selection: Strictly based on validation WAPE among supervised candidates
    supervised = {k: v for k, v in candidates.items() if v["model"] is not None}
    best_name = min(supervised, key=lambda k: supervised[k]["val_metrics"]["wape"])
    best_model = supervised[best_name]["model"]

    # Zero-Shot Holdout Evaluation on Company 3 (Apna Kirana)
    if best_name == "AAGF_Custom":
        holdout_pred = np.maximum(0, best_model.predict(holdout_co3_df))
    elif best_name == "Product_Profile_Forecaster":
        holdout_pred = np.maximum(0, best_model.predict(holdout_co3_df))
    elif best_name in ["Croston_Method", "SBA_Method"]:
        holdout_pred = np.maximum(0, best_model.predict(np.zeros(len(holdout_co3_df))))
    else:
        holdout_pred = np.maximum(0, best_model.predict(holdout_co3_df[FEATURE_COLS].values))

    holdout_metrics = compute_metrics(holdout_co3_df["quantity"].values, holdout_pred, y_train)
    holdout_naive_pred = holdout_co3_df["lag_1"].values
    holdout_naive_metrics = compute_metrics(holdout_co3_df["quantity"].values, holdout_naive_pred, y_train)

    models_dict = {
        "lr": lr,
        "ridge": ridge,
        "rf": rf,
        "xgb": xgb,
        "lgb": lgb,
        "cb": cb,
        "ppf": ppf,
        "aagf": aagf_prod
    }

    return candidates, best_name, best_model, {
        "metrics": holdout_metrics,
        "naive_baseline_metrics": holdout_naive_metrics
    }, models_dict


def train_category_model(cat_df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """Train XGBoost category-level model and compute evaluation metrics."""
    dev_cat = cat_df[cat_df["company_id"].isin(DEV_COMPANIES)].copy()
    train_mask = (dev_cat["month"] <= SPLIT_CONFIG["train_end"])
    val_mask = (dev_cat["month"] >= SPLIT_CONFIG["val_start"]) & (dev_cat["month"] <= SPLIT_CONFIG["val_end"])
    test_mask = (dev_cat["month"] >= SPLIT_CONFIG["test_start"])

    train_c = dev_cat[train_mask]
    val_c = dev_cat[val_mask]
    test_c = dev_cat[test_mask]

    X_train_c = train_c[FEATURE_COLS].values
    y_train_c = train_c["quantity"].values
    X_val_c = val_c[FEATURE_COLS].values
    y_val_c = val_c["quantity"].values
    X_test_c = test_c[FEATURE_COLS].values
    y_test_c = test_c["quantity"].values

    xgb_cat = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
    xgb_cat.fit(X_train_c, y_train_c)

    val_pred = np.maximum(0, xgb_cat.predict(X_val_c))
    test_pred = np.maximum(0, xgb_cat.predict(X_test_c))

    cat_metrics = {
        "val_metrics": compute_metrics(y_val_c, val_pred, y_train_c),
        "test_metrics": compute_metrics(y_test_c, test_pred, y_train_c)
    }

    return xgb_cat, cat_metrics


def run_pipeline() -> Dict[str, Any]:
    logger.info("Running Sales Forecasting Pipeline (Pipeline 2) with Product & Category Models...")
    train_df, val_df, test_df, holdout_co3_df = load_and_split_product_data()
    candidates, best_name, best_model, holdout_results, models_dict = train_and_evaluate_product_candidates(
        train_df, val_df, test_df, holdout_co3_df
    )

    cat_df = build_category_features()
    xgb_cat, cat_metrics = train_category_model(cat_df)

    # Save artifacts
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    save_model(
        {"model": models_dict["lr"], "feature_cols": FEATURE_COLS, "algorithm": "LinearRegression"},
        "sales_forecasting_linear_regression_product.pkl",
        MODELS_DIR
    )
    save_model(
        {"model": models_dict["xgb"], "feature_cols": FEATURE_COLS, "algorithm": "XGBRegressor"},
        "sales_forecasting_xgb_product.pkl",
        MODELS_DIR
    )
    save_model(
        {"model": models_dict["lgb"], "feature_cols": FEATURE_COLS, "algorithm": "LGBMRegressor"},
        "sales_forecasting_lgb_product.pkl",
        MODELS_DIR
    )
    save_model(
        {"model": models_dict["ppf"], "feature_cols": FEATURE_COLS, "algorithm": "ProductProfileForecaster"},
        "sales_forecasting_product_profile.pkl",
        MODELS_DIR
    )
    save_model(
        {"model": models_dict["aagf"], "feature_cols": FEATURE_COLS, "weights": models_dict["aagf"].weights.tolist(), "algorithm": "ALLADINAdaptiveGlobalForecaster"},
        "sales_forecasting_aagf_product.pkl",
        MODELS_DIR
    )
    save_model(
        {
            "model": best_model,
            "feature_cols": FEATURE_COLS,
            "algorithm": best_name,
            "selection_metric": "val_wape",
            "val_wape": candidates[best_name]["val_metrics"]["wape"],
            "test_wape": candidates[best_name]["test_metrics"]["wape"],
        },
        "sales_forecasting_selected.pkl",
        MODELS_DIR
    )
    save_model(
        {"model": xgb_cat, "feature_cols": FEATURE_COLS, "algorithm": "XGBRegressor_Category"},
        "sales_forecasting_xgb_category.pkl",
        MODELS_DIR
    )

    # Meta
    meta = {
        "task": "sales_forecasting",
        "selected_model": best_name,
        "selected_artifact": "sales_forecasting_selected.pkl",
        "features": FEATURE_COLS,
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "training_period": f"2022-01-01 to {SPLIT_CONFIG['train_end']}",
        "validation_period": f"{SPLIT_CONFIG['val_start']} to {SPLIT_CONFIG['val_end']}",
        "dev_test_period": f"{SPLIT_CONFIG['test_start']} to 2026-10-31",
        "algorithm_artifacts": {
            "linear_regression_product": "sales_forecasting_linear_regression_product.pkl",
            "xgb_product": "sales_forecasting_xgb_product.pkl",
            "lgb_product": "sales_forecasting_lgb_product.pkl",
            "aagf_product": "sales_forecasting_aagf_product.pkl",
            "product_profile": "sales_forecasting_product_profile.pkl",
            "xgb_category": "sales_forecasting_xgb_category.pkl",
        },
        "selection_rationale": f"Validation WAPE on Dev Companies (1 & 2) during {SPLIT_CONFIG['val_start']} to {SPLIT_CONFIG['val_end']}",
        "synthetic_data_evaluation_only": True
    }
    with open(MODELS_DIR / "sales_feature_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Investigation documentation on WAPE and R2
    investigation_notes = {
        "topic": "Large Saved WAPE and Negative R2 Investigation",
        "root_cause_analysis": (
            "1. Granularity & Intermittency: Product SKU-level demand contains sparse zeros, low volumes, and intermittent sales, "
            "where small unit discrepancies (e.g., predicting 3 units when actual is 0 or 1) yield massive percentage errors. "
            "2. Variance Shift vs Mean: In time-series splits, if an item experiences an out-of-sample level drop, global regression models "
            "predicting past historical means suffer SS_res > SS_tot, leading to negative R2. "
            "3. Category Aggregation Effect: At the category level, demand is aggregated across SKUs, smoothing intermittency. "
            f"Category validation WAPE drops to {cat_metrics['val_metrics']['wape']:.2f}% with strong positive R2 ({cat_metrics['val_metrics']['r2']:.4f}). "
            "4. Mitigation: Hierarchical models (ProductProfileForecaster, Croston, and regularized trees like LightGBM) prevent negative predictions "
            "and ground SKU projections in per-product velocity profiles."
        )
    }

    # Evaluation Report
    report = {
        "pipeline": "sales_forecasting",
        "strategy": "Product-level and Category-level sales forecasting (Approach C)",
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "selected_model": best_name,
        "selection_metric": "val_wape_pct",
        "metric_definitions": {
            "wape": "sum(|actual - pred|) / sum(|actual|) * 100% (volume-weighted percentage error)",
            "rmse": "sqrt(mean((actual - pred)^2)) in unit quantities",
            "mae": "mean(|actual - pred|) in unit quantities",
            "r2": "1 - SS_res / SS_tot (coefficient of determination)",
            "bias": "sum(pred - actual) / sum(|actual|) * 100% (positive = overforecasting, negative = underforecasting)",
            "mase": "mae_model / mean(|diff(y_train)|) (relative to training naive random walk)"
        },
        "investigation_wape_and_r2": investigation_notes,
        "candidates": {
            k: {
                "val_wape_pct": round(v["val_metrics"]["wape"], 2),
                "val_rmse": round(v["val_metrics"]["rmse"], 2),
                "val_mae": round(v["val_metrics"]["mae"], 2),
                "val_r2": round(v["val_metrics"]["r2"], 4),
                "val_bias_pct": round(v["val_metrics"]["bias"], 2),
                "val_mase": round(v["val_metrics"]["mase"], 4),
                "test_wape_pct": round(v["test_metrics"]["wape"], 2),
                "test_rmse": round(v["test_metrics"]["rmse"], 2),
                "test_mae": round(v["test_metrics"]["mae"], 2),
                "test_r2": round(v["test_metrics"]["r2"], 4),
                "test_bias_pct": round(v["test_metrics"]["bias"], 2),
                "test_mase": round(v["test_metrics"]["mase"], 4),
                "is_baseline": v.get("is_baseline", False),
            }
            for k, v in candidates.items()
        },
        "category_level_forecasting": {
            "model": "XGBoost_Category",
            "val_wape_pct": round(cat_metrics["val_metrics"]["wape"], 2),
            "val_rmse": round(cat_metrics["val_metrics"]["rmse"], 2),
            "val_mae": round(cat_metrics["val_metrics"]["mae"], 2),
            "val_r2": round(cat_metrics["val_metrics"]["r2"], 4),
            "val_bias_pct": round(cat_metrics["val_metrics"]["bias"], 2),
            "val_mase": round(cat_metrics["val_metrics"]["mase"], 4),
            "test_wape_pct": round(cat_metrics["test_metrics"]["wape"], 2),
            "test_rmse": round(cat_metrics["test_metrics"]["rmse"], 2),
            "test_r2": round(cat_metrics["test_metrics"]["r2"], 4),
        },
        "approach_c_holdout_co3": {
            "selected_model": best_name,
            "metrics": {
                "wape": round(holdout_results["metrics"]["wape"], 2),
                "wape_pct": round(holdout_results["metrics"]["wape"], 2),
                "rmse": round(holdout_results["metrics"]["rmse"], 2),
                "mae": round(holdout_results["metrics"]["mae"], 2),
                "r2": round(holdout_results["metrics"]["r2"], 4),
                "bias_pct": round(holdout_results["metrics"]["bias"], 2),
                "mase": round(holdout_results["metrics"]["mase"], 4),
                "naive_baseline_wape_pct": round(holdout_results["naive_baseline_metrics"]["wape"], 2),
                "naive_baseline_r2": round(holdout_results["naive_baseline_metrics"]["r2"], 4),
            },
            "naive_baseline_metrics": holdout_results["naive_baseline_metrics"],
        }
    }

    report_path = REPORTS_DIR / "sales_forecasting_eval.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info("Saved sales evaluation report: %s", report_path)

    return report


if __name__ == "__main__":
    run_pipeline()

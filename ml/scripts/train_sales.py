# -*- coding: utf-8 -*-
"""
train_sales.py
==============
Train, compare, and evaluate product-level and category-level sales forecasting models (Approach C).

Candidates evaluated:
1. Naive Baseline (Lag 1)
2. Seasonal-Naive Baseline (Lag 12)
3. Linear Regression
4. Random Forest Regressor
5. XGBoost Regressor
6. LightGBM Regressor
7. ALLADIN Adaptive Global Forecaster (AAGF - Custom Model)

Target: Monthly unit sales (quantity) per SKU or Category.
Chronological splits strictly separate Train, Validation, and Test.

Outputs:
- ml/models/sales_forecasting_linear_regression_product.pkl
- ml/models/sales_forecasting_xgb_product.pkl
- ml/models/sales_forecasting_lgb_product.pkl
- ml/models/sales_forecasting_aagf_product.pkl
- ml/models/sales_forecasting_selected.pkl (canonical winner)
- ml/models/sales_forecasting_xgb_category.pkl
- ml/models/sales_feature_meta.json
- ml/reports/sales_forecasting_eval.json

Usage:
    python ml/scripts/train_sales.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List

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
from aagf_model import ALLADINAdaptiveGlobalForecaster

logger = get_logger(__name__)

FEATURE_COLS = [
    "lag_1", "lag_2", "lag_3", "lag_12",
    "roll3_mean", "roll6_mean", "roll3_std",
    "month_num", "quarter", "year", "is_q4", "is_q1"
]


DEV_COMPANIES = ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"]
HOLDOUT_COMPANY = "00000000-0000-0000-0000-000000000003"


def load_and_split_product_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load product sales features and generate strict development (Co 1 & 2) and holdout (Co 3) splits.
    Step 4: Companies 1 & 2 are used exclusively for model development (train, val, dev-test).
    Company 3 is strictly held-out and completely excluded from model fitting and tuning.
    """
    df = load_csv("sales_features.csv", PROCESSED_DIR)
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values(["company_id", "product_id", "month"]).reset_index(drop=True)

    # Strictly Companies 1 & 2 for development
    dev_df = df[df["company_id"].isin(DEV_COMPANIES)].copy()
    train_mask = (dev_df["month"] <= "2024-03-31")
    val_mask = (dev_df["month"] >= "2024-04-01") & (dev_df["month"] <= "2024-08-31")
    test_mask = (dev_df["month"] >= "2024-09-01")

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
        "val_metrics": compute_metrics(y_val, val_pred_naive),
        "test_metrics": compute_metrics(y_test, test_pred_naive),
        "model": None,
    }

    # 2. Seasonal-Naive Baseline (Lag 12)
    val_pred_snaive = val_df["lag_12"].values
    test_pred_snaive = test_df["lag_12"].values
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

    # 4. Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    val_pred_rf = np.maximum(0, rf.predict(X_val))
    test_pred_rf = np.maximum(0, rf.predict(X_test))
    candidates["Random_Forest"] = {
        "val_metrics": compute_metrics(y_val, val_pred_rf),
        "test_metrics": compute_metrics(y_test, test_pred_rf),
        "model": rf,
    }

    # 5. XGBoost
    xgb = XGBRegressor(n_estimators=120, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42)
    xgb.fit(X_train, y_train)
    val_pred_xgb = np.maximum(0, xgb.predict(X_val))
    test_pred_xgb = np.maximum(0, xgb.predict(X_test))
    candidates["XGBoost"] = {
        "val_metrics": compute_metrics(y_val, val_pred_xgb),
        "test_metrics": compute_metrics(y_test, test_pred_xgb),
        "model": xgb,
    }

    # 6. LightGBM
    lgb = LGBMRegressor(n_estimators=120, max_depth=5, learning_rate=0.05, subsample=0.8, random_state=42, verbose=-1)
    lgb.fit(X_train, y_train)
    val_pred_lgb = np.maximum(0, lgb.predict(X_val))
    test_pred_lgb = np.maximum(0, lgb.predict(X_test))
    candidates["LightGBM"] = {
        "val_metrics": compute_metrics(y_val, val_pred_lgb),
        "test_metrics": compute_metrics(y_test, test_pred_lgb),
        "model": lgb,
    }

    # 7. Custom Model: ALLADIN Adaptive Global Forecaster (AAGF) for Product Demand
    aagf_prod = ALLADINAdaptiveGlobalForecaster(name="AAGF-ProductSales", random_state=42)
    aagf_prod.fit(train_df, y_train, val_df, y_val, feature_cols=FEATURE_COLS)
    val_pred_aagf = np.maximum(0, aagf_prod.predict(val_df))
    test_pred_aagf = np.maximum(0, aagf_prod.predict(test_df))
    candidates["AAGF_Custom"] = {
        "val_metrics": compute_metrics(y_val, val_pred_aagf),
        "test_metrics": compute_metrics(y_test, test_pred_aagf),
        "model": aagf_prod,
        "weights": aagf_prod.weights.tolist(),
    }

    # Model Selection: Strictly based on validation WAPE among supervised candidates
    supervised = {k: v for k, v in candidates.items() if v["model"] is not None}
    best_name = min(supervised, key=lambda k: supervised[k]["val_metrics"]["wape"])
    best_model = supervised[best_name]["model"]

    # Step 4 Zero-Shot Holdout Evaluation on Company 3 (Apna Kirana)
    # Production best_model trained strictly on Dev Companies is directly evaluated on Company 3
    if best_name == "AAGF_Custom":
        holdout_pred = np.maximum(0, best_model.predict(holdout_co3_df))
    else:
        holdout_pred = np.maximum(0, best_model.predict(holdout_co3_df[FEATURE_COLS].values))

    holdout_metrics = compute_metrics(holdout_co3_df["quantity"].values, holdout_pred)
    holdout_naive_pred = holdout_co3_df["lag_1"].values
    holdout_naive_metrics = compute_metrics(holdout_co3_df["quantity"].values, holdout_naive_pred)
    holdout_metrics["naive_baseline_comparison"] = {
        "wape": holdout_naive_metrics.get("wape"),
        "r2": holdout_naive_metrics.get("r2"),
    }

    models_dict = {
        "lr": lr,
        "xgb": xgb,
        "lgb": lgb,
        "aagf": aagf_prod,
        "rf": rf
    }

    return candidates, best_name, best_model, holdout_metrics, models_dict


def run_pipeline() -> Dict[str, Any]:
    """Execute product & category sales forecasting pipeline."""
    logger.info("Starting Product & Category Sales Forecasting Pipeline with AAGF...")

    train_df, val_df, test_df, holdout_co3_df = load_and_split_product_data()
    candidates, best_name, best_model, holdout_metrics, models_dict = train_and_evaluate_product_candidates(
        train_df, val_df, test_df, holdout_co3_df
    )

    logger.info(f"Selected Product Sales Model: {best_name}")
    for name, data in candidates.items():
        vm = data["val_metrics"]
        tm = data["test_metrics"]
        logger.info(f"Candidate: {name:<20} | Val WAPE: {vm.get('wape', 0):.2f}% | Test WAPE: {tm.get('wape', 0):.2f}% | Test R2: {tm.get('r2', 0):.4f}")

    logger.info(f"Approach C Holdout Co3 (Apna Kirana) WAPE: {holdout_metrics.get('wape', 0):.2f}% | R2: {holdout_metrics.get('r2', 0):.4f}")

    # Build and train Category Sales Model (XGBoost) on Dev Companies only
    cat_df = build_category_features()
    cat_dev = cat_df[cat_df["company_id"].isin(DEV_COMPANIES)].copy()
    cat_train = cat_dev[cat_dev["month"] <= "2024-03-31"]
    cat_val = cat_dev[(cat_dev["month"] >= "2024-04-01") & (cat_dev["month"] <= "2024-08-31")]
    cat_test = cat_dev[cat_dev["month"] >= "2024-09-01"]

    xgb_cat = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=42)
    xgb_cat.fit(cat_train[FEATURE_COLS].values, cat_train["quantity"].values)
    cat_val_pred = np.maximum(0, xgb_cat.predict(cat_val[FEATURE_COLS].values))
    cat_test_pred = np.maximum(0, xgb_cat.predict(cat_test[FEATURE_COLS].values))
    cat_val_metrics = compute_metrics(cat_val["quantity"].values, cat_val_pred)
    cat_test_metrics = compute_metrics(cat_test["quantity"].values, cat_test_pred)

    logger.info(f"Category Sales Model (XGBoost) | Val WAPE: {cat_val_metrics['wape']:.2f}% | Test WAPE: {cat_test_metrics['wape']:.2f}%")

    # Evaluate Category Model on Company 3 Holdout
    cat_co3 = cat_df[cat_df["company_id"] == HOLDOUT_COMPANY]
    if len(cat_co3) > 0:
        cat_co3_pred = np.maximum(0, xgb_cat.predict(cat_co3[FEATURE_COLS].values))
        cat_co3_metrics = compute_metrics(cat_co3["quantity"].values, cat_co3_pred)
    else:
        cat_co3_metrics = {}

    # Save artifacts by their true identities:
    # 1. Genuine XGBoost product artifact
    save_model({"model": models_dict["xgb"], "feature_cols": FEATURE_COLS, "algorithm": "XGBRegressor"}, "sales_forecasting_xgb_product.pkl", MODELS_DIR)

    # 2. Genuine LightGBM product artifact
    save_model({"model": models_dict["lgb"], "feature_cols": FEATURE_COLS, "algorithm": "LGBMRegressor"}, "sales_forecasting_lgb_product.pkl", MODELS_DIR)

    # 3. Genuine Linear Regression product artifact
    save_model({"model": models_dict["lr"], "feature_cols": FEATURE_COLS, "algorithm": "LinearRegression"}, "sales_forecasting_linear_regression_product.pkl", MODELS_DIR)

    # 4. Custom AAGF product artifact
    save_model({"model": models_dict["aagf"], "feature_cols": models_dict["aagf"].feature_cols, "algorithm": "AAGF_Custom"}, "sales_forecasting_aagf_product.pkl", MODELS_DIR)

    # 5. Canonical Selected Product Model
    selected_feat = models_dict["aagf"].feature_cols if best_name == "AAGF_Custom" else FEATURE_COLS
    save_model({
        "model": best_model,
        "feature_cols": selected_feat,
        "algorithm": best_name,
        "selection_metric": "val_wape",
        "val_wape": candidates[best_name]["val_metrics"]["wape"],
        "test_wape": candidates[best_name]["test_metrics"]["wape"]
    }, "sales_forecasting_selected.pkl", MODELS_DIR)

    # 6. Genuine Category XGBoost artifact
    save_model({"model": xgb_cat, "feature_cols": FEATURE_COLS, "algorithm": "XGBRegressor"}, "sales_forecasting_xgb_category.pkl", MODELS_DIR)

    # 7. Metadata
    feature_meta = {
        "pipeline": "sales_forecasting",
        "strategy": "Global Models trained on Dev Companies 1 & 2 with zero-shot holdout evaluation on Company 3",
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "target": "quantity",
        "selected_product_model": best_name,
        "selected_artifact": "sales_forecasting_selected.pkl",
        "product_features": selected_feat,
        "product_test_metrics": candidates[best_name]["test_metrics"],
        "category_test_metrics": cat_test_metrics,
        "approach_c_holdout_co3_metrics": holdout_metrics,
        "synthetic_data_evaluation_only": True
    }
    with open(MODELS_DIR / "sales_feature_meta.json", "w", encoding="utf-8") as f:
        json.dump(feature_meta, f, indent=2)

    # 8. Evaluation report
    eval_report = {
        "pipeline": "product_and_category_sales_forecasting",
        "strategy": "Global Models trained on Dev Companies 1 & 2 with zero-shot holdout evaluation on Company 3",
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "selected_model": best_name,
        "selection_metric": "val_wape",
        "candidates": {
            k: {
                "val_metrics": v["val_metrics"],
                "test_metrics": v["test_metrics"],
            }
            for k, v in candidates.items()
        },
        "category_model_metrics": {
            "val_metrics": cat_val_metrics,
            "test_metrics": cat_test_metrics,
            "holdout_co3_metrics": cat_co3_metrics
        },
        "approach_c_holdout_co3": {
            "business_id": "00000000-0000-0000-0000-000000000003",
            "business_name": "Apna Kirana Store",
            "metrics": holdout_metrics
        }
    }
    with open(REPORTS_DIR / "sales_forecasting_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    logger.info("Product & Category Sales Forecasting Pipeline completed successfully.")
    return eval_report


if __name__ == "__main__":
    run_pipeline()

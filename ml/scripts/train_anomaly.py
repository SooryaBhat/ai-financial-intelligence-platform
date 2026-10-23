# -*- coding: utf-8 -*-
"""
train_anomaly.py
================
Train, compare, and evaluate unsupervised and statistical anomaly detection models (Approach C).

Features used (strictly excluding ground-truth anomaly labels):
- net_amount, discount_pct, day_of_week, is_weekend, month,
  status_enc, roll28_mean, roll28_std, amount_z_rolling

Candidate models:
- Statistical Z-Score Baseline (|z| > 3.0)
- Statistical IQR Baseline (1.5 * IQR)
- Isolation Forest (novelty detection with StandardScaler)
- Local Outlier Factor (LOF with novelty=True)

Evaluation:
- Evaluated against synthetic ground-truth is_anomaly labels (Precision, Recall, F1, PR-AUC).
- Approach C Business Holdout on Company 3 (Apna Kirana).

Outputs:
- ml/models/anomaly_detection_isolation_forest.pkl
- ml/models/anomaly_detection_lof_config.json
- ml/reports/anomaly_detection_eval.json
- ml/reports/detected_anomalies.csv

Usage:
    python ml/scripts/train_anomaly.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, save_model,
    MODELS_DIR, REPORTS_DIR, PROCESSED_DIR
)

logger = get_logger(__name__)

FEATURE_COLS = [
    "net_amount", "discount_pct", "day_of_week", "is_weekend",
    "month", "status_enc", "roll28_mean", "roll28_std", "amount_z_rolling"
]


DEV_COMPANIES = ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"]
HOLDOUT_COMPANY = "00000000-0000-0000-0000-000000000003"


def load_and_split_anomaly_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load anomaly features and split strictly: Dev (Companies 1 & 2) vs Holdout (Company 3)."""
    df = load_csv("anomaly_features.csv", PROCESSED_DIR)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df = df.sort_values(["company_id", "sale_date"]).reset_index(drop=True)

    # Convert is_anomaly to integer (0 or 1)
    df["is_anomaly_int"] = df["is_anomaly"].astype(bool).astype(int)

    # Dev split: strictly Companies 1 and 2
    dev_df = df[df["company_id"].isin(DEV_COMPANIES)].copy()

    # Chronological splits within Dev
    train_mask = (dev_df["sale_date"] <= "2023-12-31")
    val_mask = (dev_df["sale_date"] >= "2024-01-01") & (dev_df["sale_date"] <= "2024-06-30")
    test_mask = (dev_df["sale_date"] >= "2024-07-01")

    train_df = dev_df[train_mask].copy()
    val_df = dev_df[val_mask].copy()
    test_df = dev_df[test_mask].copy()

    # Company 3 holdout (Apna Kirana)
    holdout_co3_df = df[df["company_id"] == HOLDOUT_COMPANY].copy()

    # Verify zero leakage
    assert (train_df["company_id"] == HOLDOUT_COMPANY).sum() == 0, "Leakage: Company 3 found in training set!"
    assert (val_df["company_id"] == HOLDOUT_COMPANY).sum() == 0, "Leakage: Company 3 found in validation set!"
    assert (test_df["company_id"] == HOLDOUT_COMPANY).sum() == 0, "Leakage: Company 3 found in dev test set!"

    return train_df, val_df, test_df, holdout_co3_df


def compute_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_scores: np.ndarray = None) -> Dict[str, float]:
    """Compute precision, recall, F1, and AUC metrics."""
    p = float(precision_score(y_true, y_pred, zero_division=0))
    r = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    metrics = {
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1_score": round(f1, 4),
        "total_anomalies_actual": int(np.sum(y_true)),
        "total_anomalies_flagged": int(np.sum(y_pred)),
    }

    if y_scores is not None and len(np.unique(y_true)) > 1:
        try:
            metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_scores)), 4)
            metrics["pr_auc"] = round(float(average_precision_score(y_true, y_scores)), 4)
        except Exception:
            metrics["roc_auc"] = 0.5
            metrics["pr_auc"] = 0.0

    return metrics


def train_and_evaluate_candidates(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    holdout_co3_df: pd.DataFrame,
) -> Tuple[Dict[str, Any], str, Any, StandardScaler, Dict[str, Any], Any]:
    """Train and evaluate statistical, tree-based, and density-based anomaly detectors strictly on Dev."""
    X_train_raw = train_df[FEATURE_COLS].values
    X_val_raw = val_df[FEATURE_COLS].values
    X_test_raw = test_df[FEATURE_COLS].values
    X_holdout_raw = holdout_co3_df[FEATURE_COLS].values

    y_val = val_df["is_anomaly_int"].values
    y_test = test_df["is_anomaly_int"].values
    y_holdout = holdout_co3_df["is_anomaly_int"].values

    # Fit StandardScaler strictly on Dev train split only
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_raw)
    X_val_scaled = scaler.transform(X_val_raw)
    X_test_scaled = scaler.transform(X_test_raw)
    X_holdout_scaled = scaler.transform(X_holdout_raw)

    candidates = {}

    # 1. Statistical Z-Score Baseline (|z| > 3.0 on amount_z_rolling)
    z_val = np.abs(val_df["amount_z_rolling"].values)
    z_test = np.abs(test_df["amount_z_rolling"].values)
    val_pred_z = (z_val > 3.0).astype(int)
    test_pred_z = (z_test > 3.0).astype(int)
    candidates["Statistical_ZScore"] = {
        "val_metrics": compute_classification_metrics(y_val, val_pred_z, z_val),
        "test_metrics": compute_classification_metrics(y_test, test_pred_z, z_test),
        "model": None,
    }

    # 2. Statistical IQR Baseline (1.5 * IQR on net_amount)
    q25 = np.percentile(train_df["net_amount"], 25)
    q75 = np.percentile(train_df["net_amount"], 75)
    iqr = q75 - q25
    upper_bound = q75 + 1.5 * iqr
    lower_bound = max(0, q25 - 1.5 * iqr)

    val_pred_iqr = ((val_df["net_amount"] > upper_bound) | (val_df["net_amount"] < lower_bound)).astype(int).values
    test_pred_iqr = ((test_df["net_amount"] > upper_bound) | (test_df["net_amount"] < lower_bound)).astype(int).values
    candidates["Statistical_IQR"] = {
        "val_metrics": compute_classification_metrics(y_val, val_pred_iqr),
        "test_metrics": compute_classification_metrics(y_test, test_pred_iqr),
        "model": None,
    }

    # 3. Isolation Forest
    contamination_rate = 0.015
    if_model = IsolationForest(
        n_estimators=200,
        contamination=contamination_rate,
        max_samples="auto",
        random_state=42,
        n_jobs=-1
    )
    if_model.fit(X_train_scaled)

    # predict: -1 is anomaly, 1 is normal -> map -1 to 1, 1 to 0
    val_pred_if = (if_model.predict(X_val_scaled) == -1).astype(int)
    test_pred_if = (if_model.predict(X_test_scaled) == -1).astype(int)
    # decision_function: lower score = more anomalous -> negate for ranking
    val_scores_if = -if_model.decision_function(X_val_scaled)
    test_scores_if = -if_model.decision_function(X_test_scaled)

    candidates["Isolation_Forest"] = {
        "val_metrics": compute_classification_metrics(y_val, val_pred_if, val_scores_if),
        "test_metrics": compute_classification_metrics(y_test, test_pred_if, test_scores_if),
        "model": if_model,
    }

    # 4. Local Outlier Factor (novelty=True)
    lof_model = LocalOutlierFactor(
        n_neighbors=25,
        contamination=contamination_rate,
        novelty=True,
        n_jobs=-1
    )
    lof_model.fit(X_train_scaled)

    val_pred_lof = (lof_model.predict(X_val_scaled) == -1).astype(int)
    test_pred_lof = (lof_model.predict(X_test_scaled) == -1).astype(int)
    val_scores_lof = -lof_model.decision_function(X_val_scaled)
    test_scores_lof = -lof_model.decision_function(X_test_scaled)

    candidates["Local_Outlier_Factor"] = {
        "val_metrics": compute_classification_metrics(y_val, val_pred_lof, val_scores_lof),
        "test_metrics": compute_classification_metrics(y_test, test_pred_lof, test_scores_lof),
        "model": lof_model,
    }

    # Model Selection: best F1 score on Dev validation set
    trained = {k: v for k, v in candidates.items() if v["model"] is not None}
    best_name = max(trained, key=lambda k: trained[k]["val_metrics"]["f1_score"])
    best_model = trained[best_name]["model"]

    # True Zero-Shot Holdout Evaluation on Company 3 using the frozen fitted model & scaler
    if len(holdout_co3_df) > 0:
        h_pred = (best_model.predict(X_holdout_scaled) == -1).astype(int)
        h_scores = -best_model.decision_function(X_holdout_scaled)
        holdout_metrics = compute_classification_metrics(y_holdout, h_pred, h_scores)

        # Baseline predictions on Company 3
        z_co3 = np.abs(holdout_co3_df["amount_z_rolling"].values)
        pred_z_co3 = (z_co3 > 3.0).astype(int)
        pred_iqr_co3 = ((holdout_co3_df["net_amount"] > upper_bound) | (holdout_co3_df["net_amount"] < lower_bound)).astype(int).values
        holdout_metrics["baseline_zscore_metrics"] = compute_classification_metrics(y_holdout, pred_z_co3, z_co3)
        holdout_metrics["baseline_iqr_metrics"] = compute_classification_metrics(y_holdout, pred_iqr_co3)
        holdout_metrics["n_observations"] = len(holdout_co3_df)
    else:
        holdout_metrics = {}

    return candidates, best_name, if_model, scaler, holdout_metrics, lof_model


def run_pipeline() -> Dict[str, Any]:
    """Execute anomaly detection training and evaluation pipeline."""
    logger.info("Starting Anomaly Detection Pipeline...")

    train_df, val_df, test_df, holdout_co3_df = load_and_split_anomaly_data()
    logger.info(f"Anomaly splits - Train: {train_df.shape}, Val: {val_df.shape}, Test: {test_df.shape}, Holdout Co3: {holdout_co3_df.shape}")

    candidates, best_name, if_model, scaler, holdout_metrics, lof_model = train_and_evaluate_candidates(
        train_df, val_df, test_df, holdout_co3_df
    )

    logger.info(f"Selected Anomaly Model: {best_name}")
    for name, data in candidates.items():
        vm = data["val_metrics"]
        tm = data["test_metrics"]
        logger.info(
            f"Candidate: {name:<22} | Val F1: {vm.get('f1_score', 0):.4f} (P: {vm.get('precision', 0):.2f}, R: {vm.get('recall', 0):.2f}) | "
            f"Test F1: {tm.get('f1_score', 0):.4f} (P: {tm.get('precision', 0):.2f}, R: {tm.get('recall', 0):.2f}) | "
            f"PR-AUC: {tm.get('pr_auc', 0):.4f}"
        )

    logger.info(f"Approach C Holdout Co3 Test F1: {holdout_metrics.get('f1_score', 0):.4f} | Recall: {holdout_metrics.get('recall', 0):.4f}")

    # Generate detected anomalies table for inspection
    all_df = pd.concat([train_df, val_df, test_df]).reset_index(drop=True)
    X_all_scaled = scaler.transform(all_df[FEATURE_COLS].values)
    all_df["pred_anomaly"] = (if_model.predict(X_all_scaled) == -1).astype(int)
    all_df["anomaly_score"] = np.round(-if_model.decision_function(X_all_scaled), 4)

    detected_anomalies = all_df[all_df["pred_anomaly"] == 1][[
        "id", "company_id", "sale_date", "net_amount", "discount_pct",
        "roll28_mean", "roll28_std", "amount_z_rolling", "anomaly_score", "is_anomaly"
    ]].sort_values("anomaly_score", ascending=False).reset_index(drop=True)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    detected_path = REPORTS_DIR / "detected_anomalies.csv"
    detected_anomalies.to_csv(detected_path, index=False)
    logger.info(f"Saved {len(detected_anomalies)} detected transaction anomalies to {detected_path}")

    # Save artifacts for backend compatibility:
    # 1. anomaly_detection_isolation_forest.pkl (must wrap model, scaler, and feature_cols)
    save_model(
        {
            "model": if_model,
            "scaler": scaler,
            "feature_cols": FEATURE_COLS,
            "selected_model": best_name,
            "training_companies": DEV_COMPANIES,
            "holdout_company": HOLDOUT_COMPANY
        },
        "anomaly_detection_isolation_forest.pkl",
        MODELS_DIR
    )

    # 2. anomaly_detection_lof_config.json
    lof_config = {
        "algorithm": "LocalOutlierFactor",
        "n_neighbors": 25,
        "contamination": 0.015,
        "novelty": True,
        "features": FEATURE_COLS,
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "test_metrics": candidates["Local_Outlier_Factor"]["test_metrics"],
        "disclaimer": "Unsupervised anomaly detection flags statistical transaction outliers. It is not an absolute fraud determination."
    }
    with open(MODELS_DIR / "anomaly_detection_lof_config.json", "w", encoding="utf-8") as f:
        json.dump(lof_config, f, indent=2)

    # 3. ml/reports/anomaly_detection_eval.json
    eval_report = {
        "pipeline": "transaction_anomaly_detection",
        "selected_model": best_name,
        "selection_metric": "val_f1_score",
        "training_companies": DEV_COMPANIES,
        "holdout_company": HOLDOUT_COMPANY,
        "features": FEATURE_COLS,
        "disclaimer": "Flagged outliers represent statistical deviations in amount, frequency, discount or timing; not proof of fraud.",
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
    with open(REPORTS_DIR / "anomaly_detection_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    logger.info("Anomaly Detection Pipeline completed successfully.")
    return eval_report


if __name__ == "__main__":
    run_pipeline()

"""
evaluate.py
===========
Model evaluation pipeline for all trained models.

Computes and reports performance metrics for regression, classification,
and anomaly detection models, and saves reports to reports/ directory.

Usage:
    python scripts/evaluate.py --model revenue_xgboost --task revenue
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_model, compute_metrics,
    MODELS_DIR, REPORTS_DIR, PROCESSED_DIR
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Regression evaluation
# ---------------------------------------------------------------------------

def evaluate_regression(
    model: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
    task_name: str,
) -> Dict[str, Any]:
    """
    Evaluate a regression model and produce a metrics report.

    Metrics computed:
    - RMSE (Root Mean Squared Error)
    - MAE (Mean Absolute Error)
    - MAPE (Mean Absolute Percentage Error)
    - R² (Coefficient of Determination)

    Args:
        model:      Trained regression model with a .predict() method.
        X_test:     Test feature matrix.
        y_test:     True target values.
        model_name: Display name for the model (e.g., 'XGBoost').
        task_name:  Task identifier (e.g., 'revenue_forecasting').

    Returns:
        Evaluation report dict.
    """
    # TODO: Implement regression evaluation
    logger.info(f"Evaluating {model_name} on task: {task_name}...")

    # TODO: y_pred = model.predict(X_test)
    # TODO: metrics = compute_metrics(y_test.values, y_pred)

    report = {
        "model":      model_name,
        "task":       task_name,
        "evaluated_at": datetime.now().isoformat(),
        "n_samples":  len(y_test),
        "metrics": {
            # TODO: Populate with actual metrics
        },
    }

    return report


def evaluate_all_regression_models(
    task_name: str,
    models: Dict[str, Any],
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> List[Dict[str, Any]]:
    """
    Evaluate multiple regression models on the same test set and compare.

    Args:
        task_name: Task identifier.
        models:    Dict of {model_name: model_object}.
        X_test:    Test feature matrix.
        y_test:    True target values.

    Returns:
        List of evaluation report dicts, sorted by RMSE ascending.
    """
    # TODO: Evaluate each model, collect reports, sort by RMSE
    reports = []
    for model_name, model in models.items():
        report = evaluate_regression(model, X_test, y_test, model_name, task_name)
        reports.append(report)

    # TODO: Sort reports by metrics.rmse
    return reports


# ---------------------------------------------------------------------------
# Classification evaluation
# ---------------------------------------------------------------------------

def evaluate_classification(
    model: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
    task_name: str,
    class_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Evaluate a classification model.

    Metrics computed:
    - Accuracy
    - F1 Score (macro)
    - Precision (macro)
    - Recall (macro)
    - AUC-ROC (if binary)
    - Confusion matrix

    Args:
        model:        Trained classification model.
        X_test:       Test feature matrix.
        y_test:       True labels.
        model_name:   Display name.
        task_name:    Task identifier.
        class_labels: Optional list of class label names.

    Returns:
        Evaluation report dict.
    """
    # TODO: Implement classification evaluation
    # from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
    logger.info(f"Evaluating classifier {model_name} on task: {task_name}...")

    report = {
        "model":        model_name,
        "task":         task_name,
        "evaluated_at": datetime.now().isoformat(),
        "n_samples":    len(y_test),
        "metrics": {
            # TODO: Populate with actual metrics
        },
    }

    return report


# ---------------------------------------------------------------------------
# Anomaly detection evaluation
# ---------------------------------------------------------------------------

def evaluate_anomaly_detector(
    model: Any,
    X_test: pd.DataFrame,
    y_true_anomaly: Optional[pd.Series],
    model_name: str,
    k: int = 50,
) -> Dict[str, Any]:
    """
    Evaluate an anomaly detection model.

    If ground truth labels are available (y_true_anomaly), compute:
    - Precision@k, Recall@k
    - AUC-ROC on anomaly scores

    If no labels, report:
    - Number of flagged anomalies
    - Anomaly score distribution statistics

    Args:
        model:          Trained anomaly detection model.
        X_test:         Test feature matrix.
        y_true_anomaly: Binary ground-truth anomaly labels (1=anomaly, 0=normal).
                        Pass None if not available.
        model_name:     Display name.
        k:              Top-k threshold for precision/recall.

    Returns:
        Evaluation report dict.
    """
    # TODO: Implement anomaly detection evaluation
    logger.info(f"Evaluating anomaly detector {model_name}...")

    report = {
        "model":        model_name,
        "task":         "anomaly_detection",
        "evaluated_at": datetime.now().isoformat(),
        "n_samples":    len(X_test),
        "metrics": {
            # TODO: Populate
        },
    }

    return report


# ---------------------------------------------------------------------------
# Report I/O
# ---------------------------------------------------------------------------

def save_report(report: Dict, name: str) -> Path:
    """
    Save an evaluation report to the reports/ directory as JSON.

    Args:
        report: Report dict to save.
        name:   Report filename (without extension).

    Returns:
        Path to saved report.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"{name}_{timestamp}.json"

    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Report saved: {path}")
    return path


def load_all_reports() -> List[Dict]:
    """
    Load all evaluation reports from the reports/ directory.

    Returns:
        List of report dicts.
    """
    # TODO: Load all JSON files from REPORTS_DIR
    reports = []
    for json_file in REPORTS_DIR.glob("*.json"):
        with open(json_file) as f:
            reports.append(json.load(f))
    return reports


def compare_models(reports: List[Dict]) -> pd.DataFrame:
    """
    Build a comparison table from a list of evaluation reports.

    Args:
        reports: List of report dicts from save_report.

    Returns:
        Comparison DataFrame with columns: model, task, rmse, mae, mape, r2.
    """
    # TODO: Extract metrics from each report and build a tidy DataFrame
    rows = []
    for r in reports:
        row = {
            "model": r.get("model"),
            "task":  r.get("task"),
            **r.get("metrics", {}),
        }
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained ML model.")
    parser.add_argument("--model", type=str, required=True, help="Model filename in models/")
    parser.add_argument("--task",  type=str, required=True,
                        help="Task name: revenue | sales | inventory | profit | expenses | anomaly")
    parser.add_argument("--data",  type=str, default=None,
                        help="Test dataset CSV (default: use processed/ data)")
    args = parser.parse_args()

    # TODO: Load model, load test data, run appropriate evaluator
    logger.info(f"Evaluating model '{args.model}' on task '{args.task}'...")
    logger.info("Evaluation not yet implemented.")


if __name__ == "__main__":
    main()

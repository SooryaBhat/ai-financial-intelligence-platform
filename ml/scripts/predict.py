"""
predict.py
==========
Inference script — run predictions using trained ML models.

Loads a trained model artifact and generates predictions for
a given input dataset or single inference request.

Usage:
    python scripts/predict.py --task revenue --horizon 3
    python scripts/predict.py --task anomaly --input /path/to/data.csv
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_model, load_csv,
    MODELS_DIR, PROCESSED_DIR
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

def load_model_registry() -> Dict[str, str]:
    """
    Load the model registry JSON that maps task names to model file paths.

    The registry is stored at models/model_registry.json.
    It is populated by notebook 10 (model_comparison.ipynb).

    Returns:
        Dict mapping task names to model file paths.
        Example: {"revenue": "models/revenue_xgboost_20240601.pkl"}
    """
    registry_path = MODELS_DIR / "model_registry.json"

    if not registry_path.exists():
        logger.warning("model_registry.json not found. No models are registered yet.")
        return {}

    with open(registry_path) as f:
        registry = json.load(f)

    logger.info(f"Loaded model registry with {len(registry)} entries.")
    return registry


def get_model_for_task(task: str) -> Any:
    """
    Load the best production model for a given task from the registry.

    Args:
        task: Task name (e.g., 'revenue', 'sales', 'anomaly').

    Returns:
        Loaded model object.

    Raises:
        KeyError: If task is not in the model registry.
        FileNotFoundError: If the model file does not exist.
    """
    # TODO: Load from model registry
    registry = load_model_registry()
    if task not in registry:
        raise KeyError(f"No model registered for task '{task}'. Train a model first.")

    model_path = MODELS_DIR / registry[task]
    return load_model(model_path)


# ---------------------------------------------------------------------------
# Prediction functions
# ---------------------------------------------------------------------------

def predict_revenue(
    model: Any,
    company_id: str,
    horizon_months: int = 3,
    as_of_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Generate a revenue forecast for a company over the next N months.

    Args:
        model:          Trained revenue forecasting model.
        company_id:     Company UUID to forecast for.
        horizon_months: Number of future months to forecast.
        as_of_date:     Date to start forecast from (defaults to today).

    Returns:
        DataFrame with columns: period, predicted_revenue, lower_bound, upper_bound.
    """
    # TODO: Build feature vector for forecast horizon
    # TODO: Call model.predict()
    # TODO: Construct forecast DataFrame with confidence intervals
    logger.info(f"Predicting revenue for company {company_id}, horizon={horizon_months}m")
    raise NotImplementedError("Revenue prediction not yet implemented.")


def predict_sales(
    model: Any,
    company_id: str,
    product_ids: Optional[List[str]] = None,
    horizon_months: int = 3,
) -> pd.DataFrame:
    """
    Generate a sales forecast per product for the next N months.

    Args:
        model:          Trained sales forecasting model.
        company_id:     Company UUID.
        product_ids:    List of product UUIDs to forecast (all if None).
        horizon_months: Number of future months to forecast.

    Returns:
        DataFrame with columns: product_id, period, predicted_units, predicted_revenue.
    """
    # TODO: Build feature vectors per product
    # TODO: Call model.predict()
    logger.info(f"Predicting sales for company {company_id}, {horizon_months}m horizon")
    raise NotImplementedError("Sales prediction not yet implemented.")


def predict_inventory(
    model: Any,
    company_id: str,
    warehouse_id: Optional[str] = None,
    horizon_days: int = 30,
) -> pd.DataFrame:
    """
    Predict inventory demand and flag reorder needs.

    Args:
        model:         Trained inventory demand model.
        company_id:    Company UUID.
        warehouse_id:  Specific warehouse UUID (all if None).
        horizon_days:  Forecast window in days.

    Returns:
        DataFrame with columns: product_id, warehouse_id, days_remaining,
        reorder_flag, predicted_demand, recommended_reorder_qty.
    """
    # TODO: Compute days_remaining = quantity_on_hand / daily_consumption
    # TODO: Call model.predict() for demand
    logger.info(f"Predicting inventory demand for company {company_id}")
    raise NotImplementedError("Inventory prediction not yet implemented.")


def predict_profit(
    model: Any,
    company_id: str,
    horizon_months: int = 3,
) -> pd.DataFrame:
    """
    Forecast net profit for the next N months.

    Args:
        model:          Trained profit prediction model.
        company_id:     Company UUID.
        horizon_months: Number of future months to forecast.

    Returns:
        DataFrame with columns: period, predicted_gross_profit, predicted_net_profit,
        predicted_profit_margin_pct.
    """
    # TODO: Build feature vectors
    # TODO: Call model.predict()
    logger.info(f"Predicting profit for company {company_id}")
    raise NotImplementedError("Profit prediction not yet implemented.")


def predict_expenses(
    model: Any,
    company_id: str,
    horizon_months: int = 3,
) -> pd.DataFrame:
    """
    Forecast operating expenses for the next N months.

    Args:
        model:          Trained expense prediction model.
        company_id:     Company UUID.
        horizon_months: Forecast horizon.

    Returns:
        DataFrame with columns: period, category, predicted_amount.
    """
    # TODO: Predict per expense category
    logger.info(f"Predicting expenses for company {company_id}")
    raise NotImplementedError("Expense prediction not yet implemented.")


def score_business_health(
    model: Any,
    company_id: str,
    as_of_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute the business health score for a company.

    Args:
        model:       Business health scoring model / pipeline.
        company_id:  Company UUID.
        as_of_date:  Date for snapshot (defaults to latest available data).

    Returns:
        Dict with:
        - health_score (0–100)
        - component_scores (dict of individual KPI scores)
        - grade ('A', 'B', 'C', 'D', 'F')
        - recommendations (list of strings)
    """
    # TODO: Compute KPIs from latest data
    # TODO: Apply health scoring model
    # TODO: Map score to grade and generate recommendations
    logger.info(f"Scoring business health for company {company_id}")
    raise NotImplementedError("Health scoring not yet implemented.")


def detect_anomalies(
    model: Any,
    transactions_df: pd.DataFrame,
    threshold: float = -0.5,
) -> pd.DataFrame:
    """
    Run anomaly detection on a transactions DataFrame.

    Args:
        model:          Trained anomaly detection model (IsolationForest / LOF).
        transactions_df: DataFrame of transactions with pre-engineered features.
        threshold:      Anomaly score threshold (lower = more anomalous for sklearn).

    Returns:
        transactions_df with added columns:
        - anomaly_score (raw model score)
        - is_anomaly (bool: True if flagged)
        - anomaly_reason (heuristic explanation string)
    """
    # TODO: Call model.decision_function() or model.score_samples()
    # TODO: Apply threshold to flag anomalies
    # TODO: Generate human-readable explanations
    logger.info(f"Running anomaly detection on {len(transactions_df)} records")
    raise NotImplementedError("Anomaly detection not yet implemented.")


# ---------------------------------------------------------------------------
# Batch inference
# ---------------------------------------------------------------------------

def run_batch_inference(
    task: str,
    company_id: str,
    horizon: int = 3,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Run batch inference for a given task and save output to CSV.

    Args:
        task:        Task name: 'revenue' | 'sales' | 'inventory' | 'profit' | 'expenses' | 'anomaly'.
        company_id:  Company UUID.
        horizon:     Forecast horizon (months for revenue/sales/profit/expenses, days for inventory).
        output_path: Optional path to save the output CSV.

    Returns:
        Predictions DataFrame.
    """
    logger.info(f"Running batch inference: task={task}, company={company_id}, horizon={horizon}")

    task_functions = {
        "revenue":   predict_revenue,
        "sales":     predict_sales,
        "inventory": predict_inventory,
        "profit":    predict_profit,
        "expenses":  predict_expenses,
    }

    if task not in task_functions:
        raise ValueError(f"Unknown task '{task}'. Choose from: {list(task_functions.keys())}")

    model    = get_model_for_task(task)
    pred_fn  = task_functions[task]
    # TODO: Call pred_fn(model, company_id, horizon)
    # TODO: Save to output_path if specified

    raise NotImplementedError(f"Batch inference for task '{task}' not yet implemented.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run ML model inference.")
    parser.add_argument(
        "--task", type=str, required=True,
        choices=["revenue", "sales", "inventory", "profit", "expenses", "anomaly"],
        help="Prediction task to run."
    )
    parser.add_argument(
        "--company", type=str, required=True,
        help="Company UUID to generate predictions for."
    )
    parser.add_argument(
        "--horizon", type=int, default=3,
        help="Forecast horizon (months or days depending on task)."
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output CSV path for predictions."
    )
    args = parser.parse_args()

    output = Path(args.output) if args.output else None
    run_batch_inference(args.task, args.company, args.horizon, output)


if __name__ == "__main__":
    main()

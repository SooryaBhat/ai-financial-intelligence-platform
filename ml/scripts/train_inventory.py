"""
train_inventory.py
==================
Train inventory demand prediction models.

Models supported:
- XGBoost Regressor (primary)
- Simple Exponential Smoothing (baseline)
- Moving Average baseline

Usage:
    python scripts/train_inventory.py --model xgboost
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import get_logger, load_csv, save_model, compute_metrics, PROCESSED_DIR

logger = get_logger(__name__)


def load_inventory_data() -> pd.DataFrame:
    """
    Load and join inventory, stock_movements, and sales data.

    Computes:
    - Historical daily/weekly demand per product per warehouse
    - Average consumption rate

    Returns:
        Feature DataFrame for demand prediction.
    """
    # TODO: Load inventory.csv, stock_movements.csv, sale_items.csv
    # TODO: Compute avg_daily_out (mean outbound movement per day)
    # TODO: Join with inventory to get current stock levels
    raise NotImplementedError("load_inventory_data not implemented.")


def compute_days_remaining(inventory_df: pd.DataFrame, movements_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute days of stock remaining per product per warehouse.

    Formula:
        days_remaining = quantity_on_hand / avg_daily_consumption

    Args:
        inventory_df: Current inventory levels.
        movements_df: Historical stock movements.

    Returns:
        DataFrame with days_remaining and reorder_flag columns.
    """
    # TODO: Compute avg_daily_consumption from outbound movements (last 30 days)
    # TODO: Compute days_remaining = quantity_on_hand / avg_daily_consumption
    # TODO: reorder_flag = days_remaining <= 7
    raise NotImplementedError("compute_days_remaining not implemented.")


def train_xgboost_inventory(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Optional[Dict] = None,
) -> Any:
    """
    Train XGBoost demand predictor for inventory.

    Args:
        X_train: Feature matrix (lag demand, price, season, etc.).
        y_train: Weekly/daily demand quantity.
        params:  Hyperparameter overrides.

    Returns:
        Trained XGBRegressor.
    """
    # TODO: from xgboost import XGBRegressor; train and return
    raise NotImplementedError("XGBoost inventory training not implemented.")


def train_exponential_smoothing(
    series: pd.Series,
    smoothing_level: float = 0.3,
) -> Any:
    """
    Train a Simple Exponential Smoothing model as a baseline.

    Args:
        series:          Time-series of historical demand values.
        smoothing_level: Alpha parameter (0 < alpha < 1).

    Returns:
        Fitted ExponentialSmoothing model.
    """
    # TODO: from statsmodels.tsa.holtwinters import ExponentialSmoothing
    # TODO: Fit and return model
    raise NotImplementedError("Exponential smoothing training not implemented.")


def run_training_pipeline(
    model_type: str = "xgboost",
    company_id: Optional[str] = None,
    save: bool = True,
) -> Any:
    """
    Full inventory training pipeline.

    Args:
        model_type: 'xgboost' | 'exponential_smoothing' | 'moving_average'.
        company_id: Filter to one company (all if None).
        save:       Whether to save the model artifact.

    Returns:
        Trained model.
    """
    logger.info(f"Inventory training: model={model_type}")
    # TODO: Load → feature engineering → split → train → evaluate → save
    raise NotImplementedError("Inventory training pipeline not implemented.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train inventory demand model.")
    parser.add_argument("--model",   type=str, default="xgboost",
                        choices=["xgboost", "exponential_smoothing", "moving_average"])
    parser.add_argument("--company", type=str, default=None)
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    run_training_pipeline(args.model, args.company, not args.no_save)


if __name__ == "__main__":
    main()

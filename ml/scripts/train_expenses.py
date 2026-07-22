"""
train_expenses.py
=================
Train expense prediction models per category and branch.

Supported models:
- Linear Regression (baseline)
- XGBoost Regressor
- SARIMA (for fixed recurring categories)

Usage:
    python scripts/train_expenses.py --model xgboost
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import get_logger, load_csv, save_model, compute_metrics, PROCESSED_DIR

logger = get_logger(__name__)

EXPENSE_CATEGORIES = [
    "Rent", "Salaries", "Utilities", "Marketing", "Logistics",
    "Office Supplies", "IT & Software", "Travel", "Maintenance", "Insurance",
]


def load_expense_data(
    company_id: Optional[str] = None,
    category: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load and aggregate approved expenses per month per category.

    Args:
        company_id: Filter to one company (all if None).
        category:   Filter to one expense category (all if None).

    Returns:
        Monthly expense DataFrame with columns:
        company_id, branch_id, category, period, total_amount.
    """
    # TODO: Load expenses_clean.csv from processed/
    # TODO: Filter status == 'approved'
    # TODO: Group by company_id + branch_id + category + period
    # TODO: Sum amount
    raise NotImplementedError("load_expense_data not implemented.")


def train_linear_regression_expenses(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> Any:
    """
    Train a simple linear regression model as an expense baseline.

    Args:
        X_train: Feature matrix.
        y_train: Target (expense amount).

    Returns:
        Trained LinearRegression model.
    """
    # TODO: from sklearn.linear_model import LinearRegression
    # TODO: model = LinearRegression(); model.fit(X_train, y_train); return model
    raise NotImplementedError("Linear regression expense training not implemented.")


def train_xgboost_expenses(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Optional[Dict] = None,
) -> Any:
    """
    Train XGBoost regressor for expense prediction.

    Args:
        X_train: Feature matrix (lag expenses, category encoded, date features).
        y_train: Target expense amount.
        params:  Hyperparameter overrides.

    Returns:
        Trained XGBRegressor.
    """
    # TODO: from xgboost import XGBRegressor; initialize, fit, return
    raise NotImplementedError("XGBoost expense training not implemented.")


def train_sarima_expenses(
    series: pd.Series,
    order: Tuple = (1, 1, 1),
    seasonal_order: Tuple = (1, 1, 0, 12),
) -> Any:
    """
    Train SARIMA model for a single expense category time series.

    Best suited for fixed recurring expenses like Rent and Salaries.

    Args:
        series:         Monthly expense time series (pd.Series indexed by period).
        order:          ARIMA (p, d, q) order.
        seasonal_order: Seasonal (P, D, Q, s) order.

    Returns:
        Fitted SARIMAX model results.
    """
    # TODO: from statsmodels.tsa.statespace.sarimax import SARIMAX
    # TODO: model = SARIMAX(series, order=order, seasonal_order=seasonal_order)
    # TODO: result = model.fit(disp=False); return result
    raise NotImplementedError("SARIMA expense training not implemented.")


def run_training_pipeline(
    model_type: str = "xgboost",
    company_id: Optional[str] = None,
    category: Optional[str] = None,
    save: bool = True,
) -> Any:
    """
    Full expense prediction training pipeline.

    Args:
        model_type: 'linear' | 'xgboost' | 'sarima'.
        company_id: Filter to one company (all if None).
        category:   Specific expense category to train for (all if None).
        save:       Whether to save model artifact.

    Returns:
        Trained model or dict of models (one per category for SARIMA).
    """
    logger.info(f"Expense training: model={model_type}, category={category or 'ALL'}")
    # TODO: Load → feature engineering → split → train → evaluate → save
    raise NotImplementedError("Expense training pipeline not implemented.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train expense prediction model.")
    parser.add_argument("--model",    type=str, default="xgboost",
                        choices=["linear", "xgboost", "sarima"])
    parser.add_argument("--company",  type=str, default=None)
    parser.add_argument("--category", type=str, default=None, choices=EXPENSE_CATEGORIES + [None])
    parser.add_argument("--no-save",  action="store_true")
    args = parser.parse_args()

    run_training_pipeline(args.model, args.company, args.category, not args.no_save)


if __name__ == "__main__":
    main()

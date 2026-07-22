"""
train_revenue.py
================
Train revenue forecasting models for the AI Financial Intelligence Platform.

Supported models:
- Prophet (Facebook / Meta)
- SARIMA / SARIMAX (statsmodels)
- XGBoost Regressor with time-series features
- LightGBM Regressor with time-series features

Usage:
    python scripts/train_revenue.py --model xgboost --company <uuid>
    python scripts/train_revenue.py --model prophet --all-companies
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, save_model, compute_metrics,
    PROCESSED_DIR, MODELS_DIR
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------

def load_revenue_data(company_id: Optional[str] = None) -> pd.DataFrame:
    """
    Load and aggregate processed sales data into monthly revenue per company.

    Args:
        company_id: Filter to a specific company UUID. If None, load all.

    Returns:
        Monthly revenue DataFrame with columns:
        company_id, period (YYYY-MM), revenue.
    """
    # TODO: Load sales_clean.csv from processed/
    # TODO: Parse sale_date, group by company + month, sum net_amount
    # TODO: Filter by company_id if specified
    # TODO: Sort by period ascending
    raise NotImplementedError("load_revenue_data not implemented.")


def prepare_train_test(
    df: pd.DataFrame,
    target_col: str = "revenue",
    test_size: float = 0.2,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split a revenue DataFrame into train/test sets (chronological split).

    Args:
        df:         Monthly revenue DataFrame with lag features.
        target_col: Name of the target column.
        test_size:  Fraction of data to use for testing (0.0–1.0).

    Returns:
        Tuple of (X_train, X_test, y_train, y_test).
    """
    # TODO: Sort by period, split at cutoff index
    # TODO: Separate features (X) from target (y)
    # TODO: Drop NaN rows introduced by lag features
    raise NotImplementedError("prepare_train_test not implemented.")


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

def train_xgboost_revenue(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Optional[Dict] = None,
) -> Any:
    """
    Train an XGBoost regressor for revenue forecasting.

    Default hyperparameters:
    - n_estimators: 300
    - max_depth: 5
    - learning_rate: 0.05
    - subsample: 0.8
    - colsample_bytree: 0.8
    - early_stopping_rounds: 20

    Args:
        X_train: Training feature matrix.
        y_train: Training target values.
        params:  Optional dict to override default hyperparameters.

    Returns:
        Trained XGBRegressor model.
    """
    # TODO: from xgboost import XGBRegressor
    # TODO: model = XGBRegressor(**{**default_params, **(params or {})})
    # TODO: model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=50)
    raise NotImplementedError("XGBoost revenue training not implemented.")


def train_lightgbm_revenue(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Optional[Dict] = None,
) -> Any:
    """
    Train a LightGBM regressor for revenue forecasting.

    Args:
        X_train: Training feature matrix.
        y_train: Training target values.
        params:  Optional hyperparameter overrides.

    Returns:
        Trained LGBMRegressor model.
    """
    # TODO: from lightgbm import LGBMRegressor
    # TODO: model = LGBMRegressor(**{**default_params, **(params or {})})
    # TODO: model.fit(X_train, y_train)
    raise NotImplementedError("LightGBM revenue training not implemented.")


def train_prophet_revenue(
    df: pd.DataFrame,
    company_id: str,
) -> Any:
    """
    Train a Prophet model for a single company's revenue time series.

    Args:
        df:         Monthly revenue DataFrame with columns: ds (date), y (revenue).
        company_id: Company UUID (used for logging).

    Returns:
        Trained Prophet model.
    """
    # TODO: from prophet import Prophet
    # TODO: m = Prophet(yearly_seasonality=True, weekly_seasonality=False)
    # TODO: m.fit(df)
    raise NotImplementedError("Prophet revenue training not implemented.")


# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------

def time_series_cv(
    model_fn: Any,
    df: pd.DataFrame,
    n_splits: int = 5,
    horizon: int = 3,
) -> List[Dict[str, float]]:
    """
    Perform walk-forward (expanding window) cross-validation.

    Args:
        model_fn:  Function that accepts (X_train, y_train) and returns a trained model.
        df:        Monthly revenue DataFrame with features.
        n_splits:  Number of CV folds.
        horizon:   Forecast horizon per fold (in months).

    Returns:
        List of metric dicts for each fold.
    """
    # TODO: Implement time series cross-validation
    # TODO: For each fold: train on expanding window, evaluate on next horizon months
    raise NotImplementedError("Time series CV not implemented.")


# ---------------------------------------------------------------------------
# Main training pipeline
# ---------------------------------------------------------------------------

def run_training_pipeline(
    model_type: str = "xgboost",
    company_id: Optional[str] = None,
    save: bool = True,
) -> Any:
    """
    Full training pipeline for revenue forecasting.

    Steps:
    1. Load and aggregate revenue data
    2. Feature engineering (lag, rolling, date features)
    3. Train/test split
    4. Train selected model
    5. Evaluate on test set
    6. Save model if save=True

    Args:
        model_type: Model to train: 'xgboost' | 'lightgbm' | 'prophet'.
        company_id: Company UUID. If None, trains a global model.
        save:       Whether to save the trained model to models/ directory.

    Returns:
        Trained model object.
    """
    logger.info(f"Starting revenue training pipeline: model={model_type}, company={company_id or 'ALL'}")

    # TODO: Step 1 — Load data
    # TODO: Step 2 — Feature engineering
    # TODO: Step 3 — Train/test split
    # TODO: Step 4 — Train model
    # TODO: Step 5 — Evaluate
    # TODO: Step 6 — Save

    raise NotImplementedError("Revenue training pipeline not implemented.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Train revenue forecasting model.")
    parser.add_argument(
        "--model", type=str, default="xgboost",
        choices=["xgboost", "lightgbm", "prophet"],
        help="Model architecture to train."
    )
    parser.add_argument(
        "--company", type=str, default=None,
        help="Company UUID to train for (all companies if omitted)."
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Do not save the trained model to disk."
    )
    args = parser.parse_args()

    run_training_pipeline(
        model_type=args.model,
        company_id=args.company,
        save=not args.no_save,
    )


if __name__ == "__main__":
    main()

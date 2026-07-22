"""
train_profit.py
===============
Train profit prediction models.

Net Profit = Revenue - COGS - Operating Expenses

Supported models:
- XGBoost Regressor
- LightGBM Regressor
- Prophet (for trend modeling)

Usage:
    python scripts/train_profit.py --model xgboost
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


def load_profit_data(company_id: Optional[str] = None) -> pd.DataFrame:
    """
    Load and compute monthly profit data from sales, expenses, and products.

    Computation:
    1. COGS = sum(sale_items.quantity × products.cost_price)
    2. Revenue = sum(sales.net_amount)
    3. Gross Profit = Revenue - COGS
    4. Expenses = sum(expenses.amount) per period
    5. Net Profit = Gross Profit - Expenses

    Args:
        company_id: Filter to one company (all if None).

    Returns:
        Monthly profit DataFrame with columns:
        company_id, period, revenue, cogs, gross_profit, expenses, net_profit,
        profit_margin_pct.
    """
    # TODO: Load sales_clean, sale_items_clean, products, expenses_clean
    # TODO: Join sale_items with products on product_id to get cost_price
    # TODO: Aggregate COGS per sale, join to sales
    # TODO: Group by company + period, compute profit columns
    raise NotImplementedError("load_profit_data not implemented.")


def train_xgboost_profit(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Optional[Dict] = None,
) -> Any:
    """
    Train XGBoost for profit prediction.

    Args:
        X_train: Feature matrix (revenue, expenses, cogs, lag features, date features).
        y_train: Net profit target.
        params:  Hyperparameter overrides.

    Returns:
        Trained XGBRegressor.
    """
    # TODO: from xgboost import XGBRegressor; initialize, fit, return
    raise NotImplementedError("XGBoost profit training not implemented.")


def train_lightgbm_profit(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Optional[Dict] = None,
) -> Any:
    """
    Train LightGBM for profit prediction.

    Args:
        X_train: Feature matrix.
        y_train: Net profit target.
        params:  Hyperparameter overrides.

    Returns:
        Trained LGBMRegressor.
    """
    # TODO: from lightgbm import LGBMRegressor; initialize, fit, return
    raise NotImplementedError("LightGBM profit training not implemented.")


def compute_shap_values(model: Any, X: pd.DataFrame) -> Any:
    """
    Compute SHAP values to explain profit drivers.

    Args:
        model: Trained tree-based model (XGBoost or LightGBM).
        X:     Feature matrix for SHAP computation.

    Returns:
        SHAP Explanation object.
    """
    # TODO: import shap
    # TODO: explainer = shap.TreeExplainer(model)
    # TODO: return explainer(X)
    raise NotImplementedError("SHAP computation not implemented.")


def run_training_pipeline(
    model_type: str = "xgboost",
    company_id: Optional[str] = None,
    save: bool = True,
) -> Any:
    """
    Full profit training pipeline.

    Args:
        model_type: 'xgboost' | 'lightgbm' | 'prophet'.
        company_id: Filter to one company (all if None).
        save:       Whether to save model artifact.

    Returns:
        Trained model.
    """
    logger.info(f"Profit training: model={model_type}")
    # TODO: Load → feature engineering → split → train → SHAP → evaluate → save
    raise NotImplementedError("Profit training pipeline not implemented.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train profit prediction model.")
    parser.add_argument("--model",   type=str, default="xgboost",
                        choices=["xgboost", "lightgbm", "prophet"])
    parser.add_argument("--company", type=str, default=None)
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    run_training_pipeline(args.model, args.company, not args.no_save)


if __name__ == "__main__":
    main()

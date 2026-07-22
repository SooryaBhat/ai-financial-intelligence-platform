"""
train_sales.py
==============
Train sales forecasting models (product and category level).

Supports:
- XGBoost Regressor with lag/rolling features
- LightGBM Regressor
- Prophet per-product / per-category

Usage:
    python scripts/train_sales.py --level product --model xgboost
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


def load_sales_data(level: str = "product") -> pd.DataFrame:
    """
    Load processed sales data aggregated at the specified level.

    Args:
        level: 'product' or 'category'.

    Returns:
        Monthly aggregated DataFrame with features.
    """
    # TODO: Load sale_items_clean.csv, join with sales + products + categories
    # TODO: Group by company_id + product/category_id + period
    # TODO: Sum quantity and revenue
    raise NotImplementedError("load_sales_data not implemented.")


def train_xgboost_sales(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Optional[Dict] = None,
) -> Any:
    """
    Train XGBoost for sales forecasting.

    Args:
        X_train: Feature matrix.
        y_train: Target (unit sales or revenue).
        params:  Hyperparameter overrides.

    Returns:
        Trained XGBRegressor.
    """
    # TODO: Initialize and train XGBRegressor
    raise NotImplementedError("XGBoost sales training not implemented.")


def train_lightgbm_sales(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Optional[Dict] = None,
) -> Any:
    """
    Train LightGBM for sales forecasting.

    Args:
        X_train: Feature matrix.
        y_train: Target.
        params:  Hyperparameter overrides.

    Returns:
        Trained LGBMRegressor.
    """
    # TODO: Initialize and train LGBMRegressor
    raise NotImplementedError("LightGBM sales training not implemented.")


def train_prophet_per_sku(
    sales_df: pd.DataFrame,
    product_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Train one Prophet model per SKU (product_id).

    Args:
        sales_df:    Monthly sales DataFrame per product.
        product_ids: List of product UUIDs to train. If None, trains for all.

    Returns:
        Dict mapping product_id → trained Prophet model.
    """
    # TODO: Filter by product_id if specified
    # TODO: Loop, reshape to {ds, y}, fit Prophet, store in dict
    raise NotImplementedError("Per-SKU Prophet training not implemented.")


def run_training_pipeline(
    level: str = "product",
    model_type: str = "xgboost",
    company_id: Optional[str] = None,
    save: bool = True,
) -> Any:
    """
    Full sales training pipeline.

    Args:
        level:      Aggregation level: 'product' or 'category'.
        model_type: 'xgboost' | 'lightgbm' | 'prophet'.
        company_id: Filter to one company (all if None).
        save:       Save model artifact.

    Returns:
        Trained model.
    """
    logger.info(f"Sales training: level={level}, model={model_type}")
    # TODO: load_sales_data → feature_engineering → split → train → evaluate → save
    raise NotImplementedError("Sales training pipeline not implemented.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train sales forecasting model.")
    parser.add_argument("--level",   type=str, default="product",  choices=["product", "category"])
    parser.add_argument("--model",   type=str, default="xgboost",  choices=["xgboost", "lightgbm", "prophet"])
    parser.add_argument("--company", type=str, default=None)
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    run_training_pipeline(args.level, args.model, args.company, not args.no_save)


if __name__ == "__main__":
    main()

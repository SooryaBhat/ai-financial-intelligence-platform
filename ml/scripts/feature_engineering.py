"""
feature_engineering.py
=======================
Feature creation and selection for all ML models in the platform.

This module provides domain-specific feature engineering functions
tailored for ERP financial data (sales, expenses, inventory, etc.).

Usage:
    python scripts/feature_engineering.py

Output:
    datasets/processed/*_features.csv
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, save_csv, add_date_features,
    make_lag_features, make_rolling_features, PROCESSED_DIR
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Revenue features
# ---------------------------------------------------------------------------

def build_revenue_features(
    sales_df: pd.DataFrame,
    company_id: Optional[str] = None,
    freq: str = "M",
) -> pd.DataFrame:
    """
    Build monthly revenue time-series features per company/branch.

    Features created:
    - year, month, quarter
    - revenue_lag_1, revenue_lag_2, revenue_lag_3, revenue_lag_12
    - revenue_roll_mean_3, revenue_roll_mean_6, revenue_roll_std_3
    - yoy_growth_rate (year-over-year growth)
    - is_q4 (Q4 seasonal flag)
    - is_q2 (Q2 seasonal flag)

    Args:
        sales_df:   Cleaned sales DataFrame.
        company_id: Filter to specific company UUID (optional).
        freq:       Aggregation frequency ('M' for monthly, 'Q' for quarterly).

    Returns:
        Feature DataFrame ready for time-series model training.
    """
    # TODO: Implement revenue feature engineering
    logger.info("Building revenue features...")

    # TODO: Filter by company_id if specified
    # TODO: Parse sale_date, group by company_id + period, sum net_amount
    # TODO: add_date_features(df, 'period')
    # TODO: make_lag_features(df, 'revenue', lags=[1, 2, 3, 12], group_cols=['company_id'])
    # TODO: make_rolling_features(df, 'revenue', windows=[3, 6])
    # TODO: Compute YoY growth rate
    # TODO: Add seasonal dummy flags

    raise NotImplementedError("Revenue feature engineering not yet implemented.")


# ---------------------------------------------------------------------------
# Sales features
# ---------------------------------------------------------------------------

def build_sales_features(
    sales_df: pd.DataFrame,
    sale_items_df: pd.DataFrame,
    products_df: pd.DataFrame,
    categories_df: pd.DataFrame,
    level: str = "product",
) -> pd.DataFrame:
    """
    Build sales features at product or category level.

    Args:
        sales_df:      Cleaned sales DataFrame.
        sale_items_df: Cleaned sale_items DataFrame.
        products_df:   Cleaned products DataFrame.
        categories_df: Cleaned categories DataFrame.
        level:         Aggregation level: 'product' or 'category'.

    Returns:
        Feature DataFrame with lag, rolling, and seasonal features.
    """
    # TODO: Implement sales feature engineering
    logger.info(f"Building sales features at {level} level...")

    # TODO: Join sale_items + sales + products + categories
    # TODO: Group by company_id + product/category + period
    # TODO: Sum quantity and revenue
    # TODO: make_lag_features(..., lags=[1, 2, 3, 6, 12])
    # TODO: make_rolling_features(..., windows=[3, 6])
    # TODO: Add price sensitivity features (avg unit_price, discount ratio)

    raise NotImplementedError("Sales feature engineering not yet implemented.")


# ---------------------------------------------------------------------------
# Inventory features
# ---------------------------------------------------------------------------

def build_inventory_features(
    inventory_df: pd.DataFrame,
    stock_movements_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    sale_items_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build inventory demand features.

    Features created:
    - days_of_stock_remaining (quantity_on_hand / avg_daily_consumption)
    - stockout_risk_flag (binary: days_remaining < 7)
    - avg_daily_consumption (rolling 30-day)
    - reorder_deficit (reorder_quantity - quantity_on_hand if below reorder_level)
    - in_out_ratio (purchase movements / sale movements)

    Args:
        inventory_df:       Cleaned inventory DataFrame.
        stock_movements_df: Cleaned stock_movements DataFrame.
        sales_df:           Cleaned sales DataFrame.
        sale_items_df:      Cleaned sale_items DataFrame.

    Returns:
        Feature DataFrame for inventory demand modeling.
    """
    # TODO: Implement inventory feature engineering
    logger.info("Building inventory features...")

    # TODO: Compute daily consumption rate per product per warehouse
    # TODO: Calculate days_of_stock_remaining
    # TODO: Flag products below reorder_level
    # TODO: Add seasonal demand indicators

    raise NotImplementedError("Inventory feature engineering not yet implemented.")


# ---------------------------------------------------------------------------
# Expense features
# ---------------------------------------------------------------------------

def build_expense_features(
    expenses_df: pd.DataFrame,
    sales_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build expense prediction features.

    Features created:
    - expense_lag_1, expense_lag_2, expense_lag_3
    - expense_roll_mean_3, expense_roll_std_3
    - expense_to_revenue_ratio (expenses / revenue for same period)
    - category_encoded (label encoded expense category)
    - is_year_end (flag for December)

    Args:
        expenses_df: Cleaned expenses DataFrame.
        sales_df:    Cleaned sales DataFrame (for revenue ratio).

    Returns:
        Feature DataFrame for expense forecasting.
    """
    # TODO: Implement expense feature engineering
    logger.info("Building expense features...")

    # TODO: Aggregate monthly expenses by company + category
    # TODO: make_lag_features, make_rolling_features
    # TODO: Join with revenue to compute expense ratio

    raise NotImplementedError("Expense feature engineering not yet implemented.")


# ---------------------------------------------------------------------------
# Profit features
# ---------------------------------------------------------------------------

def build_profit_features(
    sales_df: pd.DataFrame,
    sale_items_df: pd.DataFrame,
    products_df: pd.DataFrame,
    expenses_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build profit prediction features.

    Profit = Revenue - COGS - Operating Expenses

    Features created:
    - gross_profit (revenue - cogs)
    - net_profit (gross_profit - expenses)
    - profit_margin_pct (net_profit / revenue × 100)
    - profit_lag_1, profit_lag_2, profit_lag_3
    - profit_roll_mean_3, profit_roll_std_3
    - expense_ratio (expenses / revenue)

    Args:
        sales_df:      Cleaned sales DataFrame.
        sale_items_df: Cleaned sale_items DataFrame.
        products_df:   Products DataFrame (for cost_price).
        expenses_df:   Cleaned expenses DataFrame.

    Returns:
        Feature DataFrame for profit prediction.
    """
    # TODO: Implement profit feature engineering
    logger.info("Building profit features...")

    # TODO: Compute COGS = sum(quantity × cost_price) per sale
    # TODO: Gross profit = revenue - COGS
    # TODO: Net profit = gross_profit - monthly expenses
    # TODO: make_lag_features, make_rolling_features

    raise NotImplementedError("Profit feature engineering not yet implemented.")


# ---------------------------------------------------------------------------
# Business health features
# ---------------------------------------------------------------------------

def build_health_score_features(
    sales_df: pd.DataFrame,
    expenses_df: pd.DataFrame,
    invoices_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    stock_movements_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build KPI features for business health scoring.

    KPIs computed:
    - revenue_growth_rate (MoM %)
    - profit_margin_pct
    - expense_to_revenue_ratio
    - inventory_turnover_ratio
    - invoice_collection_rate (paid invoices / total invoices)
    - avg_days_to_payment (invoice date → payment date)

    Args:
        sales_df:           Cleaned sales.
        expenses_df:        Cleaned expenses.
        invoices_df:        Cleaned invoices.
        payments_df:        Cleaned payments.
        inventory_df:       Cleaned inventory.
        stock_movements_df: Cleaned stock movements.

    Returns:
        Feature DataFrame for health score computation.
    """
    # TODO: Implement health score feature engineering
    logger.info("Building business health score features...")

    # TODO: Compute all 6 KPIs per company per month
    # TODO: Normalize each KPI to 0–100 using MinMaxScaler
    # TODO: Apply weights and compute composite score

    raise NotImplementedError("Health score feature engineering not yet implemented.")


# ---------------------------------------------------------------------------
# Anomaly detection features
# ---------------------------------------------------------------------------

def build_anomaly_features(
    sales_df: pd.DataFrame,
    expenses_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    stock_movements_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build features for anomaly detection across transaction types.

    Features created:
    - amount_zscore (how many std deviations above company mean)
    - amount_iqr_flag (outside IQR × 1.5)
    - time_since_last_transaction (in days)
    - is_large_round_number (suspicious even amounts)
    - weekend_transaction_flag
    - transaction_type (sale / expense / payment / stock_movement)

    Args:
        sales_df:           Cleaned sales.
        expenses_df:        Cleaned expenses.
        payments_df:        Cleaned payments.
        stock_movements_df: Cleaned stock movements.

    Returns:
        Unified feature DataFrame for anomaly detection models.
    """
    # TODO: Implement anomaly detection feature engineering
    logger.info("Building anomaly detection features...")

    # TODO: Combine all transaction tables with a common schema
    # TODO: Compute z-scores per company
    # TODO: Compute IQR flags
    # TODO: Add transaction metadata features

    raise NotImplementedError("Anomaly feature engineering not yet implemented.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all feature engineering pipelines."""
    logger.info("Starting feature engineering pipeline...")
    # TODO: Load processed CSVs and build feature sets for each model
    logger.info("Feature engineering complete.")


if __name__ == "__main__":
    main()

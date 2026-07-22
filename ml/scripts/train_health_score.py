"""
train_health_score.py
=====================
Train or compute the Business Health Score pipeline.

The health score is a composite KPI score (0–100) based on:
- Revenue growth rate        (25%)
- Profit margin              (25%)
- Expense-to-revenue ratio   (20%)
- Inventory turnover ratio   (15%)
- Invoice collection rate    (15%)

Two approaches:
1. Rule-based (weighted KPI normalization) — fast, interpretable
2. Supervised model (if labeled health data becomes available)

Usage:
    python scripts/train_health_score.py --approach rule_based
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import get_logger, load_csv, save_model, PROCESSED_DIR, MODELS_DIR

logger = get_logger(__name__)

# KPI weights (must sum to 1.0)
KPI_WEIGHTS = {
    "revenue_growth_rate":    0.25,
    "profit_margin_pct":      0.25,
    "expense_ratio":          0.20,   # lower is better
    "inventory_turnover":     0.15,
    "invoice_collection_rate": 0.15,
}


def load_health_score_data(company_id: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Load all data needed to compute health KPIs.

    Args:
        company_id: Filter to one company (all if None).

    Returns:
        Dict with keys: sales, expenses, invoices, payments, inventory, movements.
    """
    # TODO: Load all 6 processed CSVs
    # TODO: Filter by company_id if specified
    raise NotImplementedError("load_health_score_data not implemented.")


def compute_revenue_growth_rate(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute month-over-month revenue growth rate per company.

    Formula:
        growth_rate = (revenue_this_month - revenue_last_month) / revenue_last_month

    Args:
        sales_df: Monthly aggregated sales.

    Returns:
        DataFrame with company_id, period, revenue_growth_rate.
    """
    # TODO: Group by company + period, sum net_amount, compute pct_change
    raise NotImplementedError("Revenue growth rate computation not implemented.")


def compute_profit_margin(sales_df: pd.DataFrame, expenses_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute monthly net profit margin per company.

    Formula:
        profit_margin = net_profit / revenue × 100

    Args:
        sales_df:    Monthly revenue data.
        expenses_df: Monthly expense data.

    Returns:
        DataFrame with company_id, period, profit_margin_pct.
    """
    # TODO: Join sales and expenses, compute net_profit, then margin
    raise NotImplementedError("Profit margin computation not implemented.")


def compute_expense_ratio(sales_df: pd.DataFrame, expenses_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the expense-to-revenue ratio per company per month.

    Formula:
        expense_ratio = total_expenses / total_revenue

    Lower is better. A ratio > 0.8 indicates risk.

    Args:
        sales_df:    Monthly revenue.
        expenses_df: Monthly expenses.

    Returns:
        DataFrame with company_id, period, expense_ratio.
    """
    # TODO: Join and compute ratio
    raise NotImplementedError("Expense ratio computation not implemented.")


def compute_inventory_turnover(
    inventory_df: pd.DataFrame,
    stock_movements_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute inventory turnover ratio per company.

    Formula:
        inventory_turnover = COGS / avg_inventory_value

    Higher turnover indicates efficient inventory management.

    Args:
        inventory_df:       Current inventory snapshot.
        stock_movements_df: Historical stock movements.

    Returns:
        DataFrame with company_id, period, inventory_turnover.
    """
    # TODO: Compute COGS from outbound movements × cost_price
    # TODO: Compute avg inventory value
    # TODO: Return ratio
    raise NotImplementedError("Inventory turnover computation not implemented.")


def compute_invoice_collection_rate(
    invoices_df: pd.DataFrame,
    payments_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute the invoice collection rate (% of invoice value collected on time).

    Formula:
        collection_rate = paid_amount / total_amount

    Args:
        invoices_df: Invoice records.
        payments_df: Payment records.

    Returns:
        DataFrame with company_id, period, invoice_collection_rate.
    """
    # TODO: Group invoices by period, compute paid_amount / total_amount ratio
    raise NotImplementedError("Invoice collection rate computation not implemented.")


def normalize_kpis(kpis_df: pd.DataFrame, invert_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Normalize KPI values to 0–100 using min-max scaling.

    For KPIs where lower is better (e.g., expense_ratio), invert after scaling:
        score = 100 - normalized_value

    Args:
        kpis_df:     DataFrame with one column per KPI.
        invert_cols: List of column names to invert (lower=better KPIs).

    Returns:
        Normalized DataFrame with scores in range [0, 100].
    """
    # TODO: Apply MinMaxScaler per column, multiply by 100
    # TODO: Invert specified columns
    raise NotImplementedError("KPI normalization not implemented.")


def compute_composite_score(normalized_kpis_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the weighted composite health score.

    Score = sum(kpi_score × weight) for all KPIs

    Args:
        normalized_kpis_df: KPI scores normalized to 0–100.

    Returns:
        DataFrame with company_id, period, health_score, grade.
    """
    # TODO: Weighted average of normalized KPIs
    # TODO: Map score to grade: A (80-100), B (60-79), C (40-59), D (20-39), F (<20)
    raise NotImplementedError("Composite score computation not implemented.")


def run_training_pipeline(
    approach: str = "rule_based",
    company_id: Optional[str] = None,
    save: bool = True,
) -> Any:
    """
    Full business health score pipeline.

    Args:
        approach:   'rule_based' (KPI aggregation) or 'supervised' (ML model).
        company_id: Filter to one company (all if None).
        save:       Whether to save the pipeline artifact.

    Returns:
        Health score DataFrame or trained model (depending on approach).
    """
    logger.info(f"Health score pipeline: approach={approach}")
    # TODO: Load all data
    # TODO: Compute each KPI
    # TODO: Normalize
    # TODO: Compute composite score
    # TODO: Save pipeline if save=True
    raise NotImplementedError("Health score pipeline not implemented.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run business health score pipeline.")
    parser.add_argument("--approach", type=str, default="rule_based",
                        choices=["rule_based", "supervised"])
    parser.add_argument("--company",  type=str, default=None)
    parser.add_argument("--no-save",  action="store_true")
    args = parser.parse_args()

    run_training_pipeline(args.approach, args.company, not args.no_save)


if __name__ == "__main__":
    main()

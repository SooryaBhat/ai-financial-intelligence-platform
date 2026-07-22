"""
preprocess.py
=============
Data cleaning and preprocessing pipeline for the ML module.

Reads raw/synthetic data, applies cleaning steps, and saves
processed DataFrames to datasets/processed/.

Usage:
    python scripts/preprocess.py

Output:
    datasets/processed/sales_clean.csv
    datasets/processed/expenses_clean.csv
    datasets/processed/inventory_clean.csv
    ...
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

# Adjust import path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, save_csv, check_data_quality,
    SYNTHETIC_DIR, PROCESSED_DIR
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Individual cleaning functions
# ---------------------------------------------------------------------------

def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the sales DataFrame.

    Steps:
    - Parse sale_date to datetime
    - Remove cancelled sales if needed
    - Drop duplicate rows
    - Clip negative amounts to 0
    - Enforce status enum values

    Args:
        df: Raw sales DataFrame.

    Returns:
        Cleaned sales DataFrame.
    """
    # TODO: Implement cleaning logic
    logger.info("Cleaning sales data...")
    df = df.copy()

    # TODO: df['sale_date'] = pd.to_datetime(df['sale_date'])
    # TODO: df = df[df['status'] != 'cancelled']
    # TODO: df['net_amount'] = df['net_amount'].clip(lower=0)
    # TODO: df = df.drop_duplicates(subset=['id'])

    return df


def clean_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the expenses DataFrame.

    Steps:
    - Parse expense_date to datetime
    - Filter only approved expenses
    - Remove outlier amounts (> 99th percentile per category)

    Args:
        df: Raw expenses DataFrame.

    Returns:
        Cleaned expenses DataFrame.
    """
    # TODO: Implement cleaning logic
    logger.info("Cleaning expenses data...")
    df = df.copy()

    # TODO: df['expense_date'] = pd.to_datetime(df['expense_date'])
    # TODO: df = df[df['status'] == 'approved']
    # TODO: Remove per-category outliers using IQR

    return df


def clean_inventory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the inventory DataFrame.

    Steps:
    - Ensure quantity_on_hand >= 0
    - Fill missing reorder_level with median per product
    - Deduplicate by (product_id, warehouse_id)

    Args:
        df: Raw inventory DataFrame.

    Returns:
        Cleaned inventory DataFrame.
    """
    # TODO: Implement cleaning logic
    logger.info("Cleaning inventory data...")
    df = df.copy()

    # TODO: df['quantity_on_hand'] = df['quantity_on_hand'].clip(lower=0)
    # TODO: Deduplicate

    return df


def clean_purchases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the purchases DataFrame.

    Args:
        df: Raw purchases DataFrame.

    Returns:
        Cleaned purchases DataFrame.
    """
    # TODO: Implement cleaning logic
    logger.info("Cleaning purchases data...")
    df = df.copy()
    return df


def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the payments DataFrame.

    Args:
        df: Raw payments DataFrame.

    Returns:
        Cleaned payments DataFrame.
    """
    # TODO: Implement cleaning logic
    logger.info("Cleaning payments data...")
    df = df.copy()
    return df


def clean_stock_movements(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the stock_movements DataFrame.

    Steps:
    - Validate movement_type ∈ {'in', 'out'}
    - Ensure quantity > 0
    - Parse moved_at to datetime

    Args:
        df: Raw stock_movements DataFrame.

    Returns:
        Cleaned stock_movements DataFrame.
    """
    # TODO: Implement cleaning logic
    logger.info("Cleaning stock_movements data...")
    df = df.copy()
    return df


# ---------------------------------------------------------------------------
# Master preprocessing pipeline
# ---------------------------------------------------------------------------

def run_preprocessing_pipeline(
    source_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Run the full preprocessing pipeline across all datasets.

    Args:
        source_dir: Directory to load raw/synthetic CSVs from.
        output_dir: Directory to save processed CSVs to.

    Returns:
        Dict mapping dataset names to cleaned DataFrames.
    """
    source_dir = source_dir or SYNTHETIC_DIR
    output_dir = output_dir or PROCESSED_DIR

    logger.info("=" * 60)
    logger.info("Starting preprocessing pipeline...")
    logger.info(f"Source: {source_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info("=" * 60)

    results: Dict[str, pd.DataFrame] = {}

    # TODO: Load and clean each dataset
    # datasets_to_clean = {
    #     "sales":           clean_sales,
    #     "expenses":        clean_expenses,
    #     "inventory":       clean_inventory,
    #     "purchases":       clean_purchases,
    #     "payments":        clean_payments,
    #     "stock_movements": clean_stock_movements,
    # }

    # TODO: Loop through, clean, validate, and save
    # for name, clean_fn in datasets_to_clean.items():
    #     raw_df      = load_csv(f"{name}.csv", directory=source_dir)
    #     clean_df    = clean_fn(raw_df)
    #     quality     = check_data_quality(clean_df, name)
    #     logger.info(f"{name}: {quality['row_count']} rows, {quality['duplicate_count']} duplicates")
    #     save_csv(clean_df, f"{name}_clean.csv", directory=output_dir)
    #     results[name] = clean_df

    logger.info("Preprocessing complete.")
    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess ERP datasets.")
    parser.add_argument(
        "--source", type=str, default=None,
        help="Source directory (default: datasets/synthetic/)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory (default: datasets/processed/)"
    )
    args = parser.parse_args()

    source = Path(args.source) if args.source else None
    output = Path(args.output) if args.output else None

    run_preprocessing_pipeline(source_dir=source, output_dir=output)


if __name__ == "__main__":
    main()

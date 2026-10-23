# -*- coding: utf-8 -*-
"""
preprocess.py
=============
Data cleaning and preprocessing pipeline for the ALLADIN ML module.

Reads synthetic retail datasets, validates schemas, handles missing values,
and prepares cleaned data tables under ml/datasets/processed/.

Usage:
    python ml/scripts/preprocess.py
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, save_csv,
    SYNTHETIC_DIR, PROCESSED_DIR
)

logger = get_logger(__name__)


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize sales transactions."""
    logger.info("Cleaning sales data...")
    df = df.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df = df.dropna(subset=["id", "sale_date", "company_id", "net_amount"])
    df["net_amount"] = df["net_amount"].clip(lower=0.0)
    df["total_amount"] = df["total_amount"].clip(lower=0.0)
    df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df


def clean_sale_items(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate sale line items."""
    logger.info("Cleaning sale items data...")
    df = df.copy()
    df = df.dropna(subset=["id", "sale_id", "product_id"])
    df["quantity"] = df["quantity"].clip(lower=0)
    df["unit_price"] = df["unit_price"].clip(lower=0.0)
    df["discount_pct"] = df["discount_pct"].clip(lower=0.0, upper=1.0)
    df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df


def clean_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize operational expenses."""
    logger.info("Cleaning expenses data...")
    df = df.copy()
    df["expense_date"] = pd.to_datetime(df["expense_date"], errors="coerce")
    df = df.dropna(subset=["id", "expense_date", "company_id", "amount"])
    df["amount"] = df["amount"].clip(lower=0.0)
    df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df


def clean_inventory(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate inventory records."""
    logger.info("Cleaning inventory data...")
    df = df.copy()
    df = df.dropna(subset=["id", "product_id", "warehouse_id"])
    df["quantity_on_hand"] = df["quantity_on_hand"].clip(lower=0)
    df["reorder_level"] = df["reorder_level"].clip(lower=0)
    df["reorder_quantity"] = df["reorder_quantity"].clip(lower=0)
    df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df


def clean_stock_movements(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate stock movements."""
    logger.info("Cleaning stock movements...")
    df = df.copy()
    df["moved_at"] = pd.to_datetime(df["moved_at"], errors="coerce")
    df = df.dropna(subset=["id", "product_id", "warehouse_id", "moved_at"])
    df["quantity"] = df["quantity"].clip(lower=0)
    df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df


def clean_daily_kpi(df: pd.DataFrame) -> pd.DataFrame:
    """Clean daily KPI summary table."""
    logger.info("Cleaning daily KPI summary...")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["company_id", "date", "revenue"])
    df = df.drop_duplicates(subset=["company_id", "date"]).sort_values(["company_id", "date"]).reset_index(drop=True)
    return df


def run_preprocessing() -> Dict[str, pd.DataFrame]:
    """Execute complete data preprocessing and save artifacts to processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Starting preprocessing pipeline from: %s", SYNTHETIC_DIR)

    sales_df = clean_sales(load_csv("sales.csv"))
    sale_items_df = clean_sale_items(load_csv("sale_items.csv"))
    expenses_df = clean_expenses(load_csv("expenses.csv"))
    inventory_df = clean_inventory(load_csv("inventory.csv"))
    stock_movements_df = clean_stock_movements(load_csv("stock_movements.csv"))
    daily_kpi_df = clean_daily_kpi(load_csv("daily_kpi_summary.csv"))

    save_csv(sales_df, "sales_clean.csv", PROCESSED_DIR)
    save_csv(sale_items_df, "sale_items_clean.csv", PROCESSED_DIR)
    save_csv(expenses_df, "expenses_clean.csv", PROCESSED_DIR)
    save_csv(inventory_df, "inventory_clean.csv", PROCESSED_DIR)
    save_csv(stock_movements_df, "stock_movements_clean.csv", PROCESSED_DIR)
    save_csv(daily_kpi_df, "daily_kpi_clean.csv", PROCESSED_DIR)

    logger.info("Preprocessing complete. 6 clean tables saved to: %s", PROCESSED_DIR)
    return {
        "sales": sales_df,
        "sale_items": sale_items_df,
        "expenses": expenses_df,
        "inventory": inventory_df,
        "stock_movements": stock_movements_df,
        "daily_kpi": daily_kpi_df,
    }


if __name__ == "__main__":
    run_preprocessing()

# -*- coding: utf-8 -*-
"""
feature_engineering.py
======================
Feature creation and transformation pipelines for all seven ALLADIN ML models.

Transforms cleaned retail data into structured feature matrices with:
- Calendar & seasonal attributes
- Lagged time-series features
- Rolling window statistics
- Moving consumption proxies
- Cross-ratio financial metrics
- Anomaly feature vectors

Usage:
    python ml/scripts/feature_engineering.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    get_logger, load_csv, save_csv, add_date_features,
    make_lag_features, PROCESSED_DIR
)

logger = get_logger(__name__)


def build_revenue_features(daily_kpi_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Build monthly revenue feature matrix across companies.
    Target: monthly revenue.
    Features: lag_1, lag_2, lag_3, lag_6, lag_12, roll3_mean, roll6_mean, month_num, quarter.
    """
    if daily_kpi_df is None:
        daily_kpi_df = load_csv("daily_kpi_clean.csv", PROCESSED_DIR)

    df = daily_kpi_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    
    # Monthly aggregation per company
    monthly = (
        df.groupby(["company_id", pd.Grouper(key="date", freq="ME")])
        .agg(revenue=("revenue", "sum"), orders=("order_count", "sum"))
        .reset_index()
        .rename(columns={"date": "month"})
        .sort_values(["company_id", "month"])
        .reset_index(drop=True)
    )

    records = []
    for cid, grp in monthly.groupby("company_id"):
        grp = grp.sort_values("month").copy()
        for i in range(len(grp)):
            if i < 12:  # Need 12 lags
                continue
            hist = grp.iloc[:i]["revenue"].tolist()
            m_dt = grp.iloc[i]["month"]
            records.append({
                "company_id": cid,
                "month": m_dt,
                "revenue": float(grp.iloc[i]["revenue"]),
                "lag_1": float(hist[-1]),
                "lag_2": float(hist[-2]),
                "lag_3": float(hist[-3]),
                "lag_6": float(hist[-6]),
                "lag_12": float(hist[-12]),
                "roll3_mean": float(np.mean(hist[-3:])),
                "roll6_mean": float(np.mean(hist[-6:])),
                "month_num": float(m_dt.month),
                "quarter": float((m_dt.month - 1) // 3 + 1),
            })

    feat_df = pd.DataFrame(records)
    logger.info("Built revenue features: %d rows x %d cols", len(feat_df), len(feat_df.columns))
    return feat_df


def build_sales_features(
    sale_items_df: Optional[pd.DataFrame] = None,
    sales_df: Optional[pd.DataFrame] = None,
    products_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Build monthly product and category level sales feature matrix.
    Target: quantity sold.
    Features: lag_1, lag_2, lag_3, lag_12, roll3_mean, roll6_mean, roll3_std, month_num, quarter, year, is_q4, is_q1.
    """
    if sale_items_df is None:
        sale_items_df = load_csv("sale_items_clean.csv", PROCESSED_DIR)
    if sales_df is None:
        sales_df = load_csv("sales_clean.csv", PROCESSED_DIR)
    if products_df is None:
        products_df = load_csv("products.csv")

    merged = sale_items_df.merge(
        sales_df[["id", "sale_date", "company_id", "status"]],
        left_on="sale_id", right_on="id", suffixes=("", "_sale")
    )
    merged = merged[merged["status"] == "completed"].copy()
    merged["sale_date"] = pd.to_datetime(merged["sale_date"])

    # Aggregate monthly per product
    monthly = (
        merged.groupby(["product_id", "company_id", pd.Grouper(key="sale_date", freq="ME")])
        .agg(quantity=("quantity", "sum"), revenue=("line_total", "sum"))
        .reset_index()
        .rename(columns={"sale_date": "month"})
        .sort_values(["product_id", "month"])
        .reset_index(drop=True)
    )

    records = []
    for pid, grp in monthly.groupby("product_id"):
        grp = grp.sort_values("month").copy()
        cid = grp["company_id"].iloc[0]
        for i in range(len(grp)):
            if i < 12:  # Need 12 lags
                continue
            hist = grp.iloc[:i]["quantity"].tolist()
            m_dt = grp.iloc[i]["month"]
            q = (m_dt.month - 1) // 3 + 1
            records.append({
                "product_id": pid,
                "company_id": cid,
                "month": m_dt,
                "quantity": float(grp.iloc[i]["quantity"]),
                "lag_1": float(hist[-1]),
                "lag_2": float(hist[-2]),
                "lag_3": float(hist[-3]),
                "lag_12": float(hist[-12]),
                "roll3_mean": float(np.mean(hist[-3:])),
                "roll6_mean": float(np.mean(hist[-6:])),
                "roll3_std": float(np.std(hist[-3:])),
                "month_num": float(m_dt.month),
                "quarter": float(q),
                "year": float(m_dt.year),
                "is_q4": 1.0 if q == 4 else 0.0,
                "is_q1": 1.0 if q == 1 else 0.0,
            })

    feat_df = pd.DataFrame(records)
    logger.info("Built sales features: %d rows x %d cols", len(feat_df), len(feat_df.columns))
    return feat_df


def build_inventory_features(stock_movements_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Build monthly inventory outbound consumption demand features.
    Target: units_out (demand).
    Features: lag_1, lag_2, lag_3, lag_6, roll3_mean, roll6_mean, month_num, quarter, year, is_q4, is_q1.
    """
    if stock_movements_df is None:
        stock_movements_df = load_csv("stock_movements_clean.csv", PROCESSED_DIR)

    outbound = stock_movements_df[stock_movements_df["movement_type"] == "out"].copy()
    outbound["moved_at"] = pd.to_datetime(outbound["moved_at"])

    monthly = (
        outbound.groupby(["product_id", pd.Grouper(key="moved_at", freq="ME")])
        .agg(units_out=("quantity", "sum"))
        .reset_index()
        .rename(columns={"moved_at": "month"})
        .sort_values(["product_id", "month"])
        .reset_index(drop=True)
    )

    records = []
    for pid, grp in monthly.groupby("product_id"):
        grp = grp.sort_values("month").copy()
        for i in range(len(grp)):
            if i < 6:  # Need 6 lags
                continue
            hist = grp.iloc[:i]["units_out"].tolist()
            m_dt = grp.iloc[i]["month"]
            q = (m_dt.month - 1) // 3 + 1
            records.append({
                "product_id": pid,
                "month": m_dt,
                "units_out": float(grp.iloc[i]["units_out"]),
                "lag_1": float(hist[-1]),
                "lag_2": float(hist[-2]),
                "lag_3": float(hist[-3]),
                "lag_6": float(hist[-6]),
                "roll3_mean": float(np.mean(hist[-3:])),
                "roll6_mean": float(np.mean(hist[-6:])),
                "month_num": float(m_dt.month),
                "quarter": float(q),
                "year": float(m_dt.year),
                "is_q4": 1.0 if q == 4 else 0.0,
                "is_q1": 1.0 if q == 1 else 0.0,
            })

    feat_df = pd.DataFrame(records)
    logger.info("Built inventory features: %d rows x %d cols", len(feat_df), len(feat_df.columns))
    return feat_df


def build_profit_features(daily_kpi_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Build monthly net profit features.
    Target: net_profit.
    Features: profit_lag1, profit_lag2, profit_lag3, profit_lag6, profit_roll3, profit_roll6,
              revenue_lag1, revenue_lag2, revenue_lag3, expense_ratio_lag1, expense_ratio_lag2,
              month_num, quarter, year, is_q4.
    """
    if daily_kpi_df is None:
        daily_kpi_df = load_csv("daily_kpi_clean.csv", PROCESSED_DIR)

    df = daily_kpi_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    monthly = (
        df.groupby(["company_id", pd.Grouper(key="date", freq="ME")])
        .agg(
            revenue=("revenue", "sum"),
            cogs=("cogs", "sum"),
            operating_expenses=("operating_expenses", "sum"),
            net_profit=("net_profit", "sum"),
        )
        .reset_index()
        .rename(columns={"date": "month"})
        .sort_values(["company_id", "month"])
        .reset_index(drop=True)
    )

    records = []
    for cid, grp in monthly.groupby("company_id"):
        grp = grp.sort_values("month").copy()
        for i in range(len(grp)):
            if i < 6:
                continue
            p_hist = grp.iloc[:i]["net_profit"].tolist()
            r_hist = grp.iloc[:i]["revenue"].tolist()
            e_hist = grp.iloc[:i]["operating_expenses"].tolist()
            m_dt = grp.iloc[i]["month"]
            q = (m_dt.month - 1) // 3 + 1
            exp_ratio_1 = e_hist[-1] / (r_hist[-1] + 1e-8)
            exp_ratio_2 = e_hist[-2] / (r_hist[-2] + 1e-8)
            records.append({
                "company_id": cid,
                "month": m_dt,
                "net_profit": float(grp.iloc[i]["net_profit"]),
                "profit_lag1": float(p_hist[-1]),
                "profit_lag2": float(p_hist[-2]),
                "profit_lag3": float(p_hist[-3]),
                "profit_lag6": float(p_hist[-6]),
                "profit_roll3": float(np.mean(p_hist[-3:])),
                "profit_roll6": float(np.mean(p_hist[-6:])),
                "revenue_lag1": float(r_hist[-1]),
                "revenue_lag2": float(r_hist[-2]),
                "revenue_lag3": float(r_hist[-3]),
                "expense_ratio_lag1": float(exp_ratio_1),
                "expense_ratio_lag2": float(exp_ratio_2),
                "month_num": float(m_dt.month),
                "quarter": float(q),
                "year": float(m_dt.year),
                "is_q4": 1.0 if q == 4 else 0.0,
            })

    feat_df = pd.DataFrame(records)
    logger.info("Built profit features: %d rows x %d cols", len(feat_df), len(feat_df.columns))
    return feat_df


def build_expense_features(expenses_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Build monthly expense features per company and category.
    Target: total_expense.
    Features: lag_1, lag_2, lag_3, lag_6, roll3_mean, roll6_mean, roll3_std,
              txn_count, avg_expense, month_num, quarter, year, is_q4, is_q1.
    """
    if expenses_df is None:
        expenses_df = load_csv("expenses_clean.csv", PROCESSED_DIR)

    app_exp = expenses_df[expenses_df["status"] == "approved"].copy()
    app_exp["expense_date"] = pd.to_datetime(app_exp["expense_date"])

    monthly = (
        app_exp.groupby(["company_id", "category", pd.Grouper(key="expense_date", freq="ME")])
        .agg(total_expense=("amount", "sum"), txn_count=("id", "count"))
        .reset_index()
        .rename(columns={"expense_date": "month"})
        .sort_values(["company_id", "category", "month"])
        .reset_index(drop=True)
    )

    records = []
    for (cid, cat), grp in monthly.groupby(["company_id", "category"]):
        grp = grp.sort_values("month").copy()
        for i in range(len(grp)):
            if i < 6:
                continue
            hist = grp.iloc[:i]["total_expense"].tolist()
            m_dt = grp.iloc[i]["month"]
            q = (m_dt.month - 1) // 3 + 1
            # Leakage prevention: Use strictly lag-1 transaction count at forecast origin
            t_cnt_lag1 = float(grp.iloc[i - 1]["txn_count"])
            avg_exp_lag1 = float(hist[-1] / (t_cnt_lag1 + 1e-6))
            records.append({
                "company_id": cid,
                "category": cat,
                "month": m_dt,
                "total_expense": float(grp.iloc[i]["total_expense"]),
                "lag_1": float(hist[-1]),
                "lag_2": float(hist[-2]),
                "lag_3": float(hist[-3]),
                "lag_6": float(hist[-6]),
                "roll3_mean": float(np.mean(hist[-3:])),
                "roll6_mean": float(np.mean(hist[-6:])),
                "roll3_std": float(np.std(hist[-3:])),
                "txn_count_lag1": t_cnt_lag1,
                "avg_expense_lag1": avg_exp_lag1,
                "txn_count": t_cnt_lag1,  # Safe lagged alias
                "avg_expense": avg_exp_lag1,  # Safe lagged alias
                "month_num": float(m_dt.month),
                "quarter": float(q),
                "year": float(m_dt.year),
                "is_q4": 1.0 if q == 4 else 0.0,
                "is_q1": 1.0 if q == 1 else 0.0,
            })

    feat_df = pd.DataFrame(records)
    logger.info("Built expense features: %d rows x %d cols", len(feat_df), len(feat_df.columns))
    return feat_df


def build_anomaly_features(sales_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Build transaction-level anomaly feature matrix from sales orders.
    Excludes ground truth is_anomaly from feature inputs.
    Features: net_amount, discount_pct, day_of_week, is_weekend, month,
              status_enc, roll28_mean, roll28_std, amount_z_rolling.
    """
    if sales_df is None:
        sales_df = load_csv("sales_clean.csv", PROCESSED_DIR)

    df = sales_df.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df = df.sort_values(["company_id", "sale_date"]).reset_index(drop=True)

    # Rolling 28 transactions stats per company
    df["roll28_mean"] = (
        df.groupby("company_id")["net_amount"]
        .transform(lambda x: x.shift(1).rolling(28, min_periods=5).mean())
    )
    df["roll28_std"] = (
        df.groupby("company_id")["net_amount"]
        .transform(lambda x: x.shift(1).rolling(28, min_periods=5).std())
    )
    df["amount_z_rolling"] = (
        (df["net_amount"] - df["roll28_mean"]) / (df["roll28_std"].replace(0, np.nan) + 1e-6)
    )

    df["day_of_week"] = df["sale_date"].dt.dayofweek.astype(float)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(float)
    df["month"] = df["sale_date"].dt.month.astype(float)

    # Compute discount percentage if total_amount > 0
    df["discount_pct"] = (
        df["discount_amount"] / (df["total_amount"] + df["discount_amount"] + 1e-6)
    ).clip(0.0, 1.0).astype(float)

    status_map = {"completed": 0.0, "pending": 1.0, "cancelled": 2.0}
    df["status_enc"] = df["status"].map(status_map).fillna(0.0).astype(float)

    feat_cols = [
        "net_amount", "discount_pct", "day_of_week", "is_weekend",
        "month", "status_enc", "roll28_mean", "roll28_std", "amount_z_rolling"
    ]

    # Clean NaNs in rolling features
    df["roll28_mean"] = df["roll28_mean"].fillna(df["net_amount"].median())
    df["roll28_std"] = df["roll28_std"].fillna(df["net_amount"].std())
    df["amount_z_rolling"] = df["amount_z_rolling"].fillna(0.0)

    logger.info("Built anomaly features: %d rows x %d cols", len(df), len(feat_cols))
    return df


def run_all_feature_engineering():
    """Run feature extraction for all pipelines and save to processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    rev_feat = build_revenue_features()
    save_csv(rev_feat, "revenue_features.csv", PROCESSED_DIR)

    sales_feat = build_sales_features()
    save_csv(sales_feat, "sales_features.csv", PROCESSED_DIR)

    inv_feat = build_inventory_features()
    save_csv(inv_feat, "inventory_features.csv", PROCESSED_DIR)

    profit_feat = build_profit_features()
    save_csv(profit_feat, "profit_features.csv", PROCESSED_DIR)

    exp_feat = build_expense_features()
    save_csv(exp_feat, "expense_features.csv", PROCESSED_DIR)

    anom_feat = build_anomaly_features()
    save_csv(anom_feat, "anomaly_features.csv", PROCESSED_DIR)

    logger.info("All feature engineering artifacts generated successfully.")


if __name__ == "__main__":
    run_all_feature_engineering()

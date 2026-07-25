"""
utils.py
========
Shared utility functions for the AI Financial Intelligence Platform ML module.

Provides common helpers for:
- File I/O
- Date and time utilities
- Logging configuration
- Metric computation
- Data validation
"""

import os
import json
import logging
import joblib
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT_DIR      = Path(__file__).resolve().parent.parent
DATASETS_DIR  = ROOT_DIR / "datasets"
RAW_DIR       = DATASETS_DIR / "raw"
PROCESSED_DIR = DATASETS_DIR / "processed"
SYNTHETIC_DIR = DATASETS_DIR / "synthetic"
MODELS_DIR    = ROOT_DIR / "models"
REPORTS_DIR   = ROOT_DIR / "reports"
CONFIGS_DIR   = ROOT_DIR / "configs"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a configured logger instance.

    Args:
        name:  Logger name (typically __name__ of calling module).
        level: Logging level (default INFO).

    Returns:
        Configured Logger object.
    """
    # TODO: Add file handler + structured JSON logging if needed
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s — %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def load_csv(filename: str, directory: Optional[Path] = None) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.

    Args:
        filename:  CSV filename (with or without .csv extension).
        directory: Directory to load from. Defaults to SYNTHETIC_DIR.

    Returns:
        Loaded DataFrame.

    Raises:
        FileNotFoundError: If file does not exist.
    """
    if directory is None:
        directory = SYNTHETIC_DIR

    if not filename.endswith(".csv"):
        filename += ".csv"

    path = directory / filename
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    # Auto-detect date columns by naming convention
    date_patterns = ['_date', '_at', 'moved_at', 'created_at']
    df = pd.read_csv(path)
    for col in df.columns:
        if any(col.endswith(p) for p in date_patterns):
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception:
                pass

    logger.info(f"Loaded {filename}: {len(df):,} rows x {len(df.columns)} columns")
    return df


def save_csv(df: pd.DataFrame, filename: str, directory: Optional[Path] = None,
             compress: bool = False) -> None:
    """
    Save a DataFrame to a CSV file.

    Args:
        df:        DataFrame to save.
        filename:  Output filename.
        directory: Target directory. Defaults to PROCESSED_DIR.
        compress:  If True, save as gzipped CSV.
    """
    if directory is None:
        directory = PROCESSED_DIR

    directory.mkdir(parents=True, exist_ok=True)

    if not filename.endswith(".csv"):
        filename += ".csv"

    path = directory / filename
    if compress:
        df.to_csv(str(path) + '.gz', index=False, compression='gzip')
        logger.info(f"Saved (compressed) {filename}.gz: {len(df):,} rows")
    else:
        df.to_csv(path, index=False)
        logger.info(f"Saved {filename}: {len(df):,} rows")


def save_model(model: Any, name: str, metadata: Optional[Dict] = None) -> Path:
    """
    Serialize a model artifact to the models/ directory using joblib.

    Args:
        model:    Trained model object.
        name:     Model name (e.g., 'revenue_xgboost').
        metadata: Optional dict of metadata to save alongside model.

    Returns:
        Path to saved model file.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = MODELS_DIR / f"{name}_{timestamp}.pkl"

    joblib.dump(model, model_path)

    if metadata:
        meta_path = MODELS_DIR / f"{name}_{timestamp}_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

    logger.info(f"Model saved: {model_path}")
    return model_path


def load_model(path: Union[str, Path]) -> Any:
    """
    Load a serialized model from disk using joblib.

    Args:
        path: Path to .pkl model file.

    Returns:
        Deserialized model object.
    """
    model = joblib.load(path)
    logger.info(f"Model loaded from: {path}")
    return model


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Root Mean Squared Error."""
    y_true, y_pred = np.array(y_true, dtype=float), np.array(y_pred, dtype=float)
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    return float(np.sqrt(np.mean((y_true[mask] - y_pred[mask]) ** 2)))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Mean Absolute Error."""
    y_true, y_pred = np.array(y_true, dtype=float), np.array(y_pred, dtype=float)
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask])))


def mape(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-8) -> float:
    """
    Compute Mean Absolute Percentage Error.

    Args:
        y_true:   Actual values.
        y_pred:   Predicted values.
        epsilon:  Small constant to avoid division by zero.

    Returns:
        MAPE as a percentage.
    """
    y_true, y_pred = np.array(y_true, dtype=float), np.array(y_pred, dtype=float)
    mask = (np.abs(y_true) > epsilon) & ~(np.isnan(y_true) | np.isnan(y_pred))
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Symmetric Mean Absolute Percentage Error."""
    y_true, y_pred = np.array(y_true, dtype=float), np.array(y_pred, dtype=float)
    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
    mask = denominator > 0
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / denominator[mask]) * 100)


def wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Weighted Absolute Percentage Error."""
    y_true, y_pred = np.array(y_true, dtype=float), np.array(y_pred, dtype=float)
    total = np.sum(np.abs(y_true))
    return float(np.sum(np.abs(y_true - y_pred)) / total * 100) if total > 0 else 0.0


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Compute all regression metrics in one call.

    Args:
        y_true: Actual values.
        y_pred: Predicted values.

    Returns:
        Dict with keys: rmse, mae, mape, smape, wape, r2.
    """
    y_true, y_pred = np.array(y_true, dtype=float), np.array(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        "rmse":  rmse(y_true, y_pred),
        "mae":   mae(y_true, y_pred),
        "mape":  mape(y_true, y_pred),
        "smape": smape(y_true, y_pred),
        "wape":  wape(y_true, y_pred),
        "r2":    round(r2, 4),
    }


# ---------------------------------------------------------------------------
# Date utilities
# ---------------------------------------------------------------------------

def add_date_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Extract time-based features from a date column.

    Args:
        df:       Input DataFrame.
        date_col: Name of the date column (must be parseable by pd.to_datetime).

    Returns:
        DataFrame with additional columns:
        year, month, quarter, day_of_week, week_of_year, is_month_end,
        is_quarter_end, is_year_end.
    """
    df = df.copy()
    dt = pd.to_datetime(df[date_col])

    df["year"]           = dt.dt.year
    df["month"]          = dt.dt.month
    df["quarter"]        = dt.dt.quarter
    df["day_of_week"]    = dt.dt.dayofweek   # 0=Monday
    df["week_of_year"]   = dt.dt.isocalendar().week.astype(int)
    df["is_month_end"]   = dt.dt.is_month_end.astype(int)
    df["is_quarter_end"] = dt.dt.is_quarter_end.astype(int)
    df["is_year_end"]    = dt.dt.is_year_end.astype(int)
    # Seasonal flags
    df["is_q4"]          = (df["quarter"] == 4).astype(int)  # holiday season
    df["is_q1"]          = (df["quarter"] == 1).astype(int)  # post-holiday dip
    df["is_weekend"]     = (df["day_of_week"] >= 5).astype(int)

    return df


def make_lag_features(df: pd.DataFrame, value_col: str,
                       lags: List[int], group_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Create lag features for a time-series column.

    Args:
        df:         Input DataFrame (must be sorted by time).
        value_col:  Column to create lags for.
        lags:       List of lag periods (e.g., [1, 2, 3, 12]).
        group_cols: Optional groupby columns (e.g., ['company_id', 'product_id']).

    Returns:
        DataFrame with added lag columns.
    """
    df = df.copy()

    for lag in lags:
        col_name = f"{value_col}_lag_{lag}"
        if group_cols:
            df[col_name] = df.groupby(group_cols)[value_col].shift(lag)
        else:
            df[col_name] = df[value_col].shift(lag)

    return df


def make_rolling_features(df: pd.DataFrame, value_col: str,
                           windows: List[int], group_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Create rolling mean and std features.

    Args:
        df:         Input DataFrame.
        value_col:  Column to roll over.
        windows:    List of window sizes (e.g., [3, 6, 12]).
        group_cols: Optional groupby columns.

    Returns:
        DataFrame with rolling mean and std columns.
    """
    df = df.copy()

    for w in windows:
        if group_cols:
            rolled = df.groupby(group_cols)[value_col].transform(
                lambda x: x.rolling(w, min_periods=1).mean()
            )
            df[f"{value_col}_roll_mean_{w}"] = rolled
            df[f"{value_col}_roll_std_{w}"]  = df.groupby(group_cols)[value_col].transform(
                lambda x: x.rolling(w, min_periods=2).std().fillna(0)
            )
        else:
            df[f"{value_col}_roll_mean_{w}"] = df[value_col].rolling(w, min_periods=1).mean()
            df[f"{value_col}_roll_std_{w}"]  = df[value_col].rolling(w, min_periods=2).std().fillna(0)

        # EWMA
        alpha = 2 / (w + 1)
        if group_cols:
            df[f"{value_col}_ewma_{w}"] = df.groupby(group_cols)[value_col].transform(
                lambda x: x.ewm(alpha=alpha, adjust=False).mean()
            )
        else:
            df[f"{value_col}_ewma_{w}"] = df[value_col].ewm(alpha=alpha, adjust=False).mean()

    return df


# ---------------------------------------------------------------------------
# Data validation
# ---------------------------------------------------------------------------

def validate_foreign_keys(child_df: pd.DataFrame, parent_df: pd.DataFrame,
                           child_col: str, parent_col: str = "id") -> bool:
    """
    Validate that all values in child_col exist in parent_col.

    Args:
        child_df:   Child DataFrame (e.g., sales).
        parent_df:  Parent DataFrame (e.g., customers).
        child_col:  FK column in child_df (e.g., 'customer_id').
        parent_col: PK column in parent_df (e.g., 'id').

    Returns:
        True if all FK values are valid, False otherwise.
    """
    valid_ids = set(parent_df[parent_col])
    child_ids = set(child_df[child_col].dropna())
    orphans   = child_ids - valid_ids

    if orphans:
        logger.warning(
            f"FK violation in {child_col}: {len(orphans)} orphan values found. "
            f"Examples: {list(orphans)[:5]}"
        )
        return False

    return True


def check_data_quality(df: pd.DataFrame, name: str) -> Dict[str, Any]:
    """
    Produce a data quality report for a DataFrame.

    Args:
        df:   DataFrame to inspect.
        name: Dataset name for reporting.

    Returns:
        Dict with: row_count, column_count, null_counts, duplicate_count, dtypes.
    """
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    ranges = {}
    for col in numeric_cols:
        ranges[col] = {
            'min': float(df[col].min()) if not df[col].isna().all() else None,
            'max': float(df[col].max()) if not df[col].isna().all() else None,
            'mean': float(df[col].mean()) if not df[col].isna().all() else None,
        }

    report = {
        "name":            name,
        "row_count":       len(df),
        "column_count":    len(df.columns),
        "null_counts":     df.isnull().sum().to_dict(),
        "null_pct":        (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        "duplicate_count": int(df.duplicated().sum()),
        "dtypes":          df.dtypes.astype(str).to_dict(),
        "numeric_ranges":  ranges,
    }
    return report

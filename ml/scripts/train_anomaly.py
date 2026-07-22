"""
train_anomaly.py
================
Train anomaly detection models for financial transaction data.

Supported models:
- Isolation Forest (primary)
- Local Outlier Factor (LOF)
- Statistical (Z-score + IQR — unsupervised baseline)
- Autoencoder (neural network — optional, future)

Usage:
    python scripts/train_anomaly.py --model isolation_forest
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import get_logger, load_csv, save_model, PROCESSED_DIR

logger = get_logger(__name__)


def load_anomaly_data(company_id: Optional[str] = None) -> pd.DataFrame:
    """
    Load and combine all transaction data for anomaly detection.

    Combines:
    - Sales (with net_amount as primary numeric signal)
    - Expenses (with amount)
    - Payments (with amount)
    - Stock movements (with quantity)

    Args:
        company_id: Filter to one company (all if None).

    Returns:
        Unified transaction DataFrame with engineered features:
        amount_zscore, time_gap_days, weekend_flag, large_round_number_flag.
    """
    # TODO: Load all 4 transaction tables
    # TODO: Normalize to common schema: {id, company_id, amount, date, type}
    # TODO: Compute z-scores per company
    # TODO: Compute time_gap_days (days since previous transaction)
    # TODO: weekend_flag = date.weekday() >= 5
    # TODO: large_round_number_flag = amount % 1000 == 0 and amount > 50000
    raise NotImplementedError("load_anomaly_data not implemented.")


def train_isolation_forest(
    X_train: pd.DataFrame,
    contamination: float = 0.01,
    n_estimators: int = 200,
    random_state: int = 42,
) -> Any:
    """
    Train an Isolation Forest anomaly detector.

    Isolation Forest isolates anomalies by randomly partitioning features.
    Anomalies require fewer splits to isolate (shorter path length).

    Args:
        X_train:       Feature matrix (no target needed — unsupervised).
        contamination: Proportion of anomalies expected in the data.
        n_estimators:  Number of trees in the ensemble.
        random_state:  Random seed for reproducibility.

    Returns:
        Trained IsolationForest model.
    """
    # TODO: from sklearn.ensemble import IsolationForest
    # TODO: model = IsolationForest(contamination=contamination, n_estimators=n_estimators, random_state=random_state)
    # TODO: model.fit(X_train)
    # TODO: return model
    raise NotImplementedError("Isolation Forest training not implemented.")


def train_local_outlier_factor(
    X_train: pd.DataFrame,
    n_neighbors: int = 20,
    contamination: float = 0.01,
) -> Any:
    """
    Train a Local Outlier Factor (LOF) anomaly detector.

    LOF measures local density deviation — anomalies have lower density
    than their neighbors.

    Note: LOF is a transductive method — it predicts on the training set.
          For novel detection, use novelty=True.

    Args:
        X_train:       Feature matrix.
        n_neighbors:   Number of neighbors for local density estimation.
        contamination: Expected fraction of outliers.

    Returns:
        Trained LocalOutlierFactor model.
    """
    # TODO: from sklearn.neighbors import LocalOutlierFactor
    # TODO: model = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination, novelty=True)
    # TODO: model.fit(X_train)
    # TODO: return model
    raise NotImplementedError("LOF training not implemented.")


def apply_zscore_detection(
    df: pd.DataFrame,
    amount_col: str = "amount",
    z_threshold: float = 3.0,
) -> pd.DataFrame:
    """
    Flag anomalies using Z-score statistical method.

    Records with |z_score| > z_threshold are flagged.

    Args:
        df:          Transaction DataFrame.
        amount_col:  Column to compute z-score on.
        z_threshold: Threshold for anomaly flagging.

    Returns:
        DataFrame with added columns: z_score, is_anomaly_zscore.
    """
    # TODO: Compute z-score per company: (amount - mean) / std
    # TODO: Flag: is_anomaly_zscore = abs(z_score) > z_threshold
    raise NotImplementedError("Z-score anomaly detection not implemented.")


def apply_iqr_detection(
    df: pd.DataFrame,
    amount_col: str = "amount",
    k: float = 1.5,
) -> pd.DataFrame:
    """
    Flag anomalies using IQR (Interquartile Range) method.

    Records outside [Q1 - k×IQR, Q3 + k×IQR] are flagged as anomalies.

    Args:
        df:         Transaction DataFrame.
        amount_col: Column to compute IQR on.
        k:          IQR multiplier (1.5 = standard, 3.0 = extreme outliers only).

    Returns:
        DataFrame with added columns: iqr_lower, iqr_upper, is_anomaly_iqr.
    """
    # TODO: Compute Q1, Q3, IQR per company
    # TODO: Flag outliers
    raise NotImplementedError("IQR anomaly detection not implemented.")


def run_training_pipeline(
    model_type: str = "isolation_forest",
    company_id: Optional[str] = None,
    contamination: float = 0.01,
    save: bool = True,
) -> Any:
    """
    Full anomaly detection training pipeline.

    Args:
        model_type:    'isolation_forest' | 'lof' | 'zscore' | 'iqr'.
        company_id:    Filter to one company (all if None).
        contamination: Expected anomaly fraction.
        save:          Whether to save model artifact.

    Returns:
        Trained model (or None for statistical methods).
    """
    logger.info(f"Anomaly training: model={model_type}, contamination={contamination}")
    # TODO: Load → engineer features → train → score → save
    raise NotImplementedError("Anomaly training pipeline not implemented.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train anomaly detection model.")
    parser.add_argument("--model", type=str, default="isolation_forest",
                        choices=["isolation_forest", "lof", "zscore", "iqr"])
    parser.add_argument("--contamination", type=float, default=0.01,
                        help="Expected fraction of anomalies (0.0–0.5).")
    parser.add_argument("--company",  type=str, default=None)
    parser.add_argument("--no-save",  action="store_true")
    args = parser.parse_args()

    run_training_pipeline(args.model, args.company, args.contamination, not args.no_save)


if __name__ == "__main__":
    main()

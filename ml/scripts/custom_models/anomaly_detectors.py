# -*- coding: utf-8 -*-
"""
anomaly_detectors.py
====================
Multi-Paradigm Anomaly Detection Models for Financial Transactions.

Implements:
1. RuleBasedAnomalyDetector: Domain rules (extreme amount, suspicious discount, high return).
2. RobustMADAnomalyDetector: Median Absolute Deviation (MAD) scoring robust to extreme outliers.
3. PCAReconstructionAnomalyDetector: Reconstruction error from low-rank PCA projection.
4. ContextAwareAnomalyDetector: Context-stratified z-score within company and weekday groupings.
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


class RuleBasedAnomalyDetector(BaseEstimator):
    """Domain Rule-Based Anomaly Detector for ERP Transactions."""

    def __init__(self, amount_threshold: float = 100000.0, discount_threshold: float = 0.40):
        self.amount_threshold = amount_threshold
        self.discount_threshold = discount_threshold

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Flag anomalies where rules are triggered (-1 = anomaly, 1 = normal)."""
        is_anom = np.zeros(len(df), dtype=bool)

        if isinstance(df, pd.DataFrame):
            if "net_amount" in df.columns:
                is_anom |= (df["net_amount"] > self.amount_threshold)
                is_anom |= (df["net_amount"] < 0)

            if "discount_pct" in df.columns:
                is_anom |= (df["discount_pct"] > self.discount_threshold)
        else:
            arr = np.asarray(df, dtype=float)
            if arr.ndim > 1:
                is_anom |= (arr[:, 0] > self.amount_threshold)
                is_anom |= (arr[:, 0] < 0)
                if arr.shape[1] > 1:
                    is_anom |= (arr[:, 1] > self.discount_threshold)
            else:
                is_anom |= (arr > self.amount_threshold)
                is_anom |= (arr < 0)

        return np.where(is_anom, -1, 1)


class RobustMADAnomalyDetector(BaseEstimator):
    """
    Robust Median Absolute Deviation (MAD) Anomaly Detector.
    z_mad = 0.6745 * |x - median(x)| / MAD
    Anomalous if z_mad > threshold (typically 3.0 or 3.5).
    """

    def __init__(self, threshold: float = 3.5):
        self.threshold = threshold
        self.median_: float = 0.0
        self.mad_: float = 1.0
        self.is_fitted_: bool = False

    def fit(self, X: pd.DataFrame, y=None):
        """Compute median and MAD on training transactions."""
        if isinstance(X, pd.DataFrame):
            vals = X["net_amount"].values.astype(float) if "net_amount" in X.columns else X.iloc[:, 0].values.astype(float)
        else:
            vals = np.asarray(X, dtype=float).ravel()

        self.median_ = float(np.median(vals))
        devs = np.abs(vals - self.median_)
        self.mad_ = float(np.median(devs))
        if self.mad_ < 1e-6:
            self.mad_ = float(np.std(vals)) + 1e-6

        self.is_fitted_ = True
        return self

    def decision_function(self, X: pd.DataFrame) -> np.ndarray:
        """Compute continuous negative outlier score (lower = more anomalous)."""
        if not self.is_fitted_:
            raise ValueError("Model is not fitted yet.")

        if isinstance(X, pd.DataFrame):
            vals = X["net_amount"].values.astype(float) if "net_amount" in X.columns else X.iloc[:, 0].values.astype(float)
        else:
            vals = np.asarray(X, dtype=float).ravel()

        z_mad = 0.6745 * np.abs(vals - self.median_) / self.mad_
        # Return negative score so lower values indicate anomalies (aligning with sklearn standard)
        return -z_mad

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Flag anomalies (-1 = anomaly, 1 = normal)."""
        scores = self.decision_function(X)
        return np.where(scores < -self.threshold, -1, 1)


class PCAReconstructionAnomalyDetector(BaseEstimator):
    """
    PCA Reconstruction Error Anomaly Detector.
    Projects transactions onto top k principal components; reconstruction error flags anomalies.
    """

    def __init__(self, n_components: int = 3, percentile_threshold: float = 95.0, random_state: int = 42):
        self.n_components = n_components
        self.percentile_threshold = percentile_threshold
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.pca: Optional[PCA] = None
        self.cutoff_error_: float = 1.0
        self.is_fitted_: bool = False

    def fit(self, X: pd.DataFrame, y=None):
        """Fit PCA and determine reconstruction error cutoff."""
        X_num = X.select_dtypes(include=[np.number]).fillna(0.0).values if isinstance(X, pd.DataFrame) else np.asarray(X, dtype=float)
        k = min(self.n_components, X_num.shape[1])
        self.pca = PCA(n_components=k, random_state=self.random_state)
        X_scaled = self.scaler.fit_transform(X_num)
        X_proj = self.pca.inverse_transform(self.pca.fit_transform(X_scaled))

        errors = np.sum((X_scaled - X_proj) ** 2, axis=1)
        self.cutoff_error_ = float(np.percentile(errors, self.percentile_threshold))
        self.is_fitted_ = True
        return self

    def decision_function(self, X: pd.DataFrame) -> np.ndarray:
        """Compute continuous negative reconstruction score."""
        if not self.is_fitted_:
            raise ValueError("Model is not fitted yet.")
        X_num = X.select_dtypes(include=[np.number]).fillna(0.0).values if isinstance(X, pd.DataFrame) else np.asarray(X, dtype=float)
        X_scaled = self.scaler.transform(X_num)
        X_proj = self.pca.inverse_transform(self.pca.transform(X_scaled))
        errors = np.sum((X_scaled - X_proj) ** 2, axis=1)
        return -errors

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Flag anomalies (-1 = anomaly, 1 = normal)."""
        scores = self.decision_function(X)
        return np.where(scores < -self.cutoff_error_, -1, 1)


class ContextAwareAnomalyDetector(BaseEstimator):
    """
    Context-Stratified Robust Anomaly Detector.
    Evaluates transactions relative to their specific company and weekday context.
    """

    def __init__(self, z_threshold: float = 3.0):
        self.z_threshold = z_threshold
        self.context_stats_: Dict[Tuple[str, int], Tuple[float, float]] = {}
        self.global_mean_: float = 15000.0
        self.global_std_: float = 5000.0
        self.is_fitted_: bool = False

    def fit(self, X: pd.DataFrame, y=None):
        """Compute stratified context means and standard deviations."""
        if not isinstance(X, pd.DataFrame):
            self.is_fitted_ = True
            return self

        amt_col = "net_amount" if "net_amount" in X.columns else X.columns[0]
        cid_col = "company_id" if "company_id" in X.columns else None
        dow_col = "day_of_week" if "day_of_week" in X.columns else None

        self.global_mean_ = float(X[amt_col].mean())
        self.global_std_ = float(X[amt_col].std()) + 1e-6

        if cid_col and dow_col:
            for (cid, dow), grp in X.groupby([cid_col, dow_col]):
                m = float(grp[amt_col].mean())
                s = float(grp[amt_col].std()) if len(grp) > 1 else self.global_std_
                self.context_stats_[(str(cid), int(dow))] = (m, max(s, 100.0))

        self.is_fitted_ = True
        return self

    def decision_function(self, X: pd.DataFrame) -> np.ndarray:
        """Compute stratified z-score per transaction."""
        if not self.is_fitted_:
            raise ValueError("Model is not fitted yet.")

        if not isinstance(X, pd.DataFrame):
            return np.zeros(len(X))

        amt_col = "net_amount" if "net_amount" in X.columns else X.columns[0]
        cid_col = "company_id" if "company_id" in X.columns else None
        dow_col = "day_of_week" if "day_of_week" in X.columns else None

        z_scores = []
        for _, row in X.iterrows():
            amt = float(row.get(amt_col, self.global_mean_))
            key = (str(row.get(cid_col, "")), int(row.get(dow_col, 0))) if cid_col and dow_col else None
            m, s = self.context_stats_.get(key, (self.global_mean_, self.global_std_)) if key else (self.global_mean_, self.global_std_)
            z = (amt - m) / s
            z_scores.append(z)

        return -np.abs(np.array(z_scores, dtype=float))

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Flag anomalies (-1 = anomaly, 1 = normal)."""
        scores = self.decision_function(X)
        return np.where(scores < -self.z_threshold, -1, 1)


class CatBoostAnomalyDetector(BaseEstimator):
    """
    Supervised Anomaly Detector using CatBoost with class imbalance compensation.
    predict: returns -1 for anomaly, 1 for normal.
    decision_function: returns higher positive values for normal, negative for anomaly.
    """
    def __init__(self, model=None, threshold: float = 0.80, feature_cols: Optional[List[str]] = None):
        self.model = model
        self.threshold = threshold
        self.feature_cols = feature_cols

    def predict(self, X) -> np.ndarray:
        if self.model is None:
            return np.ones(len(X), dtype=int)
        if isinstance(X, pd.DataFrame) and self.feature_cols:
            available_cols = [c for c in self.feature_cols if c in X.columns]
            X_in = X[available_cols] if len(available_cols) == len(self.feature_cols) else X
        else:
            X_in = X
        probs = self.model.predict_proba(X_in)[:, 1]
        return np.where(probs >= self.threshold, -1, 1)

    def decision_function(self, X) -> np.ndarray:
        if self.model is None:
            return np.zeros(len(X))
        if isinstance(X, pd.DataFrame) and self.feature_cols:
            available_cols = [c for c in self.feature_cols if c in X.columns]
            X_in = X[available_cols] if len(available_cols) == len(self.feature_cols) else X
        else:
            X_in = X
        probs = self.model.predict_proba(X_in)[:, 1]
        return float(self.threshold) - probs


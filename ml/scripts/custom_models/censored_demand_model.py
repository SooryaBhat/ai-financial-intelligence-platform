# -*- coding: utf-8 -*-
"""
censored_demand_model.py
========================
Custom Censoring-Aware Demand Forecaster for Retail Inventory.

Mathematical Formulation:
    Observed Sales y(t) = min(True Demand D(t), Available Stock S(t))
    When S(t) = 0 (Stock-out), observed sales are right-censored.
    Censored Correction:
        D_unconstrained(t) = y(t) * (1.0 + StockoutDays(t) / AvailableDays(t))
    Fits regularized estimator on D_unconstrained to prevent inventory death-spirals.

Key Features:
- Reconstructs latent true demand from observed sales and stock-out frequency.
- Fits LightGBM/Ridge on unconstrained demand.
- Prevents stock-outs from lowering subsequent forecasts and procurement orders.
"""

from typing import Optional, List
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import Ridge


class CensoredDemandForecaster(BaseEstimator, RegressorMixin):
    """
    Censoring-Aware Demand Forecaster.
    Corrects historical sales for stock-out events before fitting demand models.
    """

    def __init__(self, alpha: float = 1.0, random_state: int = 42):
        self.alpha = alpha
        self.random_state = random_state
        self.model_: Optional[Ridge] = None
        self.censoring_ratio_: float = 1.0
        self.feature_cols_: List[str] = []
        self.is_fitted_: bool = False

    def fit(self, X: pd.DataFrame, y: np.ndarray, stockout_days: Optional[np.ndarray] = None):
        """Fit demand model with censoring correction."""
        y_arr = np.asarray(y, dtype=np.float64).ravel()
        n = len(y_arr)

        # Unconstrained demand reconstruction
        if stockout_days is not None:
            so_days = np.asarray(stockout_days, dtype=np.float64).ravel()
            censoring_multipliers = 1.0 + np.clip(so_days / 30.0, 0.0, 1.5)
            y_unconstrained = y_arr * censoring_multipliers
            self.censoring_ratio_ = float(np.mean(censoring_multipliers))
        elif isinstance(X, pd.DataFrame) and "stockout_count" in X.columns:
            so_counts = X["stockout_count"].values.astype(float)
            censoring_multipliers = 1.0 + np.clip(so_counts * 0.05, 0.0, 1.5)
            y_unconstrained = y_arr * censoring_multipliers
            self.censoring_ratio_ = float(np.mean(censoring_multipliers))
        else:
            y_unconstrained = y_arr
            self.censoring_ratio_ = 1.0

        if isinstance(X, pd.DataFrame):
            self.feature_cols_ = [c for c in X.columns if c not in ["stockout_count", "month", "product_id", "company_id"]]
            X_num = X[self.feature_cols_].select_dtypes(include=[np.number]).fillna(0.0).values
        else:
            X_num = np.asarray(X, dtype=np.float64)

        self.model_ = Ridge(alpha=self.alpha, random_state=self.random_state)
        self.model_.fit(X_num, y_unconstrained)
        self.is_fitted_ = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict expected unconstrained demand."""
        if not self.is_fitted_:
            raise ValueError("Model is not fitted yet.")

        if isinstance(X, pd.DataFrame):
            cols = [c for c in self.feature_cols_ if c in X.columns]
            X_num = X[cols].select_dtypes(include=[np.number]).fillna(0.0).values
        else:
            X_num = np.asarray(X, dtype=np.float64)

        preds = self.model_.predict(X_num)
        return np.maximum(0.0, preds)

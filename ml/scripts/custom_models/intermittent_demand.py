# -*- coding: utf-8 -*-
"""
intermittent_demand.py
======================
Intermittent Demand Forecasting methods for slow-moving products and sporadic sales.

Implements:
1. Croston's Method (1972): Separates demand size and inter-arrival demand intervals.
2. Syntetos-Boylan Approximation (SBA, 2005): Corrects Croston's positive bias by multiplying
   by (1 - alpha / 2).

References:
- Croston, J. D. (1972). Forecasting and stock control for intermittent demands.
- Syntetos, A. A., & Boylan, J. E. (2005). The accuracy of intermittent demand estimates.
"""

from typing import Optional, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin


class CrostonMethod(BaseEstimator, RegressorMixin):
    """
    Croston's Method for intermittent demand forecasting.
    Decomposes demand into non-zero demand size (z) and inter-arrival intervals (p).
    """

    def __init__(self, alpha: float = 0.15, fallback_value: float = 1.0):
        self.alpha = float(np.clip(alpha, 0.01, 0.99))
        self.fallback_value = float(fallback_value)
        self.demand_level_: float = 0.0
        self.interval_level_: float = 1.0
        self.forecast_rate_: float = 0.0
        self.is_fitted_: bool = False

    def fit(self, X: Optional[np.ndarray], y: np.ndarray):
        """Fit Croston's parameters on historical demand series y."""
        y_arr = np.asarray(y, dtype=np.float64).ravel()
        if len(y_arr) == 0:
            self.forecast_rate_ = self.fallback_value
            self.is_fitted_ = True
            return self

        # Identify non-zero demand events
        non_zero_indices = np.where(y_arr > 0)[0]
        if len(non_zero_indices) == 0:
            self.forecast_rate_ = 0.0
            self.demand_level_ = 0.0
            self.interval_level_ = 1.0
            self.is_fitted_ = True
            return self

        # Initialize levels at first non-zero demand
        first_idx = non_zero_indices[0]
        z = float(y_arr[first_idx])
        p = float(first_idx + 1)
        prev_idx = first_idx

        # Update smoothing levels
        for idx in non_zero_indices[1:]:
            interval = float(idx - prev_idx)
            demand = float(y_arr[idx])
            z = self.alpha * demand + (1.0 - self.alpha) * z
            p = self.alpha * interval + (1.0 - self.alpha) * p
            prev_idx = idx

        self.demand_level_ = max(0.0, z)
        self.interval_level_ = max(1.0, p)
        self.forecast_rate_ = max(0.0, self.demand_level_ / self.interval_level_)
        self.is_fitted_ = True
        return self

    def predict(self, X: Union[np.ndarray, pd.DataFrame, int]) -> np.ndarray:
        """Predict expected demand rate for future steps."""
        if not self.is_fitted_:
            raise ValueError("Model is not fitted yet.")

        if isinstance(X, int):
            n_samples = X
        elif hasattr(X, "shape"):
            n_samples = len(X)
        else:
            n_samples = 1

        preds = np.full(n_samples, self.forecast_rate_, dtype=np.float64)
        return preds


class SBAMethod(BaseEstimator, RegressorMixin):
    """
    Syntetos-Boylan Approximation (SBA) for intermittent demand.
    Modifies Croston's forecast rate with factor (1 - alpha / 2) to eliminate positive bias.
    """

    def __init__(self, alpha: float = 0.15, fallback_value: float = 1.0):
        self.alpha = float(np.clip(alpha, 0.01, 0.99))
        self.fallback_value = float(fallback_value)
        self.croston = CrostonMethod(alpha=self.alpha, fallback_value=self.fallback_value)
        self.forecast_rate_: float = 0.0
        self.is_fitted_: bool = False

    def fit(self, X: Optional[np.ndarray], y: np.ndarray):
        """Fit SBA parameters on historical demand series y."""
        self.croston.fit(X, y)
        bias_correction = 1.0 - (self.alpha / 2.0)
        self.forecast_rate_ = max(0.0, self.croston.forecast_rate_ * bias_correction)
        self.is_fitted_ = True
        return self

    def predict(self, X: Union[np.ndarray, pd.DataFrame, int]) -> np.ndarray:
        """Predict expected debiased demand rate."""
        if not self.is_fitted_:
            raise ValueError("Model is not fitted yet.")

        if isinstance(X, int):
            n_samples = X
        elif hasattr(X, "shape"):
            n_samples = len(X)
        else:
            n_samples = 1

        preds = np.full(n_samples, self.forecast_rate_, dtype=np.float64)
        return preds

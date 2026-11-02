# -*- coding: utf-8 -*-
"""
recurring_expense_model.py
==========================
Custom Recurring vs. Irregular Operating Expense Forecaster.

Mathematical Formulation:
    TotalExpense(t) = RecurringBase(t) + IrregularComponent(t)
    RecurringBase(t) is estimated from low-pass rolling median of historical overhead (Rent, Salaries, Utilities).
    IrregularComponent(t) is modeled via regularized Ridge on transaction velocity and activity indicators.

Key Features:
- Separates structural fixed costs from volatile operational disbursements.
- Prevents over-fitting on one-off expense spikes.
- Guarantees strictly positive expense forecasts.
"""

from typing import Optional, List
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import Ridge


class RecurringExpenseForecaster(BaseEstimator, RegressorMixin):
    """
    Two-component Operating Expense Forecaster.
    Models recurring fixed overhead and irregular variable expenses separately.
    """

    def __init__(self, alpha: float = 1.0, random_state: int = 42):
        self.alpha = alpha
        self.random_state = random_state
        self.baseline_recurring_: float = 30000.0
        self.irregular_model_: Optional[Ridge] = None
        self.feature_cols_: List[str] = []
        self.is_fitted_: bool = False

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        """Fit recurring baseline and irregular component regressor."""
        y_arr = np.asarray(y, dtype=np.float64).ravel()
        n = len(y_arr)

        if isinstance(X, pd.DataFrame):
            self.feature_cols_ = [c for c in X.columns if c not in ["company_id", "category", "month", "total_expense"]]
            if "roll6_mean" in X.columns:
                recurring_base = X["roll6_mean"].values.astype(float)
            elif "lag_1" in X.columns:
                recurring_base = X["lag_1"].values.astype(float)
            else:
                recurring_base = np.full(n, np.median(y_arr))

            X_num = X[self.feature_cols_].select_dtypes(include=[np.number]).fillna(0.0).values
        else:
            X_num = np.asarray(X, dtype=np.float64)
            recurring_base = np.full(n, np.median(y_arr))

        self.baseline_recurring_ = float(np.median(y_arr))
        irregular_diff = y_arr - recurring_base

        self.irregular_model_ = Ridge(alpha=self.alpha, random_state=self.random_state)
        self.irregular_model_.fit(X_num, irregular_diff)

        self.is_fitted_ = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict total operating expenses as recurring base + irregular adjustment."""
        if not self.is_fitted_:
            raise ValueError("Model is not fitted yet.")

        n_samples = len(X)
        if isinstance(X, pd.DataFrame):
            if "roll6_mean" in X.columns:
                recurring_base = X["roll6_mean"].values.astype(float)
            elif "lag_1" in X.columns:
                recurring_base = X["lag_1"].values.astype(float)
            else:
                recurring_base = np.full(n_samples, self.baseline_recurring_)

            cols = [c for c in self.feature_cols_ if c in X.columns]
            X_num = X[cols].select_dtypes(include=[np.number]).fillna(0.0).values
        else:
            recurring_base = np.full(n_samples, self.baseline_recurring_)
            X_num = np.asarray(X, dtype=np.float64)

        irregular_pred = self.irregular_model_.predict(X_num)
        total_pred = np.maximum(500.0, recurring_base + irregular_pred)
        return total_pred

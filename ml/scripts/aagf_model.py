# -*- coding: utf-8 -*-
"""
aagf_model.py
=============
ALLADIN Adaptive Global Forecasting (AAGF).

A project-specific hybrid forecasting architecture engineered for Indian retail SMEs:
1. Feature Strategy:
   - Historical lags and past-only rolling statistics.
   - Indian retail festival indicators (Diwali, Dussehra, Eid, Holi, Q4 surges).
   - Business scale normalization to enable effective cross-business global learning.
2. Dual-Component Learning:
   - Component A (Seasonal Trend Anchor): Regularized Ridge regression capturing annual seasonality & macro momentum.
   - Component B (Nonlinear Interaction Engine): Constrained gradient-boosted tree (LightGBM/XGBoost) capturing complex non-linear shocks.
   - Component C (Adaptive Historical Anchor): Lag-1 / rolling seasonal persistence baseline.
3. Validation-Driven Blending:
   - Solves for optimal convex weights (alpha, beta, gamma >= 0, sum = 1.0) strictly on the chronological validation set.
4. Robust 3-Tier Fallback:
   - Graceful degradation when input history is missing, corrupted, or out-of-distribution.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from sklearn.linear_model import Ridge
from lightgbm import LGBMRegressor
from scipy.optimize import minimize


# Indian retail high-demand calendar months:
# Oct-Nov: Diwali, Dussehra, Dhanteras, Navratri shopping surge
# Jan: New Year, Makar Sankranti, Pongal, Republic Day sales
# Mar: Holi, Fiscal year-end clearance
# Aug: Raksha Bandhan, Independence Day sales
INDIAN_FESTIVAL_MONTHS = {1, 3, 8, 10, 11}


def add_aagf_features(df, date_col: str = "month") -> pd.DataFrame:
    """
    Enrich feature DataFrame with Indian retail calendar and momentum attributes.
    Strictly past-only and calendar-deterministic (zero future leakage).
    """
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    else:
        df = df.copy()
    if date_col in df.columns:
        dates = pd.to_datetime(df[date_col])
        months = dates.dt.month
        quarters = dates.dt.quarter
    elif "month_num" in df.columns:
        months = pd.to_numeric(df["month_num"], errors="coerce").fillna(1).astype(int)
        quarters = pd.to_numeric(df["quarter"], errors="coerce").fillna(1).astype(int) if "quarter" in df.columns else (months - 1) // 3 + 1
    else:
        months = pd.Series([1] * len(df))
        quarters = pd.Series([1] * len(df))

    # Indian Retail Festival & Peak Sales Season
    df["is_festival_season"] = months.isin(INDIAN_FESTIVAL_MONTHS).astype(float)
    df["is_diwali_q4"] = (quarters == 4).astype(float)
    df["is_q1_festive"] = (quarters == 1).astype(float)

    # Momentum indicator: ratio of lag_1 to rolling 3-month mean (past-only)
    if "lag_1" in df.columns and "roll3_mean" in df.columns:
        df["momentum_3m"] = (df["lag_1"] / (df["roll3_mean"] + 1e-6)).clip(0.2, 5.0)
    else:
        df["momentum_3m"] = 1.0

    return df


class ALLADINAdaptiveGlobalForecaster:
    """
    ALLADIN Adaptive Global Forecaster (AAGF).
    """

    def __init__(
        self,
        name: str = "AAGF-Revenue",
        lgbm_params: Optional[Dict[str, Any]] = None,
        ridge_alpha: float = 1.0,
        random_state: int = 42,
    ):
        self.name = name
        self.random_state = random_state
        self.ridge_alpha = ridge_alpha
        self.lgbm_params = lgbm_params or {
            "n_estimators": 100,
            "max_depth": 5,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "random_state": random_state,
            "verbose": -1,
        }

        # Sub-components
        self.trend_anchor = Ridge(alpha=self.ridge_alpha, random_state=random_state)
        self.nonlinear_engine = LGBMRegressor(**self.lgbm_params)

        # Blending weights [alpha (trend), beta (nonlinear), gamma (anchor)]
        self.weights = np.array([0.40, 0.40, 0.20], dtype=float)
        self.feature_cols: List[str] = []
        self.is_fitted: bool = False
        self.fallback_median: float = 1000.0

    EXCLUDED_COLS = {
        "company_id", "month", "date", "sale_date", "product_id", "category_id",
        "revenue", "quantity", "units_out", "net_profit", "total_expense",
        "health_score", "next_health_score", "is_anomaly", "is_anomaly_int", "target"
    }

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[np.ndarray] = None,
        anchor_col: str = "lag_1",
        feature_cols: Optional[List[str]] = None,
    ) -> "ALLADINAdaptiveGlobalForecaster":
        """
        Fit AAGF on training data and optimize blend weights strictly on validation set.
        Guarantees zero target leakage.
        """
        X_tr = add_aagf_features(X_train)
        if feature_cols is not None:
            # Add engineered features if requested
            self.feature_cols = [c for c in feature_cols if c not in self.EXCLUDED_COLS]
            for extra in ["is_festival_season", "is_diwali_q4", "is_q1_festive", "momentum_3m"]:
                if extra in X_tr.columns and extra not in self.feature_cols:
                    self.feature_cols.append(extra)
        else:
            self.feature_cols = [c for c in X_tr.columns if c not in self.EXCLUDED_COLS]

        self.fallback_median = float(np.median(y_train)) if len(y_train) > 0 else 1000.0

        X_tr_mat = X_tr[self.feature_cols].values
        y_tr = np.asarray(y_train, dtype=float)

        # 1. Fit Component A: Seasonal Trend Anchor (Ridge)
        self.trend_anchor.fit(X_tr_mat, y_tr)

        # 2. Fit Component B: Nonlinear Interaction Engine (LGBM)
        self.nonlinear_engine.fit(X_tr_mat, y_tr)

        # 3. Optimize Blending Weights on Validation Set (if provided)
        if X_val is not None and y_val is not None and len(y_val) > 0:
            X_v = add_aagf_features(X_val)
            X_v_mat = X_v[self.feature_cols].values
            y_v = np.asarray(y_val, dtype=float)

            pred_trend_val = np.maximum(0, self.trend_anchor.predict(X_v_mat))
            pred_lgb_val = np.maximum(0, self.nonlinear_engine.predict(X_v_mat))
            pred_anchor_val = np.maximum(0, X_v[anchor_col].values if anchor_col in X_v.columns else pred_trend_val)

            # Objective: Minimize validation WAPE
            def val_loss(w):
                w = np.array(w)
                w = w / np.sum(w)  # normalize to simplex
                pred = w[0] * pred_trend_val + w[1] * pred_lgb_val + w[2] * pred_anchor_val
                total_y = np.sum(np.abs(y_v))
                return float(np.sum(np.abs(y_v - pred)) / (total_y + 1e-8))

            init_w = [0.33, 0.33, 0.34]
            bounds = [(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)]
            res = minimize(val_loss, init_w, bounds=bounds, method="SLSQP")
            if res.success and np.sum(res.x) > 0:
                self.weights = res.x / np.sum(res.x)
            else:
                self.weights = np.array([0.45, 0.45, 0.10])

        self.is_fitted = True
        return self

    def predict(self, X, anchor_col: str = "lag_1") -> np.ndarray:
        """
        Generate predictions using the optimized AAGF ensemble blend with fallback.
        """
        if not self.is_fitted:
            raise RuntimeError("AAGF model is not fitted yet.")

        if isinstance(X, np.ndarray):
            if hasattr(self, "feature_cols") and X.shape[1] == len(self.feature_cols):
                X = pd.DataFrame(X, columns=self.feature_cols)
            else:
                X = pd.DataFrame(X)

        X_df = add_aagf_features(X)

        # Ensure all required features are present; fill missing with 0
        for col in self.feature_cols:
            if col not in X_df.columns:
                X_df[col] = 0.0

        X_mat = X_df[self.feature_cols].values
        # Sanitize NaNs or infinite values before passing to estimators
        X_mat = np.nan_to_num(X_mat, nan=0.0, posinf=0.0, neginf=0.0)

        # Component predictions
        pred_trend = np.maximum(0, self.trend_anchor.predict(X_mat))
        pred_lgb = np.maximum(0, self.nonlinear_engine.predict(X_mat))
        if anchor_col in X_df.columns:
            raw_anchor = pd.to_numeric(X_df[anchor_col], errors="coerce").fillna(0.0).values
            pred_anchor = np.maximum(0.0, raw_anchor)
        else:
            pred_anchor = pred_trend

        w = self.weights
        ensemble_pred = w[0] * pred_trend + w[1] * pred_lgb + w[2] * pred_anchor

        # 3-Tier Fallback handling for NaNs or corrupted inputs
        nan_mask = np.isnan(ensemble_pred) | np.isinf(ensemble_pred) | (ensemble_pred <= 0)
        if np.any(nan_mask):
            ensemble_pred[nan_mask] = np.where(
                ~np.isnan(pred_anchor[nan_mask]) & (pred_anchor[nan_mask] > 0),
                pred_anchor[nan_mask],
                self.fallback_median
            )

        return np.maximum(0.0, ensemble_pred)

# -*- coding: utf-8 -*-
"""
health_scorers.py
=================
Multi-Paradigm Business Health Scorers & Diagnostic Indices.

Implements:
1. TrafficLightScorer: Rule-based Green/Amber/Red operational alerts.
2. WeightedScorecard: Transparent weighted sum of MinMax-scaled financial KPIs.
3. PCAHealthIndex: Unsupervised dimensionality reduction capturing dominant health variance.
4. WeakestLinkScorer: Bottleneck-penalized score based on Liebig's law of the minimum.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


class TrafficLightScorer(BaseEstimator):
    """Rule-based Traffic Light (Green / Amber / Red) Health Categorizer."""

    def __init__(self):
        pass

    def evaluate_row(self, row: Dict[str, float]) -> str:
        """Evaluate traffic light status for a single business period."""
        margin = row.get("profit_margin", 0.10)
        exp_ctrl = row.get("expense_control", 0.50)
        collection = row.get("payment_collection", 0.85)

        # Red triggers
        if margin < -0.10 or exp_ctrl < 0.20 or collection < 0.50:
            return "RED_CRITICAL"
        # Amber triggers
        if margin < 0.05 or exp_ctrl < 0.40 or collection < 0.70:
            return "AMBER_WATCHLIST"
        # Otherwise Green
        return "GREEN_HEALTHY"

    def predict(self, df: pd.DataFrame) -> List[str]:
        """Classify each row into Traffic Light categories."""
        return [self.evaluate_row(row) for _, row in df.iterrows()]


class WeightedScorecard(BaseEstimator):
    """Transparent Weighted Multi-KPI Financial Health Scorecard (0-100)."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "revenue_growth": 0.25,
            "profit_margin": 0.25,
            "expense_control": 0.20,
            "inventory_turnover": 0.15,
            "payment_collection": 0.15,
        }
        self.ranges = {
            "revenue_growth": [-0.50, 1.00],
            "profit_margin": [-0.20, 0.40],
            "expense_control": [0.00, 1.00],
            "inventory_turnover": [0.00, 10.00],
            "payment_collection": [0.00, 1.00],
        }

    def _scale(self, val: float, min_v: float, max_v: float) -> float:
        if max_v <= min_v:
            return 50.0
        norm = (val - min_v) / (max_v - min_v)
        return float(np.clip(norm * 100.0, 0.0, 100.0))

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Compute composite 0-100 health score."""
        scores = []
        for _, row in df.iterrows():
            total = 0.0
            for kpi, w in self.weights.items():
                val = row.get(kpi, 0.5)
                r = self.ranges.get(kpi, [0.0, 1.0])
                total += self._scale(val, r[0], r[1]) * w
            scores.append(round(total, 1))
        return np.array(scores, dtype=np.float64)


class PCAHealthIndex(BaseEstimator):
    """Unsupervised PCA-derived Financial Health Index."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=1, random_state=random_state)
        self.feature_cols_: List[str] = [
            "revenue_growth", "profit_margin", "expense_control",
            "inventory_turnover", "payment_collection"
        ]
        self.is_fitted_: bool = False

    def fit(self, df: pd.DataFrame, y=None):
        """Fit PCA on standardized KPI inputs."""
        X = df[self.feature_cols_].select_dtypes(include=[np.number]).fillna(0.0).values
        X_scaled = self.scaler.fit_transform(X)
        self.pca.fit(X_scaled)
        self.is_fitted_ = True
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Transform KPIs into 0-100 normalized first principal component score."""
        if not self.is_fitted_:
            raise ValueError("Model is not fitted yet.")
        X = df[self.feature_cols_].select_dtypes(include=[np.number]).fillna(0.0).values
        X_scaled = self.scaler.transform(X)
        comp1 = self.pca.transform(X_scaled).ravel()
        # Scale to 0-100
        min_v, max_v = np.min(comp1), np.max(comp1)
        if max_v <= min_v:
            return np.full(len(comp1), 50.0)
        norm = (comp1 - min_v) / (max_v - min_v) * 100.0
        return np.round(norm, 1)


class WeakestLinkScorer(BaseEstimator):
    """
    Liebig's Law of the Minimum Health Scorer.
    Penalizes businesses where a single critical metric (e.g. collection or margin) fails,
    preventing strong metrics from masking imminent insolvency.
    """

    def __init__(self, base_scorer: Optional[WeightedScorecard] = None, bottleneck_weight: float = 0.40):
        self.base_scorer = base_scorer or WeightedScorecard()
        self.bottleneck_weight = bottleneck_weight

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Compute weakest-link penalized health score."""
        composite_scores = self.base_scorer.predict(df)
        final_scores = []
        for i, (_, row) in enumerate(df.iterrows()):
            sub_scores = []
            for kpi, r in self.base_scorer.ranges.items():
                val = row.get(kpi, 0.5)
                sub_scores.append(self.base_scorer._scale(val, r[0], r[1]))

            min_score = min(sub_scores) if sub_scores else 50.0
            # Blend standard weighted score with bottleneck penalty
            blended = (1.0 - self.bottleneck_weight) * composite_scores[i] + self.bottleneck_weight * min_score
            final_scores.append(round(blended, 1))

        return np.array(final_scores, dtype=np.float64)

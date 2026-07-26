"""
Singleton ML Model Loader.
Loads all serialized machine learning models once during application startup and caches them in memory.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
import joblib

from app.core.logging import logger


class ModelLoader:
    """
    Thread-safe Model Loader Singleton.
    Manages in-memory cache of trained ML models and feature metadata.
    """

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._meta: Dict[str, Any] = {}
        self._is_loaded: bool = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def _resolve_models_dir(self) -> Path:
        """Find the ml/models directory across possible execution contexts."""
        candidates = [
            Path(os.getcwd()) / "ml" / "models",
            Path(os.getcwd()).parent / "ml" / "models",
            Path(__file__).resolve().parents[3] / "ml" / "models",
            Path(__file__).resolve().parents[2] / "ml" / "models",
        ]
        for p in candidates:
            if p.exists() and p.is_dir():
                return p
        # Fallback default
        return candidates[0]

    def load_all_models(self) -> None:
        """Load all trained machine learning artifacts into memory once at startup."""
        if self._is_loaded:
            logger.info("[ML ModelLoader] Models already loaded in memory.")
            return

        models_dir = self._resolve_models_dir()
        logger.info("[ML ModelLoader] Loading trained model artifacts from: {}", models_dir)

        model_files = {
            "revenue_xgboost": "revenue_forecasting_xgboost.pkl",
            "revenue_sarima": "revenue_forecasting_sarima.pkl",
            "sales_xgb_product": "sales_forecasting_xgb_product.pkl",
            "sales_lgb_product": "sales_forecasting_lgb_product.pkl",
            "sales_xgb_category": "sales_forecasting_xgb_category.pkl",
            "inventory_demand": "inventory_demand_xgboost.pkl",
            "profit_prediction": "profit_prediction_xgboost.pkl",
            "expense_xgboost": "expense_prediction_xgboost.pkl",
            "expense_linear_regression": "expense_prediction_linear_regression.pkl",
            "health_score_pipeline": "health_score_pipeline.pkl",
            "anomaly_detection": "anomaly_detection_isolation_forest.pkl",
        }

        meta_files = {
            "revenue_meta": "revenue_feature_meta.json",
            "sales_meta": "sales_feature_meta.json",
            "inventory_meta": "inventory_feature_meta.json",
            "profit_meta": "profit_feature_meta.json",
            "expense_meta": "expense_feature_meta.json",
            "health_config": "health_score_config.json",
            "anomaly_config": "anomaly_detection_lof_config.json",
            "model_registry": "model_registry.json",
        }

        # 1. Load PKL models
        loaded_count = 0
        for key, fname in model_files.items():
            path = models_dir / fname
            if path.exists():
                try:
                    obj = joblib.load(path)
                    self._models[key] = obj
                    loaded_count += 1
                    logger.info("[ML ModelLoader] Successfully loaded model: {}", fname)
                except Exception as e:
                    logger.error("[ML ModelLoader] Failed to load model {}: {}", fname, e)
            else:
                logger.warning("[ML ModelLoader] Model file missing: {}", path)

        # 2. Load JSON configs & metadata
        for key, fname in meta_files.items():
            path = models_dir / fname
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self._meta[key] = json.load(f)
                except Exception as e:
                    logger.error("[ML ModelLoader] Failed to load metadata {}: {}", fname, e)

        self._is_loaded = True
        logger.info("[ML ModelLoader] Startup loading complete: {}/{} models active.", loaded_count, len(model_files))

    def get_model(self, key: str) -> Optional[Any]:
        """Retrieve a cached model artifact by key."""
        if not self._is_loaded:
            self.load_all_models()
        return self._models.get(key)

    def get_meta(self, key: str) -> Optional[Any]:
        """Retrieve cached feature metadata or config by key."""
        if not self._is_loaded:
            self.load_all_models()
        return self._meta.get(key)


# Global singleton instance
model_loader = ModelLoader()


def get_model_loader() -> ModelLoader:
    """FastAPI Dependency for accessing ModelLoader singleton."""
    if not model_loader.is_loaded:
        model_loader.load_all_models()
    return model_loader

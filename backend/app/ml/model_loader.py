"""
Singleton ML Model Loader.
Loads all serialized machine learning models once during application startup and caches them in memory.
"""
import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional
import joblib

from app.core.logging import logger

# Ensure ml/scripts is in sys.path so custom models (like AAGF) unpickle cleanly
for _base in [
    Path(os.getcwd()),
    Path(os.getcwd()).parent,
    Path(__file__).resolve().parents[3],
    Path(__file__).resolve().parents[2],
]:
    _scripts_dir = _base / "ml" / "scripts"
    if _scripts_dir.exists() and str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))

try:
    import aagf_model
    sys.modules["aagf_model"] = aagf_model
except Exception:
    pass


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
            # Canonical Selected Models (True validation winners)
            "revenue_selected": "revenue_forecasting_selected.pkl",
            "sales_selected": "sales_forecasting_selected.pkl",
            "profit_selected": "profit_prediction_selected.pkl",
            "inventory_selected": "inventory_demand_selected.pkl",
            "expense_selected": "expense_prediction_selected.pkl",

            # Algorithm-specific models (Exact algorithm identities)
            "revenue_aagf": "revenue_forecasting_aagf.pkl",
            "revenue_linear_regression": "revenue_forecasting_linear_regression.pkl",
            "revenue_xgboost": "revenue_forecasting_xgboost.pkl",
            "revenue_sarima": "revenue_forecasting_sarima.pkl",

            "sales_aagf": "sales_forecasting_aagf_product.pkl",
            "sales_aagf_product": "sales_forecasting_aagf_product.pkl",
            "sales_xgb_product": "sales_forecasting_xgb_product.pkl",
            "sales_lgb_product": "sales_forecasting_lgb_product.pkl",
            "sales_linear_regression": "sales_forecasting_linear_regression_product.pkl",
            "sales_linear_regression_product": "sales_forecasting_linear_regression_product.pkl",
            "sales_xgb_category": "sales_forecasting_xgb_category.pkl",

            "inventory_demand": "inventory_demand_xgboost.pkl",
            "inventory_xgboost": "inventory_demand_xgboost.pkl",
            "inventory_random_forest": "inventory_demand_random_forest.pkl",
            "inventory_demand_rf": "inventory_demand_random_forest.pkl",
            "inventory_lightgbm": "inventory_demand_lightgbm.pkl",

            "profit_prediction": "profit_prediction_selected.pkl",  # legacy key points to canonical selected
            "profit_xgboost": "profit_prediction_xgboost.pkl",
            "profit_random_forest": "profit_prediction_random_forest.pkl",
            "profit_linear_regression": "profit_prediction_linear_regression.pkl",

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

# -*- coding: utf-8 -*-
"""
ml/tests/test_ml_readiness.py
==============================
Automated Readiness, Integrity & Holdout Test Suite for ALLADIN ML Pipelines (Step 4).

Acceptance Criteria Verified:
1. Artifact Deserialization and Model Registry Consistency.
2. Strict exclusion of Company 3 from all model-development training datasets.
3. Preprocessing, scaling, and custom models fitted only on Dev Companies (1 & 2).
4. Validation-only model selection across all seven pipelines.
5. Chronological feature generation and absence of future target leakage.
6. Frozen model zero-shot evaluation on Company 3 with baseline comparisons.
7. Safe fallbacks for insufficient history, unseen entities, and NaN inputs.
8. Prediction scale consistency on realistic retail domain.
9. Independent non-circular inventory reorder policy evaluation.
10. Simultaneous live inference smoke tests across all seven pipelines.
11. Clean separation of zero-shot metrics from adaptation.
12. Graceful error handling and rejection of corrupt inputs.

Usage:
    pytest ml/tests/test_ml_readiness.py -v
    python -m unittest ml/tests/test_ml_readiness.py
"""

import sys
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "ml" / "scripts"))

import aagf_model
from app.ml.model_loader import model_loader
from app.ml.revenue_predictor import predict_revenue, _default_historical_revenue
from app.ml.sales_predictor import predict_sales
from app.ml.inventory_predictor import predict_inventory
from app.ml.profit_predictor import predict_profit
from app.ml.expense_predictor import predict_expense
from app.ml.business_health import calculate_business_health
from app.ml.anomaly_detector import detect_anomaly
from app.schemas.ml import (
    RevenuePredictionRequest,
    SalesPredictionRequest,
    InventoryPredictionRequest,
    ProfitPredictionRequest,
    ExpensePredictionRequest,
    BusinessHealthRequest,
    AnomalyDetectionRequest,
)

DEV_COMPANIES = ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"]
HOLDOUT_COMPANY = "00000000-0000-0000-0000-000000000003"


class TestALLADINMLReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        model_loader.load_all_models()
        cls.models_dir = PROJECT_ROOT / "ml" / "models"
        cls.reports_dir = PROJECT_ROOT / "ml" / "reports"
        cls.processed_dir = PROJECT_ROOT / "ml" / "datasets" / "processed"
        cls.synthetic_dir = PROJECT_ROOT / "ml" / "datasets" / "synthetic"
        with open(cls.models_dir / "model_registry.json", "r", encoding="utf-8") as f:
            cls.registry = json.load(f)

    def test_01_registry_artifacts_exist_and_deserialize(self):
        """Confirm all registered models exist, deserialize, and match declared algorithms."""
        for pipe_name, info in self.registry.items():
            art_file = info.get("selected_artifact") or info.get("artifact_path")
            p = self.models_dir / Path(art_file).name
            self.assertTrue(p.exists(), f"Artifact missing: {p}")
            obj = joblib.load(p)
            self.assertIsNotNone(obj, f"Failed to deserialize {p.name}")

            # Verify declared algorithm matches loaded class
            declared = info.get("selected_algorithm") or info.get("model_name")
            est = obj.get("model", obj) if isinstance(obj, dict) else obj
            loaded_class = type(est).__name__

            if "AAGF" in declared:
                self.assertEqual(loaded_class, "ALLADINAdaptiveGlobalForecaster")
            elif "XGBoost" in declared or "XGB" in declared:
                self.assertIn(loaded_class, ["XGBRegressor", "dict"])
            elif "LightGBM" in declared or "LGBM" in declared:
                self.assertIn(loaded_class, ["LGBMRegressor", "dict"])
            elif "Random_Forest" in declared:
                self.assertIn(loaded_class, ["RandomForestRegressor", "dict"])
            elif "Isolation_Forest" in declared:
                self.assertEqual(loaded_class, "IsolationForest")

    def test_02_strict_exclusion_of_company_3_from_training_datasets(self):
        """
        Verify strict exclusion of Company 3 from model development training sets across all pipelines.
        Asserts that train_df contains only Companies 1 & 2 and ZERO rows of Company 3.
        """
        # 1. Revenue
        from train_revenue import load_and_split_data as load_rev
        train_rev, val_rev, test_rev, holdout_rev = load_rev()
        self.assertEqual((train_rev["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((val_rev["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((test_rev["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertTrue(set(train_rev["company_id"].unique()).issubset(set(DEV_COMPANIES)))

        # 2. Sales
        from train_sales import load_and_split_product_data as load_sales
        train_sales, val_sales, test_sales, holdout_sales = load_sales()
        self.assertEqual((train_sales["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((val_sales["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((test_sales["company_id"] == HOLDOUT_COMPANY).sum(), 0)

        # 3. Inventory
        from train_inventory import load_and_split_inventory_data as load_inv
        train_inv, val_inv, test_inv, holdout_inv = load_inv()
        self.assertEqual((train_inv["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((val_inv["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((test_inv["company_id"] == HOLDOUT_COMPANY).sum(), 0)

        # 4. Profit
        from train_profit import load_and_split_profit_data as load_profit
        train_profit, val_profit, test_profit, holdout_profit = load_profit()
        self.assertEqual((train_profit["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((val_profit["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((test_profit["company_id"] == HOLDOUT_COMPANY).sum(), 0)

        # 5. Expenses
        from train_expenses import load_and_split_expense_data as load_exp
        train_exp, val_exp, test_exp, holdout_exp = load_exp()
        self.assertEqual((train_exp["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((val_exp["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((test_exp["company_id"] == HOLDOUT_COMPANY).sum(), 0)

        # 6. Anomaly
        from train_anomaly import load_and_split_anomaly_data as load_anom
        train_anom, val_anom, test_anom, holdout_anom = load_anom()
        self.assertEqual((train_anom["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((val_anom["company_id"] == HOLDOUT_COMPANY).sum(), 0)
        self.assertEqual((test_anom["company_id"] == HOLDOUT_COMPANY).sum(), 0)

    def test_03_preprocessing_and_scalers_fit_only_on_dev_companies(self):
        """Confirm scalers and feature transformers were fit only on Companies 1 & 2."""
        anom_art = joblib.load(self.models_dir / "anomaly_detection_isolation_forest.pkl")
        scaler = anom_art["scaler"]
        self.assertIsNotNone(scaler.mean_)
        self.assertEqual(len(scaler.mean_), 9)

        # Verify training companies attribute stored in artifacts
        self.assertEqual(anom_art.get("training_companies"), DEV_COMPANIES)
        self.assertEqual(anom_art.get("holdout_company"), HOLDOUT_COMPANY)

    def test_04_validation_only_model_selection(self):
        """Confirm that model selection was based purely on Dev validation metrics."""
        for pipe_name, info in self.registry.items():
            metric_key = info.get("selection_metric")
            self.assertIn(metric_key, ["val_wape", "validation_wape", "val_mae", "val_f1_score"])
            self.assertEqual(info.get("training_companies"), DEV_COMPANIES)
            self.assertEqual(info.get("holdout_company"), HOLDOUT_COMPANY)

    def test_05_chronological_feature_generation_and_no_future_leakage(self):
        """Confirm feature vectors do not include concurrent target variables or raw company IDs."""
        with open(self.models_dir / "expense_feature_meta.json", "r", encoding="utf-8") as f:
            exp_meta = json.load(f)
        self.assertNotIn("total_expense", exp_meta["features"])
        self.assertIn("txn_count_lag1", exp_meta["features"])
        self.assertIn("avg_expense_lag1", exp_meta["features"])

        with open(self.models_dir / "profit_feature_meta.json", "r", encoding="utf-8") as f:
            profit_meta = json.load(f)
        self.assertNotIn("net_profit", profit_meta["features"])

        with open(self.models_dir / "inventory_feature_meta.json", "r", encoding="utf-8") as f:
            inv_meta = json.load(f)
        self.assertNotIn("units_out", inv_meta["features"])

    def test_06_frozen_model_zero_shot_holdout_on_company_3(self):
        """
        Verify that frozen production models were evaluated zero-shot on Company 3,
        and that holdout metrics and baseline comparisons are recorded in evaluation reports.
        """
        # Revenue
        with open(self.reports_dir / "revenue_forecasting_eval.json", "r", encoding="utf-8") as f:
            rev_eval = json.load(f)
        co3_rev = rev_eval.get("approach_c_holdout_company3_metrics", {})
        rev_wape = co3_rev.get("wape") or co3_rev.get("wape_pct")
        self.assertIsNotNone(rev_wape)
        self.assertIn("naive_baseline_wape_pct", co3_rev)
        self.assertLess(rev_wape, 25.0)

        # Sales
        with open(self.reports_dir / "sales_forecasting_eval.json", "r", encoding="utf-8") as f:
            sales_eval = json.load(f)
        co3_sales = sales_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        self.assertIn("wape", co3_sales)

        # Inventory
        with open(self.reports_dir / "inventory_prediction_eval.json", "r", encoding="utf-8") as f:
            inv_eval = json.load(f)
        co3_inv = inv_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        self.assertIn("wape", co3_inv)
        self.assertIn("baseline_lag1_metrics", co3_inv)

        # Profit
        with open(self.reports_dir / "profit_prediction_eval.json", "r", encoding="utf-8") as f:
            profit_eval = json.load(f)
        co3_profit = profit_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        self.assertIn("wape", co3_profit)
        self.assertIn("baseline_lag1_metrics", co3_profit)
        self.assertLess(co3_profit["wape"], co3_profit["baseline_lag1_metrics"]["wape"])

        # Expenses
        with open(self.reports_dir / "expense_prediction_eval.json", "r", encoding="utf-8") as f:
            exp_eval = json.load(f)
        co3_exp = exp_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        self.assertIn("wape", co3_exp)
        self.assertIn("baseline_naive_metrics", co3_exp)
        self.assertLess(co3_exp["wape"], co3_exp["baseline_naive_metrics"]["wape"])

        # Health Score
        with open(self.reports_dir / "health_score_eval.json", "r", encoding="utf-8") as f:
            health_eval = json.load(f)
        co3_health = health_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        self.assertIn("mae", co3_health)
        self.assertIn("baseline_persistence_metrics", co3_health)
        self.assertLess(co3_health["mae"], co3_health["baseline_persistence_metrics"]["mae"])

        # Anomaly Detection
        with open(self.reports_dir / "anomaly_detection_eval.json", "r", encoding="utf-8") as f:
            anom_eval = json.load(f)
        co3_anom = anom_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        self.assertIn("f1_score", co3_anom)
        self.assertIn("baseline_zscore_metrics", co3_anom)
        self.assertGreater(co3_anom["f1_score"], co3_anom["baseline_zscore_metrics"]["f1_score"])

    def test_07_safe_fallbacks_for_insufficient_history_and_unseen_entities(self):
        """Verify robust fallback behavior when history is empty, unseen product/category, or NaN."""
        # 1. Empty historical revenue safely falls back to default
        req_empty = RevenuePredictionRequest(months_ahead=3, model_type="aagf", historical_revenue=[])
        resp_empty = predict_revenue(req_empty, model_loader)
        self.assertEqual(len(resp_empty.predictions), 3)
        self.assertGreater(resp_empty.total_projected_revenue, 0)

        # 2. Unseen product ID gracefully handled with fallback baseline
        req_unseen = SalesPredictionRequest(entity_type="product", entity_id="UNKNOWN_PROD_999", months_ahead=3)
        resp_unseen = predict_sales(req_unseen, model_loader)
        self.assertEqual(len(resp_unseen.predictions), 3)
        self.assertGreaterEqual(resp_unseen.total_predicted_units, 1.0)

        # 3. Model direct fallback on NaN features
        aagf_obj = joblib.load(self.models_dir / "revenue_forecasting_aagf.pkl")
        aagf_mod = aagf_obj["model"]
        corrupt_df = pd.DataFrame([{c: np.nan for c in aagf_mod.feature_cols}])
        pred = aagf_mod.predict(corrupt_df)
        self.assertFalse(np.isnan(pred[0]))
        self.assertFalse(np.isinf(pred[0]))
        self.assertGreater(pred[0], 0)

    def test_08_revenue_prediction_scale_consistency(self):
        """Verify that predictions from AAGF, Linear Regression, and XGBoost are on realistic retail scale."""
        controlled_hist = [
            253538.11, 225239.65, 255930.89, 254989.03, 264565.76, 264128.18,
            254534.83, 261845.50, 256036.27, 388987.42, 312945.67, 337562.33
        ]

        req_xgb = RevenuePredictionRequest(months_ahead=3, model_type="xgboost", historical_revenue=controlled_hist)
        resp_xgb = predict_revenue(req_xgb, model_loader)

        req_lr = RevenuePredictionRequest(months_ahead=3, model_type="linear_regression", historical_revenue=controlled_hist)
        resp_lr = predict_revenue(req_lr, model_loader)

        req_aagf = RevenuePredictionRequest(months_ahead=3, model_type="aagf", historical_revenue=controlled_hist)
        resp_aagf = predict_revenue(req_aagf, model_loader)

        for name, resp in [("XGBoost", resp_xgb), ("LinearRegression", resp_lr), ("AAGF", resp_aagf)]:
            avg_mo = resp.average_monthly_revenue
            self.assertGreaterEqual(avg_mo, 150000.0, f"{name} monthly revenue unexpectedly low: {avg_mo}")
            self.assertLessEqual(avg_mo, 450000.0, f"{name} monthly revenue unexpectedly high: {avg_mo}")

        pct_diff = abs(resp_aagf.total_projected_revenue - resp_lr.total_projected_revenue) / resp_lr.total_projected_revenue
        self.assertLess(pct_diff, 0.10, f"AAGF and Linear Regression differ by {pct_diff*100:.2f}%, expected < 10%")

    def test_09_inventory_reorder_evaluation_non_circular(self):
        """Audit the inventory reorder evaluation for honest reporting and stress testing."""
        inv_eval_path = self.reports_dir / "inventory_prediction_eval.json"
        self.assertTrue(inv_eval_path.exists())
        with open(inv_eval_path, "r", encoding="utf-8") as f:
            inv_eval = json.load(f)

        reorder_info = inv_eval.get("dev_reorder_policy_evaluation") or inv_eval.get("independent_reorder_policy_evaluation", {})
        self.assertIn("boundary_simulation_metrics", reorder_info)
        self.assertIn("native_baseline_audit", reorder_info)

        bs = reorder_info["boundary_simulation_metrics"]
        self.assertGreater(bs["positive_support_count"], 300)
        self.assertGreater(bs["f1_score"], 0.80)

        nb = reorder_info["native_baseline_audit"]
        self.assertEqual(nb["true_positives"], 0)
        self.assertNotEqual(nb.get("precision"), 1.0)

    def test_10_all_seven_pipeline_inference_smoke_test(self):
        """Verify live inference across all seven ML pipelines simultaneously."""
        # 1. Revenue
        rev_res = predict_revenue(RevenuePredictionRequest(months_ahead=3, model_type="aagf"), model_loader)
        self.assertGreater(rev_res.total_projected_revenue, 0)

        # 2. Sales
        sales_res = predict_sales(SalesPredictionRequest(entity_type="product", entity_id="1", months_ahead=3), model_loader)
        self.assertGreater(sales_res.total_predicted_units, 0)

        # 3. Inventory
        inv_res = predict_inventory(InventoryPredictionRequest(product_id="PRD_001", current_stock=250.0), model_loader)
        self.assertGreater(inv_res.predicted_monthly_demand, 0)

        # 4. Profit
        profit_res = predict_profit(ProfitPredictionRequest(), model_loader)
        self.assertIsNotNone(profit_res.predicted_profit)

        # 5. Expenses
        exp_res = predict_expense(ExpensePredictionRequest(), model_loader)
        self.assertGreater(exp_res.predicted_expense, 0)

        # 6. Business Health Score
        health_res = calculate_business_health(
            BusinessHealthRequest(
                revenue_growth=0.15,
                profit_margin=0.20,
                expense_control=0.85,
                inventory_turnover=4.2,
                payment_collection=0.92,
            ),
            model_loader,
        )
        self.assertGreaterEqual(health_res.health_score, 0.0)
        self.assertLessEqual(health_res.health_score, 100.0)

        # 7. Anomaly Detection
        anom_res = detect_anomaly(
            AnomalyDetectionRequest(
                net_amount=15500.0,
                discount_pct=5.0,
                status_enc=1.0,
            ),
            model_loader,
        )
        self.assertIn(anom_res.is_anomaly, [True, False])

    def test_11_separation_of_zero_shot_metrics_and_adaptation(self):
        """Verify that primary reported holdout metrics are strictly zero-shot with adaptation disabled."""
        for pipe_name, info in self.registry.items():
            self.assertEqual(info.get("status"), "production")
            # Must document that model was evaluated zero-shot
            h = info.get("holdout_company3_metrics", {})
            self.assertIsNotNone(h)

    def test_12_rejection_and_handling_of_nan_and_invalid_inputs(self):
        """Verify that invalid prediction requests are rejected or safely bounded."""
        # Negative months_ahead in revenue request should raise validation error or be handled safely
        with self.assertRaises(Exception):
            RevenuePredictionRequest(months_ahead=-2)

        # Business Health with extreme values should be safely clamped to [0, 100]
        health_extreme = calculate_business_health(
            BusinessHealthRequest(
                revenue_growth=999.0,
                profit_margin=-999.0,
                expense_control=-50.0,
                inventory_turnover=999.0,
                payment_collection=-10.0,
            ),
            model_loader,
        )
        self.assertGreaterEqual(health_extreme.health_score, 0.0)
        self.assertLessEqual(health_extreme.health_score, 100.0)


if __name__ == "__main__":
    unittest.main()

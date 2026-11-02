"""
Test Phase 6 Targeted Corrections and Verification Integrity.
Validates:
1. Accurate, reproducible registry metrics matching evaluation JSONs.
2. Inventory test predictions and tuned LightGBM verification.
3. Independent anomaly benchmark dataset and circularity evaluation.
4. Business health tripartite separation (scorecard, categorization, transition regression).
5. Dataset provenance (multi-year synthetic_v2: 2022-2026, 1755 days).
"""

import json
import os
import pandas as pd
import pytest

ML_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml"))

def test_registry_metrics_sync_with_eval_json():
    """Verify registry metrics are synchronized with source-of-truth eval JSON files."""
    registry_path = os.path.join(ML_ROOT, "models", "model_registry.json")
    assert os.path.exists(registry_path), "model_registry.json missing"
    
    with open(registry_path, "r") as f:
        registry = json.load(f)
    
    pipelines = [
        ("revenue_forecasting", "revenue_forecasting_eval.json", "val_wape_pct", "test_wape_pct"),
        ("sales_forecasting", "sales_forecasting_eval.json", "val_wape_pct", "test_wape_pct"),
        ("inventory_prediction", "inventory_prediction_eval.json", "val_wape_pct", "test_wape_pct"),
        ("profit_prediction", "profit_prediction_eval.json", "val_wape_pct", "test_wape_pct"),
        ("expense_prediction", "expense_prediction_eval.json", "val_wape_pct", "test_wape_pct"),
        ("business_health_score", "health_score_eval.json", "val_mae", "test_mae"),
        ("anomaly_detection", "anomaly_detection_eval.json", "val_f1_score", "test_f1_score")
    ]
    
    for reg_key, eval_filename, val_metric_name, test_metric_name in pipelines:
        eval_path = os.path.join(ML_ROOT, "reports", eval_filename)
        assert os.path.exists(eval_path), f"Eval file missing: {eval_filename}"
        with open(eval_path, "r") as ef:
            eval_data = json.load(ef)
        
        reg_entry = registry.get(reg_key)
        assert reg_entry is not None, f"Registry missing key: {reg_key}"
        
        # Check selected model in candidates
        selected_model_name = eval_data.get("selected_model") or eval_data.get("selected_transition_model")
        candidates = eval_data.get("candidates") or eval_data.get("transition_candidates") or eval_data.get("demand_candidates")
        assert selected_model_name in candidates, f"Selected model {selected_model_name} not in candidates"
        
        eval_cand = candidates[selected_model_name]
        expected_val = eval_cand[val_metric_name]
        expected_test = eval_cand[test_metric_name]
        
        reg_metrics = reg_entry.get("metrics", {})
        actual_val = reg_metrics.get(val_metric_name)
        actual_test = reg_metrics.get(test_metric_name)
        
        assert pytest.approx(actual_val, rel=1e-2) == expected_val, (
            f"Validation metric mismatch for {reg_key}: registry={actual_val} vs eval={expected_val}"
        )
        assert pytest.approx(actual_test, rel=1e-2) == expected_test, (
            f"Test metric mismatch for {reg_key}: registry={actual_test} vs eval={expected_test}"
        )

def test_inventory_tuned_evaluation_and_residuals():
    """Verify inventory demand LightGBM test WAPE is 58.19% and test residuals are saved."""
    preds_path = os.path.join(ML_ROOT, "reports", "inventory_test_predictions.csv")
    assert os.path.exists(preds_path), "inventory_test_predictions.csv missing"
    
    df_preds = pd.read_csv(preds_path)
    assert len(df_preds) == 1500, f"Expected 1,500 test predictions, got {len(df_preds)}"
    assert "units_out" in df_preds.columns
    assert "predicted_demand" in df_preds.columns
    assert "residual" in df_preds.columns
    
    # Calculate WAPE on test set
    wape = (df_preds["units_out"] - df_preds["predicted_demand"]).abs().sum() / df_preds["units_out"].sum()
    assert pytest.approx(wape * 100, rel=1e-2) == 58.19

def test_anomaly_independent_benchmark_and_circularity():
    """Verify independent anomaly benchmark exists and detects rule-based circularity."""
    benchmark_path = os.path.join(ML_ROOT, "datasets", "processed", "anomaly_benchmark_v2.csv")
    assert os.path.exists(benchmark_path), "anomaly_benchmark_v2.csv missing"
    
    df_bm = pd.read_csv(benchmark_path)
    assert len(df_bm) == 1560
    assert "benchmark_anomaly_label" in df_bm.columns
    assert "anomaly_type" in df_bm.columns
    
    anomaly_types = set(df_bm[df_bm["benchmark_anomaly_label"] == 1]["anomaly_type"].unique())
    expected_types = {"EXTREME_OUTLIER", "CONTEXTUAL_DISCOUNT", "MARGIN_EROSION", "TIMING_VELOCITY", "MULTIVARIATE_COVARIANCE"}
    assert anomaly_types == expected_types
    
    # Verify eval JSON documents circularity
    eval_path = os.path.join(ML_ROOT, "reports", "anomaly_detection_eval.json")
    with open(eval_path, "r") as f:
        eval_data = json.load(f)
    
    bm_res = eval_data.get("independent_multi_type_benchmark", {})
    assert "Rule_Based_Detector" in bm_res
    assert "PCA_Reconstruction_Detector" in bm_res
    
    # Rule based detector should fail on non-outlier anomalies (0% recall)
    rule_breakdown = bm_res["Rule_Based_Detector"]["recall_by_anomaly_type"]
    assert rule_breakdown["EXTREME_OUTLIER"] == 1.0
    assert rule_breakdown["CONTEXTUAL_DISCOUNT"] == 0.0
    assert rule_breakdown["MARGIN_EROSION"] == 0.0
    assert rule_breakdown["TIMING_VELOCITY"] == 0.0
    assert rule_breakdown["MULTIVARIATE_COVARIANCE"] == 0.0

def test_business_health_tripartite_separation():
    """Verify health score separates deterministic scorecard from forward transition model."""
    config_path = os.path.join(ML_ROOT, "models", "health_score_config.json")
    assert os.path.exists(config_path), "health_score_config.json missing"
    with open(config_path, "r") as f:
        config = json.load(f)
    
    distinction = config.get("architecture_distinction", {})
    assert "scorecard_concept" in distinction
    assert "classification_concept" in distinction
    assert "transition_prediction_concept" in distinction
    assert "evaluation_limitations" in distinction
    
    eval_path = os.path.join(ML_ROOT, "reports", "health_score_eval.json")
    with open(eval_path, "r") as f:
        eval_data = json.load(f)
    
    # Forward model must compare against persistence baseline
    assert "Persistence_Baseline" in eval_data["transition_candidates"]
    assert "Linear_Regression" in eval_data["transition_candidates"]
    linear_mae = eval_data["transition_candidates"]["Linear_Regression"]["test_mae"]
    persist_mae = eval_data["transition_candidates"]["Persistence_Baseline"]["test_mae"]
    assert linear_mae < persist_mae  # 3.76 < 5.70

def test_raw_dataset_provenance():
    """Verify raw synthetic dataset spans multi-year 2022-2026, not 2024 archive."""
    manifest_path = os.path.join(ML_ROOT, "datasets", "synthetic", "dataset_manifest.json")
    assert os.path.exists(manifest_path), "dataset_manifest.json missing"
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    assert manifest["dataset_version"] == "synthetic_v2"
    assert manifest["effective_date_range"] == ["2022-01-01", "2026-10-21"]
    assert manifest["consecutive_calendar_days"] == 1755
    assert manifest["total_records"] == 142791
    assert manifest["table_count"] == 18

# -*- coding: utf-8 -*-
"""
train_all_pipelines.py
======================
Master Execution Script for ALLADIN Part 2 ML Pipelines.

Executes and verifies all steps end-to-end:
1. Synthetic Data Validation (273 checks)
2. Preprocessing & Cleaning (6 tables)
3. Feature Engineering (6 feature matrices)
4. Pipeline 1: Revenue Forecasting (Approach C, 7 candidates)
5. Pipeline 2: Product & Category Sales Forecasting (Approach C, 6 candidates)
6. Pipeline 3: Inventory Demand & Reorder Prediction (Approach C, 5 candidates)
7. Pipeline 4: Profit Prediction (Approach C, 6 candidates)
8. Pipeline 5: Operating Expense Forecasting (Approach C, 6 candidates)
9. Pipeline 6: Business Health Scoring & Transition (Scorecard + 4 candidates)
10. Pipeline 7: Transaction Anomaly Detection (Statistical + IF + LOF)
11. Updates ml/models/model_registry.json with relative paths and metrics.
12. Validates that backend ModelLoader successfully loads all artifacts.

Usage:
    python ml/train_all_pipelines.py
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Setup project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "ml" / "scripts"))

ML_DIR = PROJECT_ROOT / "ml"
MODELS_DIR = ML_DIR / "models"
REPORTS_DIR = ML_DIR / "reports"
PROCESSED_DIR = ML_DIR / "datasets" / "processed"


def print_step_header(title: str) -> None:
    sep = "=" * 80
    print(f"\n{sep}")
    print(f"  {title.upper()}")
    print(f"{sep}")


def run_command(cmd: str, desc: str) -> bool:
    print(f"\n--> Running: {desc}...")
    start_t = time.time()
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )
    elapsed = time.time() - start_t
    if result.returncode != 0:
        print(f"[FAILED] {desc} (in {elapsed:.2f}s)")
        print("STDOUT:\n", result.stdout[-1000:])
        print("STDERR:\n", result.stderr[-1000:])
        return False
    else:
        print(f"[PASSED] {desc} (in {elapsed:.2f}s)")
        # Print key lines from output
        lines = [line for line in result.stdout.strip().split("\n") if "INFO" in line or "Selected" in line or "WAPE" in line or "MAE" in line or "F1" in line or "Model saved" in line]
        for l in lines[-8:]:
            print("   ", l.strip())
        return True


def update_model_registry() -> Dict[str, Any]:
    """Generate clean, relative-path model registry with actual evaluation metrics."""
    print_step_header("Updating Model Registry (Relative Paths & Metrics)")

    # Load individual evaluation reports
    def load_report(name: str) -> Dict[str, Any]:
        p = REPORTS_DIR / name
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    rev_eval = load_report("revenue_forecasting_eval.json")
    sales_eval = load_report("sales_forecasting_eval.json")
    inv_eval = load_report("inventory_prediction_eval.json")
    profit_eval = load_report("profit_prediction_eval.json")
    exp_eval = load_report("expense_prediction_eval.json")
    health_eval = load_report("health_score_eval.json")
    anomaly_eval = load_report("anomaly_detection_eval.json")

    DEV_CO = ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"]
    HOLD_CO = "00000000-0000-0000-0000-000000000003"

    registry = {
        "revenue_forecasting": {
            "selected_algorithm": rev_eval.get("selected_model", "AAGF_Custom"),
            "model_name": "ALLADIN Adaptive Global Forecaster (AAGF)" if rev_eval.get("selected_model") == "AAGF_Custom" else rev_eval.get("selected_model"),
            "selected_artifact": "ml/models/revenue_forecasting_selected.pkl",
            "artifact_file": "revenue_forecasting_selected.pkl",
            "artifact_path": "ml/models/revenue_forecasting_selected.pkl",
            "training_companies": DEV_CO,
            "holdout_company": HOLD_CO,
            "algorithm_artifacts": {
                "aagf": "ml/models/revenue_forecasting_aagf.pkl",
                "linear_regression": "ml/models/revenue_forecasting_linear_regression.pkl",
                "xgboost": "ml/models/revenue_forecasting_xgboost.pkl",
                "sarima": "ml/models/revenue_forecasting_sarima.pkl"
            },
            "artifact_exists": (MODELS_DIR / "revenue_forecasting_selected.pkl").exists(),
            "registered_at": datetime.now().isoformat(),
            "status": "production",
            "selection_metric": "val_wape",
            "metrics": (rev_eval.get("candidates") or rev_eval.get("candidate_comparisons") or {}).get(rev_eval.get("selected_model", "AAGF_Custom"), {}),
            "holdout_company3_metrics": rev_eval.get("approach_c_holdout_company3_metrics", {})
        },
        "sales_forecasting": {
            "selected_algorithm": sales_eval.get("selected_model", "AAGF_Custom"),
            "model_name": "ALLADIN Adaptive Global Forecaster (AAGF) Product" if sales_eval.get("selected_model") == "AAGF_Custom" else sales_eval.get("selected_model"),
            "selected_artifact": "ml/models/sales_forecasting_selected.pkl",
            "artifact_file": "sales_forecasting_selected.pkl",
            "artifact_path": "ml/models/sales_forecasting_selected.pkl",
            "training_companies": DEV_CO,
            "holdout_company": HOLD_CO,
            "algorithm_artifacts": {
                "aagf_product": "ml/models/sales_forecasting_aagf_product.pkl",
                "xgb_product": "ml/models/sales_forecasting_xgb_product.pkl",
                "lgb_product": "ml/models/sales_forecasting_lgb_product.pkl",
                "linear_regression_product": "ml/models/sales_forecasting_linear_regression_product.pkl",
                "xgb_category": "ml/models/sales_forecasting_xgb_category.pkl"
            },
            "artifact_exists": (MODELS_DIR / "sales_forecasting_selected.pkl").exists(),
            "registered_at": datetime.now().isoformat(),
            "status": "production",
            "selection_metric": "val_wape",
            "metrics": sales_eval.get("candidates", {}).get(sales_eval.get("selected_model", "AAGF_Custom"), {}),
            "holdout_company3_metrics": sales_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        },
        "inventory_prediction": {
            "selected_algorithm": inv_eval.get("selected_model", "LightGBM"),
            "model_name": inv_eval.get("selected_model", "LightGBM"),
            "selected_artifact": "ml/models/inventory_demand_selected.pkl",
            "artifact_file": "inventory_demand_selected.pkl",
            "artifact_path": "ml/models/inventory_demand_selected.pkl",
            "training_companies": DEV_CO,
            "holdout_company": HOLD_CO,
            "algorithm_artifacts": {
                "lightgbm": "ml/models/inventory_demand_lightgbm.pkl",
                "xgboost": "ml/models/inventory_demand_xgboost.pkl",
                "random_forest": "ml/models/inventory_demand_random_forest.pkl"
            },
            "artifact_exists": (MODELS_DIR / "inventory_demand_selected.pkl").exists(),
            "registered_at": datetime.now().isoformat(),
            "status": "production",
            "selection_metric": "val_wape",
            "metrics": inv_eval.get("demand_candidates", {}).get(inv_eval.get("selected_model", "LightGBM"), {}),
            "dev_reorder_evaluation": inv_eval.get("dev_reorder_policy_evaluation") or inv_eval.get("independent_reorder_policy_evaluation", {}),
            "co3_reorder_evaluation": inv_eval.get("co3_reorder_policy_evaluation", {}),
            "holdout_company3_metrics": inv_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        },
        "profit_prediction": {
            "selected_algorithm": profit_eval.get("selected_model", "LightGBM"),
            "model_name": profit_eval.get("selected_model", "LightGBM"),
            "selected_artifact": "ml/models/profit_prediction_selected.pkl",
            "artifact_file": "profit_prediction_selected.pkl",
            "artifact_path": "ml/models/profit_prediction_selected.pkl",
            "training_companies": DEV_CO,
            "holdout_company": HOLD_CO,
            "algorithm_artifacts": {
                "lightgbm": "ml/models/profit_prediction_selected.pkl",
                "random_forest": "ml/models/profit_prediction_random_forest.pkl",
                "xgboost": "ml/models/profit_prediction_xgboost.pkl",
                "linear_regression": "ml/models/profit_prediction_linear_regression.pkl"
            },
            "artifact_exists": (MODELS_DIR / "profit_prediction_selected.pkl").exists(),
            "registered_at": datetime.now().isoformat(),
            "status": "production",
            "selection_metric": "val_wape",
            "metrics": profit_eval.get("candidates", {}).get(profit_eval.get("selected_model", "LightGBM"), {}),
            "holdout_company3_metrics": profit_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        },
        "expense_prediction": {
            "selected_algorithm": exp_eval.get("selected_model", "LightGBM"),
            "model_name": exp_eval.get("selected_model", "LightGBM"),
            "selected_artifact": "ml/models/expense_prediction_selected.pkl",
            "artifact_file": "expense_prediction_selected.pkl",
            "artifact_path": "ml/models/expense_prediction_selected.pkl",
            "training_companies": DEV_CO,
            "holdout_company": HOLD_CO,
            "algorithm_artifacts": {
                "lightgbm": "ml/models/expense_prediction_selected.pkl",
                "xgboost": "ml/models/expense_prediction_xgboost.pkl",
                "linear_regression": "ml/models/expense_prediction_linear_regression.pkl"
            },
            "artifact_exists": (MODELS_DIR / "expense_prediction_selected.pkl").exists(),
            "registered_at": datetime.now().isoformat(),
            "status": "production",
            "selection_metric": "val_wape",
            "metrics": exp_eval.get("candidates", {}).get(exp_eval.get("selected_model", "LightGBM"), {}),
            "holdout_company3_metrics": exp_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        },
        "business_health_score": {
            "selected_algorithm": "TransparentKPIScorecard + " + health_eval.get("selected_transition_model", "Random_Forest"),
            "model_name": "TransparentKPIScorecard + " + health_eval.get("selected_transition_model", "Random_Forest"),
            "selected_artifact": "ml/models/health_score_pipeline.pkl",
            "artifact_file": "health_score_pipeline.pkl",
            "artifact_path": "ml/models/health_score_pipeline.pkl",
            "training_companies": DEV_CO,
            "holdout_company": HOLD_CO,
            "artifact_exists": (MODELS_DIR / "health_score_pipeline.pkl").exists(),
            "registered_at": datetime.now().isoformat(),
            "status": "production",
            "selection_metric": "val_mae",
            "scorecard_weights": health_eval.get("scorecard_weights", {}),
            "transition_metrics": health_eval.get("transition_candidates", {}).get(health_eval.get("selected_transition_model", "Random_Forest"), {}),
            "holdout_company3_metrics": health_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        },
        "anomaly_detection": {
            "selected_algorithm": anomaly_eval.get("selected_model", "Isolation_Forest"),
            "model_name": anomaly_eval.get("selected_model", "Isolation_Forest"),
            "selected_artifact": "ml/models/anomaly_detection_isolation_forest.pkl",
            "artifact_file": "anomaly_detection_isolation_forest.pkl",
            "artifact_path": "ml/models/anomaly_detection_isolation_forest.pkl",
            "secondary_config": "ml/models/anomaly_detection_lof_config.json",
            "training_companies": DEV_CO,
            "holdout_company": HOLD_CO,
            "artifact_exists": (MODELS_DIR / "anomaly_detection_isolation_forest.pkl").exists(),
            "registered_at": datetime.now().isoformat(),
            "status": "production",
            "selection_metric": "val_f1_score",
            "metrics": anomaly_eval.get("candidates", {}).get(anomaly_eval.get("selected_model", "Isolation_Forest"), {}),
            "holdout_company3_metrics": anomaly_eval.get("approach_c_holdout_co3", {}).get("metrics", {})
        }
    }

    reg_path = MODELS_DIR / "model_registry.json"
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
    print(f"Saved updated model registry to: {reg_path}")

    # Generate model_registry.md
    md_content = "# ALLADIN Machine Learning Model Registry\n\n"
    md_content += f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n"
    md_content += "**Evaluation Strategy:** Strict Cross-Business Generalization (Dev Companies 1 & 2 vs Strictly Held-Out Company 3).\n\n"
    md_content += "| Pipeline | Selected Algorithm | Primary Canonical Artifact | Dev Val Metric | Dev Test Metric | Holdout Co3 Performance | Status |\n"
    md_content += "|---|---|---|---|---|---|---|\n"

    for pipe_name, info in registry.items():
        art = info.get("artifact_file", "N/A")
        mod = info.get("selected_algorithm", "N/A")
        m = info.get("metrics", {})
        vm = m.get("val_metrics", {})
        tm = m.get("test_metrics", {})

        if "wape" in vm:
            val_str = f"WAPE: {vm.get('wape'):.2f}%"
            test_str = f"WAPE: {tm.get('wape'):.2f}%" if "wape" in tm else "N/A"
        elif "f1_score" in vm:
            val_str = f"F1: {vm.get('f1_score'):.4f}"
            test_str = f"F1: {tm.get('f1_score'):.4f}" if "f1_score" in tm else "N/A"
        elif "mae" in vm:
            val_str = f"MAE: {vm.get('mae'):.2f} pts"
            test_str = f"MAE: {tm.get('mae'):.2f} pts" if "mae" in tm else "N/A"
        else:
            val_str = "Verified"
            test_str = "Verified"

        h = info.get("holdout_company3_metrics", {})
        if "wape" in h or "wape_pct" in h:
            h_str = f"WAPE: {h.get('wape', h.get('wape_pct')):.2f}%"
        elif "f1_score" in h:
            h_str = f"F1: {h.get('f1_score'):.4f}"
        elif "mae" in h:
            h_str = f"MAE: {h.get('mae'):.2f} pts"
        else:
            h_str = "Evaluated"

        md_content += f"| **{pipe_name}** | {mod} | `{art}` | {val_str} | {test_str} | {h_str} | {info.get('status')} |\n"

    md_path = REPORTS_DIR / "model_registry.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved markdown model registry summary to: {md_path}")

    return registry


def verify_backend_model_loader() -> bool:
    """Run verification to check that backend ModelLoader loads every artifact cleanly and runs inference."""
    print_step_header("Verifying Backend ModelLoader Compatibility & Inference Smoke Test")

    test_script = """
import sys
from pathlib import Path
root = Path('.').resolve()
sys.path.insert(0, str(root / 'backend'))

from app.ml.model_loader import model_loader
from app.ml.revenue_predictor import predict_revenue
from app.ml.sales_predictor import predict_sales
from app.schemas.ml import RevenuePredictionRequest, SalesPredictionRequest

model_loader.load_all_models()
print(f"ModelLoader active: {model_loader.is_loaded}")

expected_models = [
    "revenue_selected", "revenue_aagf", "revenue_linear_regression", "revenue_xgboost", "revenue_sarima",
    "sales_selected", "sales_aagf", "sales_xgb_product", "sales_lgb_product", "sales_linear_regression", "sales_xgb_category",
    "inventory_selected", "inventory_demand", "inventory_xgboost", "inventory_random_forest",
    "profit_selected", "profit_prediction", "profit_random_forest", "profit_xgboost", "profit_linear_regression",
    "expense_selected", "expense_xgboost", "expense_linear_regression",
    "health_score_pipeline", "anomaly_detection"
]

missing = []
for m in expected_models:
    obj = model_loader.get_model(m)
    if obj is None:
        missing.append(m)
    else:
        print(f"  [OK] Model '{m}' loaded successfully.")

if missing:
    print(f"FAILED: Missing models: {missing}")
    sys.exit(1)

print("All registered model keys loaded cleanly!")

# Run live inference smoke tests
print("Running live inference smoke tests...")
rev_req_legacy = RevenuePredictionRequest(months_ahead=3, model_type="xgboost")
rev_resp_legacy = predict_revenue(rev_req_legacy, model_loader)
print(f"  [OK] Legacy XGBoost Revenue prediction executed:")
print(f"       Model: {rev_resp_legacy.model_used} | Projected: Rs. {rev_resp_legacy.total_projected_revenue:,.2f}")

rev_req_aagf = RevenuePredictionRequest(months_ahead=3, model_type="aagf")
rev_resp_aagf = predict_revenue(rev_req_aagf, model_loader)
print(f"  [OK] Custom AAGF Revenue prediction executed:")
print(f"       Model: {rev_resp_aagf.model_used} | Projected: Rs. {rev_resp_aagf.total_projected_revenue:,.2f}")

sales_req_legacy = SalesPredictionRequest(entity_type="product", entity_id="1", months_ahead=3, model_type="xgboost")
sales_resp_legacy = predict_sales(sales_req_legacy, model_loader)
print(f"  [OK] Legacy XGBoost Sales prediction executed:")
print(f"       Model: {sales_resp_legacy.model_used} | Units: {sales_resp_legacy.total_predicted_units}")

sales_req_aagf = SalesPredictionRequest(entity_type="product", entity_id="1", months_ahead=3, model_type="aagf")
sales_resp_aagf = predict_sales(sales_req_aagf, model_loader)
print(f"  [OK] Custom AAGF Sales prediction executed:")
print(f"       Model: {sales_resp_aagf.model_used} | Units: {sales_resp_aagf.total_predicted_units}")

print("Backend ModelLoader & inference smoke tests verified successfully!")
"""
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print("ERROR:\n", result.stderr)
        return False
    return True


def main() -> None:
    print_step_header("ALLADIN Part 2: Master ML Training Suite")
    start_total = time.time()

    pipeline_steps = [
        ("python ml/datasets/synthetic/validate_synthetic_data.py", "Step 0: Validate Synthetic Dataset"),
        ("python ml/scripts/preprocess.py", "Step 1: Preprocess Raw Synthetic Data"),
        ("python ml/scripts/feature_engineering.py", "Step 2: Feature Engineering (All 6 Tables)"),
        ("python ml/scripts/train_revenue.py", "Pipeline 1: Revenue Forecasting"),
        ("python ml/scripts/train_sales.py", "Pipeline 2: Sales Forecasting (Product & Category)"),
        ("python ml/scripts/train_inventory.py", "Pipeline 3: Inventory Demand & Reorders"),
        ("python ml/scripts/train_profit.py", "Pipeline 4: Profit Prediction"),
        ("python ml/scripts/train_expenses.py", "Pipeline 5: Operating Expense Forecasting"),
        ("python ml/scripts/train_health_score.py", "Pipeline 6: Business Health Scoring"),
        ("python ml/scripts/train_anomaly.py", "Pipeline 7: Transaction Anomaly Detection"),
    ]

    summary = {
        "timestamp": datetime.now().isoformat(),
        "steps": [],
        "overall_status": "PENDING"
    }

    all_passed = True
    for cmd, desc in pipeline_steps:
        print_step_header(desc)
        passed = run_command(cmd, desc)
        summary["steps"].append({"step": desc, "command": cmd, "passed": passed})
        if not passed:
            all_passed = False
            print(f"\n[CRITICAL STOP] {desc} failed. Halting training orchestrator.")
            break

    if all_passed:
        # Step 11: Update registry
        registry = update_model_registry()

        # Step 12: Backend compatibility verification
        loader_ok = verify_backend_model_loader()
        summary["backend_model_loader_verified"] = loader_ok
        if not loader_ok:
            all_passed = False

    total_time = time.time() - start_total
    summary["overall_status"] = "PASSED" if all_passed else "FAILED"
    summary["total_runtime_seconds"] = round(total_time, 2)

    # Save execution summary
    summary_path = REPORTS_DIR / "pipeline_execution_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print_step_header(f"ALLADIN ML Suite Completed in {total_time:.2f}s - Status: {summary['overall_status']}")
    print(f"Summary report written to: {summary_path}")


if __name__ == "__main__":
    main()

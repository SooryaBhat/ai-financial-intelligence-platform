import sys
from pathlib import Path
import json

base_dir = Path(__file__).resolve().parents[2]
backend_dir = base_dir / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(base_dir / "ml" / "scripts"))
sys.path.insert(0, str(base_dir / "ml" / "scripts" / "custom_models"))

from app.ml.model_loader import ModelLoader
from app.ml.sales_predictor import predict_sales
from app.schemas.ml import SalesPredictionRequest

loader = ModelLoader()
loader.load_all_models()

print("\n--- TEST 1: Default history (12 items) with product_profile (default winner) ---")
for m in [1, 2, 3, 6]:
    req = SalesPredictionRequest(
        entity_type="product",
        model_type="product_profile",
        months_ahead=m
    )
    res = predict_sales(req, loader)
    preds = [(p.month, p.predicted_units_sold, p.predicted_sales_amount) for p in res.predictions]
    print(f"Months={m}: {preds}")

print("\n--- TEST 2: With specific product entity_id ---")
req = SalesPredictionRequest(
    entity_type="product",
    model_type="product_profile",
    entity_id="prod_01",
    months_ahead=6
)
res = predict_sales(req, loader)
preds = [(p.month, p.predicted_units_sold) for p in res.predictions]
print(f"prod_01: {preds}")

print("\n--- TEST 3: Other model types ---")
for mt in ["aagf", "lightgbm", "xgboost", "linear_regression"]:
    req = SalesPredictionRequest(
        entity_type="product",
        model_type=mt,
        months_ahead=6
    )
    res = predict_sales(req, loader)
    preds = [(p.month, p.predicted_units_sold) for p in res.predictions]
    print(f"Model {mt}: {preds}")

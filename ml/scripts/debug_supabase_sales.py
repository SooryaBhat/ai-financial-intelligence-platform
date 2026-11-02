import sys
from pathlib import Path
import os
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parents[2]
backend_dir = base_dir / "backend"
load_dotenv(backend_dir / ".env")

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(base_dir / "ml" / "scripts"))
sys.path.insert(0, str(base_dir / "ml" / "scripts" / "custom_models"))

from app.database.client import get_admin_client
from app.services.ml_data_service import MLDataService
from app.ml.model_loader import ModelLoader
from app.ml.sales_predictor import predict_sales
from app.schemas.ml import SalesPredictionRequest

company_id = "33333333-0000-0000-0000-000000000001"
admin = get_admin_client()
data_service = MLDataService(admin, company_id)

units, amounts, months, is_sufficient = data_service.get_historical_product_sales("product", None)
print(f"Months found ({len(months)}): {months}")
print(f"Units found ({len(units)}): {units}")
print(f"Amounts found ({len(amounts)}): {amounts}")
print(f"is_sufficient: {is_sufficient}")

loader = ModelLoader()
loader.load_all_models()

for m in [1, 2, 3, 6]:
    req = SalesPredictionRequest(
        entity_type="product",
        model_type="product_profile",
        historical_sales=units,
        months_ahead=m
    )
    res = predict_sales(req, loader)
    preds = [(p.month, p.predicted_units_sold, p.predicted_sales_amount) for p in res.predictions]
    print(f"\nSupermarket DB Sales Forecast (months_ahead={m}):")
    for p in preds:
        print(f"  {p}")

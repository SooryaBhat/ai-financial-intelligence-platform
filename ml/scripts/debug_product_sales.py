import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')
sys.path.insert(0, 'ml/scripts')
sys.path.insert(0, 'ml/scripts/custom_models')

from app.database.client import get_admin_client
from app.services.ml_data_service import MLDataService
from app.ml.model_loader import ModelLoader
from app.ml.sales_predictor import predict_sales
from app.schemas.ml import SalesPredictionRequest

company_id = "33333333-0000-0000-0000-000000000001"
admin = get_admin_client()
ds = MLDataService(admin, company_id)

prods = admin.table("products").select("id, name").eq("company_id", company_id).execute().data
print(f"Total products in company: {len(prods)}")

loader = ModelLoader()
loader.load_all_models()

for p in prods[:3]:
    pid = p["id"]
    pname = p["name"]
    units, amounts, months, is_sufficient = ds.get_historical_product_sales("product", pid)
    print(f"\nProduct: {pname} (ID: {pid})")
    print(f"  Months: {months}")
    print(f"  Units: {units}")
    req = SalesPredictionRequest(
        entity_type="product",
        model_type="product_profile",
        entity_id=pid,
        historical_sales=units,
        months_ahead=6
    )
    res = predict_sales(req, loader)
    preds = [(item.month, item.predicted_units_sold) for item in res.predictions]
    print(f"  PPF 6m Forecast: {preds}")

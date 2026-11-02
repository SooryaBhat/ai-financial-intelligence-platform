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

prods = admin.table("products").select("id, name, selling_price").eq("company_id", company_id).execute().data
loader = ModelLoader()
loader.load_all_models()

monthly_totals = [0.0] * 6
for p in prods:
    pid = p["id"]
    units, amounts, months, is_sufficient = ds.get_historical_product_sales("product", pid)
    req = SalesPredictionRequest(
        entity_type="product",
        model_type="product_profile",
        entity_id=pid,
        historical_sales=units,
        months_ahead=6
    )
    res = predict_sales(req, loader)
    for i, item in enumerate(res.predictions):
        monthly_totals[i] += item.predicted_units_sold

print("Bottom-Up Sum across all 20 products for 6 months:")
for i, tot in enumerate(monthly_totals):
    print(f"  Month {i+1}: {tot:.2f} units")

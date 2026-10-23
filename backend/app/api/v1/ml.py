"""
Machine Learning Predictions API Router.
Exposes database-backed, authenticated, and tenant-isolated endpoints for:
  - Revenue Forecasting (/revenue/predict)
  - Sales Forecasting (/sales/predict)
  - Inventory Demand Prediction (/inventory/predict)
  - Profit Prediction (/profit/predict)
  - Expense Prediction (/expense/predict)
  - Business Health Scoring (/business-health/predict)
  - Anomaly Detection (/anomaly/predict)
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import logger
from app.dependencies.auth import get_request_context
from app.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.ml.anomaly_detector import detect_anomaly
from app.ml.business_health import calculate_business_health
from app.ml.expense_predictor import predict_expense
from app.ml.inventory_predictor import predict_inventory
from app.ml.model_loader import ModelLoader, get_model_loader
from app.ml.profit_predictor import predict_profit
from app.ml.revenue_predictor import predict_revenue
from app.ml.sales_predictor import predict_sales
from app.schemas.common import SuccessResponse
from app.schemas.ml import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    BusinessHealthRequest,
    BusinessHealthResponse,
    ExpensePredictionRequest,
    ExpensePredictionResponse,
    InventoryPredictionRequest,
    InventoryPredictionResponse,
    ProfitPredictionRequest,
    ProfitPredictionResponse,
    RevenuePredictionRequest,
    RevenuePredictionResponse,
    SalesPredictionRequest,
    SalesPredictionResponse,
)
from app.services.context import RequestContext
from app.services.ml_data_service import MLDataService

router = APIRouter(prefix="/ml", tags=["ML Predictions"])


@router.post(
    "/revenue/predict",
    response_model=SuccessResponse[RevenuePredictionResponse],
    summary="Forecast platform / company monthly revenue",
    description=(
        "Uses trained XGBoost or SARIMA time-series models to forecast future monthly revenue.\n\n"
        "Automatically retrieves authorized historical sales from Supabase if not manually provided.\n"
        "- **months_ahead**: Forecast horizon in months (1-24).\n"
        "- **model_type**: Select algorithm ('xgboost' or 'sarima').\n"
        "- **branch_id**: Optional outlet UUID filter."
    ),
)
def forecast_revenue_endpoint(
    payload: RevenuePredictionRequest,
    ctx: RequestContext = Depends(get_request_context),
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        data_service = MLDataService(ctx.user_client, ctx.company_id, payload.branch_id)
        is_fallback = False
        warning = None

        history = payload.historical_revenue
        if not history:
            db_revenues, months, is_sufficient = data_service.get_historical_monthly_revenue()
            if db_revenues and is_sufficient:
                history = db_revenues
            elif db_revenues:
                history = db_revenues
                is_fallback = True
                warning = f"Only {len(db_revenues)} month(s) of revenue records found. Model output is an initial baseline."
            else:
                is_fallback = True
                warning = "No historical sales records found for this company. Using safe retail industry baseline."

        req_copy = payload.model_copy(update={"historical_revenue": history})
        res = predict_revenue(req_copy, loader)
        res.is_fallback = is_fallback
        res.warning_message = warning

        data_service.record_prediction(
            prediction_type="revenue",
            predicted_value=res.total_projected_revenue,
            confidence_score=0.90,
            model_version=res.model_used,
            input_data={"months_ahead": payload.months_ahead, "model_type": payload.model_type, "history_len": len(history or [])},
            output_data=res.model_dump(),
        )

        return SuccessResponse(data=res)
    except ForbiddenError as fe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(fe))
    except UnauthorizedError as ue:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ue))
    except Exception as e:
        logger.error("[API ML] Revenue prediction failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Revenue prediction failed: {str(e)}",
        )


@router.post(
    "/sales/predict",
    response_model=SuccessResponse[SalesPredictionResponse],
    summary="Forecast product or category sales demand",
    description=(
        "Predicts upcoming units sold and total sales volume per product or category.\n\n"
        "Automatically retrieves authorized product sales history from Supabase if not manually provided.\n"
        "- **entity_type**: 'product' or 'category'.\n"
        "- **model_type**: 'xgboost' or 'lightgbm'.\n"
        "- **months_ahead**: Horizon (1-12 months)."
    ),
)
def forecast_sales_endpoint(
    payload: SalesPredictionRequest,
    ctx: RequestContext = Depends(get_request_context),
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        data_service = MLDataService(ctx.user_client, ctx.company_id, payload.branch_id)
        is_fallback = False
        warning = None

        history = payload.historical_sales
        if not history:
            units, amounts, months, is_sufficient = data_service.get_historical_product_sales(
                payload.entity_type, payload.entity_id
            )
            if units and is_sufficient:
                history = units
            elif units:
                history = units
                is_fallback = True
                warning = f"Only {len(units)} month(s) of sales found for {payload.entity_type}. Using initial trend."
            else:
                is_fallback = True
                warning = f"No historical sales records found for {payload.entity_type}. Using safe retail demand baseline."

        req_copy = payload.model_copy(update={"historical_sales": history})
        res = predict_sales(req_copy, loader)
        res.is_fallback = is_fallback
        res.warning_message = warning

        data_service.record_prediction(
            prediction_type="sales",
            predicted_value=res.total_predicted_units,
            confidence_score=0.88,
            model_version=res.model_used,
            input_data={"entity_type": payload.entity_type, "entity_id": payload.entity_id, "months_ahead": payload.months_ahead},
            output_data=res.model_dump(),
        )

        return SuccessResponse(data=res)
    except ForbiddenError as fe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(fe))
    except UnauthorizedError as ue:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ue))
    except Exception as e:
        logger.error("[API ML] Sales prediction failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sales prediction failed: {str(e)}",
        )


@router.post(
    "/inventory/predict",
    response_model=SuccessResponse[InventoryPredictionResponse],
    summary="Predict inventory demand and stock reorder triggers",
    description=(
        "Estimates monthly inventory demand, calculates optimal reorder points, and evaluates stockout risk.\n\n"
        "Automatically retrieves live warehouse stock and historical product demand from Supabase.\n"
        "- **product_id**: Optional Product UUID to look up stock and history.\n"
        "- **lead_time_days**: Supplier replenishment lead time."
    ),
)
def predict_inventory_endpoint(
    payload: InventoryPredictionRequest,
    ctx: RequestContext = Depends(get_request_context),
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        data_service = MLDataService(ctx.user_client, ctx.company_id, payload.branch_id)
        is_fallback = False
        warning = None

        curr_stock = payload.current_stock
        unit_cost = payload.unit_cost
        demand_hist = payload.historical_monthly_demand
        prod_name = payload.product_name

        if payload.product_id and (curr_stock is None or demand_hist is None):
            inv_info = data_service.get_inventory_status_and_demand(payload.product_id, payload.product_name)
            if curr_stock is None:
                curr_stock = inv_info["current_stock"]
            if unit_cost == 10.0 and inv_info["unit_cost"] != 10.0:
                unit_cost = inv_info["unit_cost"]
            if prod_name is None:
                prod_name = inv_info["product_name"]
            if demand_hist is None and inv_info["historical_monthly_demand"]:
                demand_hist = inv_info["historical_monthly_demand"]
                if not inv_info["has_sufficient_data"]:
                    is_fallback = True
                    warning = f"Limited historical demand ({len(demand_hist)} months). Conservative reorder recommendation applied."
            elif demand_hist is None:
                is_fallback = True
                warning = "No historical demand records found for this product. Using safe baseline demand."

        if curr_stock is None:
            curr_stock = 0.0

        req_copy = payload.model_copy(update={
            "current_stock": curr_stock,
            "unit_cost": unit_cost,
            "product_name": prod_name,
            "historical_monthly_demand": demand_hist,
        })
        res = predict_inventory(req_copy, loader)
        res.is_fallback = is_fallback
        res.warning_message = warning

        data_service.record_prediction(
            prediction_type="inventory",
            predicted_value=res.predicted_monthly_demand,
            confidence_score=0.85,
            model_version="inventory_xgb_v2",
            input_data={"product_id": payload.product_id, "current_stock": curr_stock, "lead_time_days": payload.lead_time_days},
            output_data=res.model_dump(),
        )

        return SuccessResponse(data=res)
    except ForbiddenError as fe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(fe))
    except UnauthorizedError as ue:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ue))
    except Exception as e:
        logger.error("[API ML] Inventory prediction failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inventory prediction failed: {str(e)}",
        )


@router.post(
    "/profit/predict",
    response_model=SuccessResponse[ProfitPredictionResponse],
    summary="Predict gross & net profit margins",
    description=(
        "Predicts upcoming monthly profit performance, profit margin percentage, and margin efficiency status.\n\n"
        "Automatically retrieves real revenue and operating expenses from Supabase to compute historical profit series."
    ),
)
def predict_profit_endpoint(
    payload: ProfitPredictionRequest,
    ctx: RequestContext = Depends(get_request_context),
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        data_service = MLDataService(ctx.user_client, ctx.company_id, payload.branch_id)
        is_fallback = False
        warning = None

        p_hist = payload.historical_profits
        r_hist = payload.historical_revenues
        proj_rev = payload.projected_revenue

        if not p_hist or not r_hist:
            db_p, db_r, db_e, months, is_sufficient = data_service.get_historical_monthly_profit()
            if not p_hist and db_p:
                p_hist = db_p
            if not r_hist and db_r:
                r_hist = db_r
            if not proj_rev and db_r:
                proj_rev = db_r[-1]

            if not is_sufficient:
                is_fallback = True
                warning = f"Limited historical profit records ({len(db_p)} months). Initial margin estimates applied."

        req_copy = payload.model_copy(update={
            "historical_profits": p_hist,
            "historical_revenues": r_hist,
            "projected_revenue": proj_rev,
        })
        res = predict_profit(req_copy, loader)
        res.is_fallback = is_fallback
        res.warning_message = warning

        data_service.record_prediction(
            prediction_type="profit",
            predicted_value=res.predicted_profit,
            confidence_score=res.confidence_score,
            model_version="profit_xgb_v2",
            input_data={"projected_revenue": proj_rev, "history_len": len(p_hist or [])},
            output_data=res.model_dump(),
        )

        return SuccessResponse(data=res)
    except ForbiddenError as fe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(fe))
    except UnauthorizedError as ue:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ue))
    except Exception as e:
        logger.error("[API ML] Profit prediction failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profit prediction failed: {str(e)}",
        )


@router.post(
    "/expense/predict",
    response_model=SuccessResponse[ExpensePredictionResponse],
    summary="Forecast operating expenses and flag spending risks",
    description=(
        "Predicts future operational expenses per category and generates expense anomaly surge alerts.\n\n"
        "Automatically retrieves approved expenses from Supabase to construct historical lag features."
    ),
)
def predict_expense_endpoint(
    payload: ExpensePredictionRequest,
    ctx: RequestContext = Depends(get_request_context),
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        data_service = MLDataService(ctx.user_client, ctx.company_id, payload.branch_id)
        is_fallback = False
        warning = None

        expenses = payload.historical_expenses
        breakdown = None

        if not expenses:
            db_exp, months, cat_breakdown, is_sufficient = data_service.get_historical_monthly_expenses(payload.category)
            breakdown = cat_breakdown
            if db_exp and is_sufficient:
                expenses = db_exp
            elif db_exp:
                expenses = db_exp
                is_fallback = True
                warning = f"Limited historical expenses ({len(db_exp)} months) for {payload.category or 'all categories'}."
            else:
                is_fallback = True
                warning = f"No historical expense records found for {payload.category or 'all categories'}. Safe retail baseline used."

        req_copy = payload.model_copy(update={"historical_expenses": expenses})
        res = predict_expense(req_copy, loader)
        if breakdown and not res.category_breakdown:
            res.category_breakdown = breakdown
        res.is_fallback = is_fallback
        res.warning_message = warning

        data_service.record_prediction(
            prediction_type="expense",
            predicted_value=res.predicted_expense,
            confidence_score=0.87,
            model_version=res.model_used,
            input_data={"category": payload.category, "model_type": payload.model_type, "months_ahead": payload.months_ahead},
            output_data=res.model_dump(),
        )

        return SuccessResponse(data=res)
    except ForbiddenError as fe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(fe))
    except UnauthorizedError as ue:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ue))
    except Exception as e:
        logger.error("[API ML] Expense prediction failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Expense prediction failed: {str(e)}",
        )


@router.post(
    "/business-health/predict",
    response_model=SuccessResponse[BusinessHealthResponse],
    summary="Calculate composite Business Health Score (0-100)",
    description=(
        "Evaluates 5 core financial KPIs to calculate overall Business Health Index, letter grade (A-F), and actionable advice.\n\n"
        "Automatically computes real deterministic KPIs from sales, expenses, inventory, and invoice records in Supabase."
    ),
)
def calculate_business_health_endpoint(
    payload: BusinessHealthRequest,
    ctx: RequestContext = Depends(get_request_context),
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        data_service = MLDataService(ctx.user_client, ctx.company_id, payload.branch_id)
        is_fallback = False
        warning = None

        rev_growth = payload.revenue_growth
        prof_margin = payload.profit_margin
        exp_control = payload.expense_control
        inv_turnover = payload.inventory_turnover
        pay_collection = payload.payment_collection

        # If any KPI is omitted, auto-compute from database
        if any(x is None for x in [rev_growth, prof_margin, exp_control, inv_turnover, pay_collection]):
            db_kpis = data_service.get_business_health_kpis()
            if rev_growth is None:
                rev_growth = db_kpis["revenue_growth"]
            if prof_margin is None:
                prof_margin = db_kpis["profit_margin"]
            if exp_control is None:
                exp_control = db_kpis["expense_control"]
            if inv_turnover is None:
                inv_turnover = db_kpis["inventory_turnover"]
            if pay_collection is None:
                pay_collection = db_kpis["payment_collection"]

            if not db_kpis["has_sufficient_data"]:
                is_fallback = True
                warning = "Business records are limited. Health scorecard includes safe retail sector baseline estimates: " + "; ".join(db_kpis["warnings"])

        req_copy = BusinessHealthRequest(
            branch_id=payload.branch_id,
            revenue_growth=rev_growth if rev_growth is not None else 0.15,
            profit_margin=prof_margin if prof_margin is not None else 0.20,
            expense_control=exp_control if exp_control is not None else 0.82,
            inventory_turnover=inv_turnover if inv_turnover is not None else 4.5,
            payment_collection=pay_collection if pay_collection is not None else 0.90,
        )

        res = calculate_business_health(req_copy, loader)
        res.is_fallback = is_fallback
        res.warning_message = warning

        data_service.record_prediction(
            prediction_type="business_health",
            predicted_value=res.health_score,
            confidence_score=0.92,
            model_version="health_scorecard_v2",
            input_data={"revenue_growth": rev_growth, "profit_margin": prof_margin, "expense_control": exp_control},
            output_data=res.model_dump(),
        )

        return SuccessResponse(data=res)
    except ForbiddenError as fe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(fe))
    except UnauthorizedError as ue:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ue))
    except Exception as e:
        logger.error("[API ML] Business health score calculation failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Business health score calculation failed: {str(e)}",
        )


@router.post(
    "/anomaly/predict",
    response_model=SuccessResponse[AnomalyDetectionResponse],
    summary="Detect transaction & invoice anomalies",
    description=(
        "Uses trained Isolation Forest model to detect suspicious invoices, price anomalies, or uncharacteristic transactions.\n\n"
        "Automatically computes the company's real 28-day rolling amount baseline from Supabase sales."
    ),
)
def detect_anomaly_endpoint(
    payload: AnomalyDetectionRequest,
    ctx: RequestContext = Depends(get_request_context),
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        data_service = MLDataService(ctx.user_client, ctx.company_id, payload.branch_id)
        is_fallback = False
        warning = None

        roll_mean = payload.roll28_mean
        roll_std = payload.roll28_std

        if roll_mean is None or roll_std is None:
            baseline = data_service.get_transaction_anomaly_baseline()
            if roll_mean is None:
                roll_mean = baseline["roll28_mean"]
            if roll_std is None:
                roll_std = baseline["roll28_std"]
            if not baseline["has_sufficient_data"]:
                is_fallback = True
                warning = "Fewer than 5 transactions in the last 28 days. Using standard retail variance baseline."

        req_copy = payload.model_copy(update={
            "roll28_mean": roll_mean,
            "roll28_std": roll_std,
        })

        res = detect_anomaly(req_copy, loader)
        res.is_fallback = is_fallback
        res.warning_message = warning

        data_service.record_prediction(
            prediction_type="anomaly",
            predicted_value=res.anomaly_score,
            confidence_score=res.confidence / 100.0,
            model_version="isolation_forest_v2",
            input_data={"net_amount": payload.net_amount, "discount_pct": payload.discount_pct, "is_anomaly": res.is_anomaly},
            output_data=res.model_dump(),
        )

        return SuccessResponse(data=res)
    except ForbiddenError as fe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(fe))
    except UnauthorizedError as ue:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ue))
    except Exception as e:
        logger.error("[API ML] Anomaly detection failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(e)}",
        )

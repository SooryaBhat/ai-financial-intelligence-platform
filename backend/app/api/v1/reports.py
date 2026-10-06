"""Reports router — /api/v1/reports"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_request_context
from app.repositories.reports import ReportRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.reports import ReportCreate, ReportUpdate
from app.services.context import RequestContext

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/", response_model=SuccessResponse, summary="List reports")
def list_reports(ctx: RequestContext = Depends(get_request_context)):
    repo = ReportRepository(ctx.user_client)
    return SuccessResponse(data=repo.list(ctx.company_id))


@router.get("/summary", response_model=SuccessResponse, summary="Get dashboard summary metrics")
def get_dashboard_summary(ctx: RequestContext = Depends(get_request_context)):
    client = ctx.user_client
    cid = str(ctx.company_id)

    sales_res = client.table("sales").select("total_amount, sale_date").eq("company_id", cid).neq("status", "cancelled").execute()
    total_revenue = sum(float(s["total_amount"]) for s in (sales_res.data or []))
    total_sales_count = len(sales_res.data or [])

    exp_res = client.table("expenses").select("amount").eq("company_id", cid).eq("status", "approved").execute()
    total_expenses = sum(float(e["amount"]) for e in (exp_res.data or []))

    net_profit = total_revenue - total_expenses

    inv_res = client.table("inventory").select("id, quantity, reorder_level").eq("company_id", cid).execute()
    inventory_count = len(inv_res.data or [])
    low_stock_count = sum(1 for i in (inv_res.data or []) if float(i.get("quantity", 0)) <= float(i.get("reorder_level", 0)))

    invc_res = client.table("invoices").select("amount_due").eq("company_id", cid).eq("invoice_type", "receivable").neq("status", "paid").execute()
    total_outstanding = sum(float(i["amount_due"]) for i in (invc_res.data or []) if i.get("amount_due"))

    recent_sales = client.table("sales").select("id, sale_number, total_amount, sale_date, status, customers(name)").eq("company_id", cid).order("created_at", desc=True).limit(5).execute()

    return SuccessResponse(data={
        "total_revenue": total_revenue,
        "total_sales_count": total_sales_count,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "inventory_count": inventory_count,
        "low_stock_count": low_stock_count,
        "total_outstanding": total_outstanding,
        "recent_sales": recent_sales.data or [],
    })


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create report")
def create_report(payload: ReportCreate, ctx: RequestContext = Depends(get_request_context)):
    repo = ReportRepository(ctx.user_client)
    data = {
        "company_id": str(ctx.company_id),
        "user_id": str(ctx.user_id),
        "report_type": payload.report_type.value,
        "title": payload.title,
        "period_start": payload.period_start.isoformat() if payload.period_start else None,
        "period_end": payload.period_end.isoformat() if payload.period_end else None,
        "status": "generating",
    }
    result = repo.create(data)
    return SuccessResponse(data=result)


@router.get("/{report_id}", response_model=SuccessResponse, summary="Get report")
def get_report(report_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ReportRepository(ctx.user_client)
    return SuccessResponse(data=repo.get_by_id(report_id, ctx.company_id))


@router.patch("/{report_id}", response_model=SuccessResponse, summary="Update report")
def update_report(report_id: UUID, payload: ReportUpdate, ctx: RequestContext = Depends(get_request_context)):
    repo = ReportRepository(ctx.user_client)
    data = repo.update(report_id, payload.model_dump(exclude_none=True), ctx.company_id)
    return SuccessResponse(data=data)


@router.delete("/{report_id}", response_model=MessageResponse, summary="Delete report")
def delete_report(report_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ReportRepository(ctx.user_client)
    repo.soft_delete(report_id, ctx.company_id)
    return MessageResponse(message="Report deleted.")

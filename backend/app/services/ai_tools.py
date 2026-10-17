"""
AI Assistant Tool Definitions and Secure Execution Engine.

Provides 8 enterprise-grade tools scoped strictly to the authenticated company and knowledge base:
1. get_company_profile — Verified business name, industry, functional currency, and metadata
2. get_sales_analysis — Sales performance, top products, MoM growth, recent transactions (supports custom & historical dates)
3. get_expense_summary — Expense totals, category breakdowns, recent expenses (supports custom & historical dates)
4. get_inventory_status — Total inventory units, catalog count, reorder alerts
5. forecast_revenue — ML-driven revenue forecasting (XGBoost / SARIMA)
6. detect_transaction_anomalies — Isolation Forest transaction anomaly scanner
7. get_business_health_analysis — 5-KPI composite business health scoring & grade
8. search_business_knowledge_base — Verified business guidelines, official MSME schemes & policies, and RAG retrieval

All operations are read-only and strictly scoped to company_id or platform knowledge.
"""
import calendar
import re
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import UUID

from supabase import Client

from app.core.logging import logger
from app.database.retry import execute_with_retry
from app.ml.anomaly_detector import detect_anomaly
from app.ml.business_health import calculate_business_health
from app.ml.model_loader import get_model_loader
from app.ml.revenue_predictor import predict_revenue
from app.schemas.ml import (
    AnomalyDetectionRequest,
    BusinessHealthRequest,
    RevenuePredictionRequest,
)


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        if val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _parse_period_date_range(
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], str]:
    """
    Parse a historical or relative period string or explicit start/end dates.
    Returns (start_iso_date, end_iso_date, display_label).
    Enables historical queries such as 'december 2024', '2024', custom dates, etc.
    """
    if start_date and end_date:
        s = str(start_date)[:10]
        e = str(end_date)[:10]
        return s, e, f"{s} to {e}"

    p = (period or "all").strip().lower()
    today = date.today()

    month_lookup = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
        "nov": 11, "november": 11, "dec": 12, "december": 12,
    }

    if p in ("all", "any", "total", "all_time", "everything"):
        return None, None, "all recorded history"

    if p == "this_month":
        start = today.replace(day=1)
        return start.isoformat(), today.isoformat(), "this month"

    if p == "last_month":
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        first_prev = last_prev.replace(day=1)
        return first_prev.isoformat(), last_prev.isoformat(), "last month"

    if p == "last_30_days":
        return (today - timedelta(days=30)).isoformat(), today.isoformat(), "the last 30 days"

    if p == "last_90_days":
        return (today - timedelta(days=90)).isoformat(), today.isoformat(), "the last 90 days"

    # Explicit ISO range: YYYY-MM-DD to YYYY-MM-DD
    iso_range = re.search(r"(\d{4}-\d{2}-\d{2})\s*(?:to|through|–|-)\s*(\d{4}-\d{2}-\d{2})", p)
    if iso_range:
        return iso_range.group(1), iso_range.group(2), f"{iso_range.group(1)} to {iso_range.group(2)}"

    # YYYY-MM
    ym_match = re.search(r"\b(20\d{2})-(0[1-9]|1[0-2])\b", p)
    if ym_match:
        y, m = int(ym_match.group(1)), int(ym_match.group(2))
        _, last_day = calendar.monthrange(y, m)
        return f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{last_day:02d}", f"{calendar.month_name[m]} {y}"

    # Month name + Year (e.g. "december 2024", "dec 2024")
    my_match = re.search(r"([a-z]+)[,\s_-]+(20\d{2})", p)
    if my_match and my_match.group(1) in month_lookup:
        m = month_lookup[my_match.group(1)]
        y = int(my_match.group(2))
        _, last_day = calendar.monthrange(y, m)
        return f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{last_day:02d}", f"{calendar.month_name[m]} {y}"

    # Year + Month name (e.g. "2024 december")
    ym2_match = re.search(r"(20\d{2})[,\s_-]+([a-z]+)", p)
    if ym2_match and ym2_match.group(2) in month_lookup:
        y = int(ym2_match.group(1))
        m = month_lookup[ym2_match.group(2)]
        _, last_day = calendar.monthrange(y, m)
        return f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{last_day:02d}", f"{calendar.month_name[m]} {y}"

    # Full year (e.g. "2024", "year 2024")
    y_match = re.search(r"\b(20\d{2})\b", p)
    if y_match:
        y = int(y_match.group(1))
        return f"{y:04d}-01-01", f"{y:04d}-12-31", f"the year {y}"

    return None, None, p


class AIToolExecutor:
    """
    Secure Tool Execution Engine for the ALLADIN AI Assistant.
    Enforces multi-tenant data boundaries by injecting company_id and authenticated Supabase client.
    """

    def __init__(self, client: Client, company_id: UUID) -> None:
        self.client = client
        self.company_id = str(company_id)
        self.model_loader = get_model_loader()

    def _fetch_company_currency(self) -> str:
        """Retrieve currency code for this company."""
        try:
            query = (
                self.client.table("companies")
                .select("currency")
                .eq("id", self.company_id)
                .is_("deleted_at", "null")
            )
            res = execute_with_retry(query)
            if res.data and res.data[0].get("currency"):
                return res.data[0]["currency"]
        except Exception as e:
            logger.warning("Failed to fetch company currency: {}", e)
        return "USD"

    # ── Tool 0: Company Profile & Identity ────────────────────────────

    def get_company_profile(self) -> Dict[str, Any]:
        """
        Retrieve verified, safe company profile and identity metadata for the authenticated company.
        Company identity is derived strictly from the server-side authenticated context (self.company_id).
        Never trusts client- or LLM-supplied company IDs.
        """
        try:
            query = (
                self.client.table("companies")
                .select("id, name, slug, industry, country, currency, timezone, subscription_status, is_active")
                .eq("id", self.company_id)
                .is_("deleted_at", "null")
            )
            res = execute_with_retry(query)
            if not res.data:
                return {
                    "company_name": "Unknown",
                    "currency": "USD",
                    "error": "Company profile not found.",
                    "summary": "No company record found for the authenticated session.",
                }
            comp = res.data[0]
            name = comp.get("name") or "Business"
            industry = comp.get("industry") or "General Enterprise"
            country = comp.get("country") or "Global"
            currency = comp.get("currency") or "USD"
            tz = comp.get("timezone") or "UTC"
            sub_status = comp.get("subscription_status") or "active"

            summary = (
                f"The authenticated company name is '{name}'. It operates in the '{industry}' industry "
                f"based in {country}, with functional currency {currency} and timezone {tz}."
            )
            return {
                "company_id": self.company_id,
                "company_name": name,
                "slug": comp.get("slug"),
                "industry": industry,
                "country": country,
                "currency": currency,
                "timezone": tz,
                "subscription_status": sub_status,
                "is_active": comp.get("is_active", True),
                "summary": summary,
            }
        except Exception as e:
            logger.error("Error retrieving company profile: {}", e)
            return {
                "company_name": "Unknown",
                "currency": "USD",
                "error": str(e),
                "summary": "An error occurred while retrieving company profile metadata.",
            }

    # ── Tool 1: Sales Analysis ────────────────────────────────────────

    def get_sales_analysis(
        self,
        period: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Analyze company sales records, revenue, top products, and growth.

        Args:
            period: Filter window ('all', 'december 2024', '2024', 'this_month', 'last_month', 'last_30_days', 'last_90_days').
            start_date: Optional explicit ISO start date (YYYY-MM-DD).
            end_date: Optional explicit ISO end date (YYYY-MM-DD).
            limit: Maximum number of recent sales and top products to inspect (1 to 20).
        """
        limit = max(1, min(20, int(limit or 5)))
        currency = self._fetch_company_currency()
        start_iso, end_iso, period_label = _parse_period_date_range(period, start_date, end_date)

        try:
            query = (
                self.client.table("sales")
                .select("id, sale_number, sale_date, status, total_amount, subtotal, customers(name)")
                .eq("company_id", self.company_id)
                .is_("deleted_at", "null")
                .order("sale_date", desc=True)
            )

            # Apply date filters if resolved
            if start_iso:
                query = query.gte("sale_date", start_iso)
            if end_iso:
                query = query.lte("sale_date", end_iso)

            res = execute_with_retry(query.limit(400))
            sales = res.data or []

            if not sales:
                return {
                    "company_currency": currency,
                    "total_revenue": 0.0,
                    "total_sales_count": 0,
                    "average_sale_value": 0.0,
                    "this_month_revenue": 0.0,
                    "last_month_revenue": 0.0,
                    "growth_percentage": None,
                    "top_products": [],
                    "recent_sales": [],
                    "period": period_label,
                    "summary": f"No confirmed sales transactions found for company in period '{period_label}'. Note: Current recorded historical transactions exist up to December 2024.",
                }

            confirmed_sales = [
                s for s in sales
                if s.get("status") in ("confirmed", "delivered", "completed", "paid")
            ] or sales

            total_revenue = sum(_safe_float(s.get("total_amount")) for s in confirmed_sales)
            total_sales_count = len(confirmed_sales)
            avg_sale_val = (total_revenue / total_sales_count) if total_sales_count > 0 else 0.0

            # MoM calculations
            today = date.today()
            first_this_month = today.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            first_last_month = last_month_end.replace(day=1)

            this_month_rev = 0.0
            last_month_rev = 0.0
            for s in confirmed_sales:
                dt_str = s.get("sale_date")
                if not dt_str:
                    continue
                try:
                    s_date = datetime.strptime(str(dt_str)[:10], "%Y-%m-%d").date()
                    amt = _safe_float(s.get("total_amount"))
                    if s_date >= first_this_month:
                        this_month_rev += amt
                    elif first_last_month <= s_date <= last_month_end:
                        last_month_rev += amt
                except ValueError:
                    pass

            growth_pct = None
            if last_month_rev > 0:
                growth_pct = round(((this_month_rev - last_month_rev) / last_month_rev) * 100, 2)

            # Top selling products aggregation
            top_products = []
            sale_ids = [str(s["id"]) for s in sales[:50] if s.get("id")]
            if sale_ids:
                try:
                    items_query = (
                        self.client.table("sale_items")
                        .select("quantity, unit_price, line_total, product_id, products(name, sku)")
                        .in_("sale_id", sale_ids)
                    )
                    items_res = execute_with_retry(items_query)
                    items = items_res.data or []
                    prod_agg: Dict[str, Dict[str, Any]] = {}
                    for item in items:
                        p_name = item.get("products", {}).get("name") if item.get("products") else "Unknown Product"
                        p_id = str(item.get("product_id") or p_name)
                        qty = _safe_float(item.get("quantity"))
                        line_tot = _safe_float(item.get("line_total") or (qty * _safe_float(item.get("unit_price"))))
                        if p_id not in prod_agg:
                            prod_agg[p_id] = {"name": p_name, "quantity_sold": 0.0, "revenue": 0.0}
                        prod_agg[p_id]["quantity_sold"] += qty
                        prod_agg[p_id]["revenue"] += line_tot

                    sorted_prods = sorted(prod_agg.values(), key=lambda x: x["revenue"], reverse=True)
                    top_products = [
                        {
                            "name": p["name"],
                            "quantity_sold": round(p["quantity_sold"], 2),
                            "revenue": round(p["revenue"], 2),
                        }
                        for p in sorted_prods[:limit]
                    ]
                except Exception as p_err:
                    logger.warning("Could not aggregate top products: {}", p_err)

            recent_sales = [
                {
                    "sale_number": s.get("sale_number") or f"SL-{idx+1:03d}",
                    "date": s.get("sale_date"),
                    "amount": round(_safe_float(s.get("total_amount")), 2),
                    "customer": (s.get("customers", {}) or {}).get("name") or "Walk-in Customer",
                    "status": s.get("status") or "completed",
                }
                for idx, s in enumerate(sales[:limit])
            ]

            summary_parts = [
                f"Total sales revenue for {period_label} is {currency} {total_revenue:,.2f} across {total_sales_count} sales transactions (avg order value: {currency} {avg_sale_val:,.2f})."
            ]
            if growth_pct is not None:
                summary_parts.append(f"Month-over-month sales growth is {growth_pct}%.")
            if top_products:
                summary_parts.append(f"Top-selling product: {top_products[0]['name']} ({currency} {top_products[0]['revenue']:,.2f}).")

            return {
                "company_currency": currency,
                "total_revenue": round(total_revenue, 2),
                "total_sales_count": total_sales_count,
                "average_sale_value": round(avg_sale_val, 2),
                "this_month_revenue": round(this_month_rev, 2),
                "last_month_revenue": round(last_month_rev, 2),
                "growth_percentage": growth_pct,
                "top_products": top_products,
                "recent_sales": recent_sales,
                "period": period_label,
                "summary": " ".join(summary_parts),
            }
        except Exception as e:
            logger.error("Error executing get_sales_analysis tool: {}", e)
            return {
                "company_currency": currency,
                "error": f"Failed to retrieve sales analysis: {str(e)}",
                "summary": "An error occurred while querying company sales records.",
            }

    # ── Tool 2: Expense Summary ───────────────────────────────────────

    def get_expense_summary(
        self,
        period: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: str = "",
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Aggregate company operational expenses, category distribution, and recent spendings.

        Args:
            period: Time period filter ('all', 'december 2024', '2024', 'this_month', 'last_month', 'last_30_days').
            start_date: Optional explicit ISO start date (YYYY-MM-DD).
            end_date: Optional explicit ISO end date (YYYY-MM-DD).
            category: Optional category name to filter by.
            limit: Maximum recent expense records to include (1 to 20).
        """
        limit = max(1, min(20, int(limit or 5)))
        currency = self._fetch_company_currency()
        start_iso, end_iso, period_label = _parse_period_date_range(period, start_date, end_date)

        try:
            query = (
                self.client.table("expenses")
                .select("id, description, amount, expense_date, category_id, categories(name), status")
                .eq("company_id", self.company_id)
                .is_("deleted_at", "null")
                .order("expense_date", desc=True)
            )

            # Apply date filters if resolved
            if start_iso:
                query = query.gte("expense_date", start_iso)
            if end_iso:
                query = query.lte("expense_date", end_iso)

            res = execute_with_retry(query.limit(400))
            expenses = res.data or []

            if not expenses:
                return {
                    "company_currency": currency,
                    "total_expenses": 0.0,
                    "expense_count": 0,
                    "category_breakdown": [],
                    "recent_expenses": [],
                    "period": period_label,
                    "summary": f"No expenses found for company in period '{period_label}'. Note: Current recorded historical transactions exist up to December 2024.",
                }

            # Optional in-memory filter by category
            if category.strip():
                cat_lower = category.strip().lower()
                expenses = [
                    e for e in expenses
                    if cat_lower in ((e.get("categories", {}) or {}).get("name", "")).lower()
                ]

            total_expenses = sum(_safe_float(e.get("amount")) for e in expenses)
            expense_count = len(expenses)

            cat_agg: Dict[str, float] = {}
            for e in expenses:
                c_name = (e.get("categories", {}) or {}).get("name") or "General / Uncategorized"
                cat_agg[c_name] = cat_agg.get(c_name, 0.0) + _safe_float(e.get("amount"))

            cat_breakdown = [
                {
                    "category": k,
                    "amount": round(v, 2),
                    "percentage": round((v / total_expenses * 100), 1) if total_expenses > 0 else 0.0,
                }
                for k, v in sorted(cat_agg.items(), key=lambda x: x[1], reverse=True)
            ]

            recent = [
                {
                    "description": e.get("description") or "Operating Expense",
                    "amount": round(_safe_float(e.get("amount")), 2),
                    "date": e.get("expense_date"),
                    "category": (e.get("categories", {}) or {}).get("name") or "General",
                    "status": e.get("status") or "recorded",
                }
                for e in expenses[:limit]
            ]

            summary = (
                f"Total recorded expenses for {period_label} are {currency} {total_expenses:,.2f} across {expense_count} expense entries. "
            )
            if cat_breakdown:
                top_cat = cat_breakdown[0]
                summary += f"The highest expenditure category is '{top_cat['category']}' ({currency} {top_cat['amount']:,.2f}, {top_cat['percentage']}% of total)."
            else:
                summary += "No expense breakdown categories available."

            return {
                "company_currency": currency,
                "total_expenses": round(total_expenses, 2),
                "expense_count": expense_count,
                "category_breakdown": cat_breakdown,
                "recent_expenses": recent,
                "period": period_label,
                "summary": summary,
            }
        except Exception as e:
            logger.error("Error executing get_expense_summary tool: {}", e)
            return {
                "company_currency": currency,
                "error": f"Failed to retrieve expense summary: {str(e)}",
                "summary": "An error occurred while querying company expense records.",
            }

    # ── Tool 3: Inventory Status & Low-Stock Alerts ───────────────────

    def get_inventory_status(
        self,
        low_stock_only: bool = False,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Inspect physical inventory levels, product catalog count, and restock alerts.

        Args:
            low_stock_only: If True, only return products that have reached or dropped below their reorder threshold.
            limit: Maximum items to return in the list (1 to 50).
        """
        limit = max(1, min(50, int(limit or 10)))

        try:
            prod_query = (
                self.client.table("products")
                .select("id, name, sku, cost_price, selling_price, type")
                .eq("company_id", self.company_id)
                .is_("deleted_at", "null")
            )
            prod_res = execute_with_retry(prod_query)
            products = prod_res.data or []
            total_products = len(products)

            inv_query = (
                self.client.table("inventory")
                .select("product_id, quantity, reorder_level, products(name, sku), warehouses(name)")
                .eq("company_id", self.company_id)
            )
            inv_res = execute_with_retry(inv_query)
            inventory_items = inv_res.data or []

            total_units = sum(_safe_float(i.get("quantity")) for i in inventory_items)
            low_stock_alerts: List[Dict[str, Any]] = []

            for inv in inventory_items:
                qty = _safe_float(inv.get("quantity"))
                reorder = _safe_float(inv.get("reorder_level"), default=10.0)
                if qty <= reorder:
                    p_info = inv.get("products") or {}
                    w_info = inv.get("warehouses") or {}
                    deficit = max(0.0, reorder - qty)
                    low_stock_alerts.append({
                        "product_name": p_info.get("name") or "Unnamed Product",
                        "sku": p_info.get("sku") or "N/A",
                        "current_stock": qty,
                        "reorder_level": reorder,
                        "deficit_units": deficit,
                        "warehouse": w_info.get("name") or "Primary Warehouse",
                    })

            low_stock_count = len(low_stock_alerts)
            if low_stock_count == 0:
                stock_status = "HEALTHY"
                summary = (
                    f"Inventory check across {total_products} catalog SKUs and {total_units:,.0f} total units: "
                    "no critical low-stock items detected at or below reorder threshold."
                )
            elif low_stock_count <= 3:
                stock_status = "WARNING"
                item_names = ", ".join(i["product_name"] for i in low_stock_alerts[:3])
                summary = (
                    f"Warning: {low_stock_count} item(s) are at or below reorder threshold ({item_names}). "
                    f"Total warehouse units: {total_units:,.0f}."
                )
            else:
                stock_status = "CRITICAL_STOCKOUT_RISK"
                summary = (
                    f"Critical Stockout Alert: {low_stock_count} products have dropped to or below reorder levels. "
                    "Immediate procurement replenishment recommended."
                )

            items_to_return = low_stock_alerts if low_stock_only else (low_stock_alerts + [
                {
                    "product_name": (i.get("products") or {}).get("name") or "Item",
                    "sku": (i.get("products") or {}).get("sku") or "N/A",
                    "current_stock": _safe_float(i.get("quantity")),
                    "reorder_level": _safe_float(i.get("reorder_level"), 10.0),
                    "deficit_units": 0.0,
                    "warehouse": (i.get("warehouses") or {}).get("name") or "Primary Warehouse",
                }
                for i in inventory_items if _safe_float(i.get("quantity")) > _safe_float(i.get("reorder_level"), 10.0)
            ])

            return {
                "total_catalog_products": total_products,
                "total_stock_units": round(total_units, 2),
                "low_stock_count": low_stock_count,
                "stock_status": stock_status,
                "low_stock_items": low_stock_alerts[:limit],
                "inventory_items": items_to_return[:limit],
                "summary": summary,
            }
        except Exception as e:
            logger.error("Error executing get_inventory_status tool: {}", e)
            return {
                "error": f"Failed to inspect inventory: {str(e)}",
                "stock_status": "UNKNOWN",
                "summary": "An error occurred while checking warehouse inventory records.",
            }

    # ── Tool 4: Revenue Forecasting ───────────────────────────────────

    def forecast_revenue(
        self,
        months_ahead: int = 6,
        model_type: str = "xgboost",
    ) -> Dict[str, Any]:
        """
        Generate machine-learning monthly revenue forecasts using historical sales records.

        Args:
            months_ahead: Projection horizon in months (1 to 24).
            model_type: Algorithm selection ('xgboost' or 'sarima').
        """
        months_ahead = max(1, min(24, int(months_ahead or 6)))
        model_type = (model_type or "xgboost").lower()
        if model_type not in ("xgboost", "sarima"):
            model_type = "xgboost"

        currency = self._fetch_company_currency()

        try:
            # Query actual monthly sales numbers for company
            sales_query = (
                self.client.table("sales")
                .select("total_amount, sale_date, status")
                .eq("company_id", self.company_id)
                .is_("deleted_at", "null")
                .order("sale_date", desc=False)
            )
            sales_res = execute_with_retry(sales_query)
            sales = sales_res.data or []

            # Aggregate monthly historical totals
            monthly_totals: Dict[str, float] = {}
            for s in sales:
                s_date = s.get("sale_date")
                if not s_date:
                    continue
                month_key = str(s_date)[:7]  # YYYY-MM
                amt = _safe_float(s.get("total_amount"))
                monthly_totals[month_key] = monthly_totals.get(month_key, 0.0) + amt

            history_list = [v for _, v in sorted(monthly_totals.items())] if monthly_totals else []

            # Run prediction through existing ML service
            req = RevenuePredictionRequest(
                months_ahead=months_ahead,
                model_type=model_type,
                historical_revenue=history_list if history_list else None,
            )

            pred_res = predict_revenue(req, self.model_loader)

            formatted_forecasts = [
                {
                    "month": item.month,
                    "predicted_revenue": round(item.predicted_revenue, 2),
                    "confidence_lower": round(item.confidence_lower, 2),
                    "confidence_upper": round(item.confidence_upper, 2),
                }
                for item in pred_res.predictions
            ]

            summary = (
                f"Revenue projection over next {months_ahead} months totals {currency} {pred_res.total_projected_revenue:,.2f} "
                f"(avg {currency} {pred_res.average_monthly_revenue:,.2f}/month) with an {pred_res.growth_trend} growth trajectory "
                f"using {pred_res.model_used}."
            )

            return {
                "company_currency": currency,
                "model_used": pred_res.model_used,
                "forecast_period_months": months_ahead,
                "total_projected_revenue": round(pred_res.total_projected_revenue, 2),
                "average_monthly_revenue": round(pred_res.average_monthly_revenue, 2),
                "growth_trend": pred_res.growth_trend,
                "predictions": formatted_forecasts,
                "historical_data_points_used": len(history_list),
                "summary": summary,
            }
        except Exception as e:
            logger.error("Error executing forecast_revenue tool: {}", e)
            return {
                "company_currency": currency,
                "error": f"Revenue forecast model could not complete: {str(e)}",
                "summary": "Revenue forecast model is temporarily unable to calculate projections.",
            }

    # ── Tool 5: Anomaly Detection ─────────────────────────────────────

    def detect_transaction_anomalies(
        self,
        net_amount: Optional[float] = None,
        discount_pct: float = 0.0,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Detect transaction outliers or audit company sales transactions using Isolation Forest.

        Args:
            net_amount: Optional specific transaction amount to test for anomaly.
            discount_pct: Discount percentage applied to the transaction (0 to 100).
            limit: If net_amount is omitted, scan recent company sales up to limit (1 to 20).
        """
        limit = max(1, min(20, int(limit or 5)))
        currency = self._fetch_company_currency()

        try:
            # Query recent sales to calculate 28-day baseline
            sales_query = (
                self.client.table("sales")
                .select("id, sale_number, total_amount, subtotal, discount_amount, sale_date")
                .eq("company_id", self.company_id)
                .is_("deleted_at", "null")
                .order("sale_date", desc=True)
                .limit(50)
            )
            sales_res = execute_with_retry(sales_query)
            sales = sales_res.data or []
            amounts = [_safe_float(s.get("total_amount")) for s in sales if _safe_float(s.get("total_amount")) > 0]

            if amounts:
                import numpy as np
                mean_val = float(np.mean(amounts))
                std_val = float(np.std(amounts)) if len(amounts) > 1 else 1000.0
                if std_val < 1.0:
                    std_val = 1000.0
            else:
                mean_val = 18500.0
                std_val = 6200.0

            # Case A: User asked about a specific amount
            if net_amount is not None:
                net_val = float(net_amount)
                disc_val = float(discount_pct or 0.0)
                req = AnomalyDetectionRequest(
                    net_amount=net_val,
                    discount_pct=disc_val,
                    roll28_mean=mean_val,
                    roll28_std=std_val,
                )
                res = detect_anomaly(req, self.model_loader)
                status_str = "ANOMALY_DETECTED" if res.is_anomaly else "NORMAL"
                summary = (
                    f"Transaction amount {currency} {net_val:,.2f} (discount {disc_val:.1f}%) evaluated as {status_str} "
                    f"[Severity: {res.severity}, Confidence: {res.confidence}%]. {res.reason}"
                )
                return {
                    "company_currency": currency,
                    "target_amount": net_val,
                    "discount_pct": disc_val,
                    "is_anomaly": res.is_anomaly,
                    "severity": res.severity,
                    "confidence": res.confidence,
                    "anomaly_score": res.anomaly_score,
                    "reason": res.reason,
                    "summary": summary,
                }

            # Case B: Scan company's recent sales
            flagged = []
            for s in sales[:limit]:
                amt = _safe_float(s.get("total_amount"))
                subtot = _safe_float(s.get("subtotal") or amt)
                disc_amt = _safe_float(s.get("discount_amount"))
                disc_pct = (disc_amt / subtot * 100.0) if subtot > 0 else 0.0

                req = AnomalyDetectionRequest(
                    net_amount=amt,
                    discount_pct=disc_pct,
                    roll28_mean=mean_val,
                    roll28_std=std_val,
                )
                eval_res = detect_anomaly(req, self.model_loader)
                if eval_res.is_anomaly or eval_res.severity in ("HIGH", "CRITICAL"):
                    flagged.append({
                        "sale_number": s.get("sale_number") or "N/A",
                        "date": s.get("sale_date"),
                        "amount": amt,
                        "discount_pct": round(disc_pct, 1),
                        "severity": eval_res.severity,
                        "confidence": eval_res.confidence,
                        "reason": eval_res.reason,
                    })

            if flagged:
                summary = (
                    f"Scanned {len(sales[:limit])} recent transactions and flagged {len(flagged)} potential anomaly(ies). "
                    f"Highest severity: {flagged[0]['severity']} for sale {flagged[0]['sale_number']}."
                )
            else:
                summary = (
                    f"Scanned {len(sales[:limit])} recent transactions using Isolation Forest. "
                    "No anomalous patterns or suspicious discounts detected."
                )

            return {
                "company_currency": currency,
                "scanned_transactions_count": len(sales[:limit]),
                "anomalies_detected": len(flagged) > 0,
                "flagged_transactions": flagged,
                "baseline_mean": round(mean_val, 2),
                "baseline_std": round(std_val, 2),
                "summary": summary,
            }
        except Exception as e:
            logger.error("Error executing detect_transaction_anomalies tool: {}", e)
            return {
                "company_currency": currency,
                "error": f"Anomaly detection model failed: {str(e)}",
                "summary": "Transaction anomaly detector encountered an error while scanning records.",
            }

    # ── Tool 6: Business Health Analysis ──────────────────────────────

    def get_business_health_analysis(
        self,
        revenue_growth: Optional[float] = None,
        profit_margin: Optional[float] = None,
        expense_control: Optional[float] = None,
        inventory_turnover: Optional[float] = None,
        payment_collection: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate overall company Business Health Score (0-100), risk tier, and operational advice.
        If KPIs are not provided, automatically derives live values from the company ERP data.

        Args:
            revenue_growth: MoM revenue growth ratio (e.g. 0.15 for 15%).
            profit_margin: Net profit margin ratio (e.g. 0.20 for 20%).
            expense_control: Expense control efficiency index (0.0 to 1.0).
            inventory_turnover: Annual inventory turnover ratio.
            payment_collection: Accounts receivable collection efficiency (0.0 to 1.0).
        """
        try:
            # 1. Fetch live metrics if any parameter is omitted
            sales_info = self.get_sales_analysis(period="all", limit=5)
            exp_info = self.get_expense_summary(period="all", limit=5)

            tot_rev = _safe_float(sales_info.get("total_revenue"))
            tot_exp = _safe_float(exp_info.get("total_expenses"))

            # Derive revenue growth
            if revenue_growth is None:
                growth_pct = sales_info.get("growth_percentage")
                revenue_growth = (growth_pct / 100.0) if growth_pct is not None else 0.12

            # Derive profit margin
            if profit_margin is None:
                profit_margin = ((tot_rev - tot_exp) / tot_rev) if tot_rev > 0 else 0.18

            # Derive expense control
            if expense_control is None:
                exp_ratio = (tot_exp / tot_rev) if tot_rev > 0 else 0.60
                expense_control = max(0.0, min(1.0, 1.0 - (exp_ratio * 0.5)))

            # Derive inventory turnover
            if inventory_turnover is None:
                inv_info = self.get_inventory_status(low_stock_only=False, limit=5)
                tot_units = _safe_float(inv_info.get("total_stock_units"), default=100.0)
                inventory_turnover = min(10.0, max(1.0, (tot_rev / (tot_units * 1000.0 + 1e-6))))

            # Derive payment collection
            if payment_collection is None:
                invc_query = (
                    self.client.table("invoices")
                    .select("total_amount, amount_paid, amount_due, status")
                    .eq("company_id", self.company_id)
                    .eq("invoice_type", "receivable")
                    .is_("deleted_at", "null")
                )
                invc_res = execute_with_retry(invc_query)
                invoices = invc_res.data or []
                if invoices:
                    tot_due = sum(_safe_float(i.get("total_amount")) for i in invoices)
                    tot_paid = sum(_safe_float(i.get("amount_paid")) for i in invoices)
                    payment_collection = (tot_paid / tot_due) if tot_due > 0 else 0.85
                else:
                    payment_collection = 0.88

            # Clamp parameters into valid ranges
            revenue_growth = float(max(-0.5, min(1.0, revenue_growth)))
            profit_margin = float(max(-0.2, min(0.4, profit_margin)))
            expense_control = float(max(0.0, min(1.0, expense_control)))
            inventory_turnover = float(max(0.0, min(10.0, inventory_turnover)))
            payment_collection = float(max(0.0, min(1.0, payment_collection)))

            req = BusinessHealthRequest(
                revenue_growth=revenue_growth,
                profit_margin=profit_margin,
                expense_control=expense_control,
                inventory_turnover=inventory_turnover,
                payment_collection=payment_collection,
            )

            res = calculate_business_health(req, self.model_loader)

            summary = (
                f"Business Health Score is {res.health_score}/100 [Grade {res.health_grade}, Risk Tier: {res.risk_rating}]. "
                f"Key action: {res.recommendations[0] if res.recommendations else 'Maintain operational discipline.'}"
            )

            return {
                "health_score": res.health_score,
                "health_grade": res.health_grade,
                "risk_rating": res.risk_rating,
                "sub_scores": res.sub_scores,
                "recommendations": res.recommendations,
                "evaluated_kpis": {
                    "revenue_growth_pct": round(revenue_growth * 100, 1),
                    "profit_margin_pct": round(profit_margin * 100, 1),
                    "expense_control_index": round(expense_control, 2),
                    "inventory_turnover_ratio": round(inventory_turnover, 2),
                    "payment_collection_efficiency": round(payment_collection * 100, 1),
                },
                "summary": summary,
            }
        except Exception as e:
            logger.error("Error executing get_business_health_analysis tool: {}", e)
            return {
                "error": f"Failed to compute health score: {str(e)}",
                "summary": "Unable to calculate business health score at this time.",
            }

    # ── Tool 7: Business Knowledge Base Search (RAG) ──────────────────

    def search_business_knowledge_base(
        self,
        query: str,
        doc_type: Optional[str] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """
        Search verified business knowledge base, official regulatory documents,
        MSME schemes, accounting standards, financial concepts, and working capital guides.
        Returns grounded passages with source citations.
        """
        query_clean = (query or "").strip()
        if not query_clean:
            return {
                "query": "",
                "results_count": 0,
                "passages": [],
                "citations": [],
                "formatted_context": "No search query provided.",
                "summary": "Please provide a valid query to search the business knowledge base.",
            }

        try:
            from app.services.rag.retriever import RAGRetriever

            cid = None
            if self.company_id:
                try:
                    cid = UUID(str(self.company_id))
                except (ValueError, TypeError):
                    pass

            retriever = RAGRetriever(client=self.client, company_id=cid)
            results = retriever.retrieve(
                query=query_clean,
                top_k=int(top_k or 4),
                doc_type=doc_type,
            )

            if not results:
                return {
                    "query": query_clean,
                    "results_count": 0,
                    "passages": [],
                    "citations": [],
                    "formatted_context": "No relevant business knowledge passages found in the knowledge base.",
                    "summary": f"No knowledge base entries matched '{query_clean}'.",
                }

            passages = []
            citations = []
            for r in results:
                passages.append({
                    "doc_id": r.get("doc_id"),
                    "title": r.get("title"),
                    "author": r.get("author"),
                    "section_title": r.get("section_title"),
                    "page_number": r.get("page_number"),
                    "content": r.get("content"),
                    "similarity": r.get("similarity"),
                    "citation": r.get("citation"),
                    "is_draft": r.get("is_draft", False),
                    "status_label": r.get("status_label", ""),
                })
                if r.get("citation") and r["citation"] not in citations:
                    citations.append(r["citation"])

            formatted_xml = retriever.format_for_assistant(results)

            return {
                "query": query_clean,
                "results_count": len(results),
                "passages": passages,
                "citations": citations,
                "formatted_context": formatted_xml,
                "summary": f"Retrieved {len(results)} relevant knowledge passages from official guides and policies.",
            }

        except Exception as e:
            logger.error("Error executing search_business_knowledge_base tool: {}", e)
            return {
                "error": str(e),
                "query": query_clean,
                "results_count": 0,
                "passages": [],
                "citations": [],
                "summary": f"Failed to retrieve business knowledge: {str(e)}",
            }

    # ── Universal Tool Invocation Gateway ─────────────────────────────

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically and safely dispatch execution to the matching tool function.
        """
        tool_map: Dict[str, Callable[..., Dict[str, Any]]] = {
            "get_company_profile": self.get_company_profile,
            "get_sales_analysis": self.get_sales_analysis,
            "get_expense_summary": self.get_expense_summary,
            "get_inventory_status": self.get_inventory_status,
            "forecast_revenue": self.forecast_revenue,
            "detect_transaction_anomalies": self.detect_transaction_anomalies,
            "get_business_health_analysis": self.get_business_health_analysis,
            "search_business_knowledge_base": self.search_business_knowledge_base,
        }

        func = tool_map.get(tool_name)
        if not func:
            logger.warning("Unrecognized tool '{}' requested by LLM.", tool_name)
            return {
                "error": f"Tool '{tool_name}' is not supported.",
                "summary": f"Failed to execute unknown tool '{tool_name}'.",
            }

        logger.info("Executing AI Tool '{}' with args: {}", tool_name, arguments)
        try:
            # Filter kwargs to only those accepted by the function
            import inspect
            sig = inspect.signature(func)
            valid_args = {k: v for k, v in arguments.items() if k in sig.parameters}
            return func(**valid_args)
        except Exception as e:
            logger.error("Tool '{}' raised unhandled error: {}", tool_name, e)
            return {
                "error": str(e),
                "summary": f"Execution of '{tool_name}' failed.",
            }


# ── Tool Declarations for LLM Tool Calling ────────────────────────────

TOOL_DECLARATIONS = [
    {
        "name": "get_company_profile",
        "description": (
            "Retrieve verified company identity and profile metadata (company name, industry, "
            "country of operation, functional currency, timezone, and fiscal calendar) for the authenticated business. "
            "Use this tool when asked about the company name, business identity, what company this is, "
            "or basic business profile."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        },
    },
    {
        "name": "get_sales_analysis",
        "description": (
            "Retrieve verified company sales metrics including total revenue, order count, "
            "average order value, month-over-month growth rate, top-selling products, and recent sales transactions. "
            "Supports historical date filtering (e.g. 'december 2024', '2024', or custom start/end dates)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "period": {
                    "type": "STRING",
                    "description": "Time window: e.g. 'all', 'december 2024', '2024', 'this_month', 'last_month', 'last_30_days', 'last_90_days'.",
                },
                "start_date": {
                    "type": "STRING",
                    "description": "Optional ISO start date (YYYY-MM-DD) for custom historical ranges.",
                },
                "end_date": {
                    "type": "STRING",
                    "description": "Optional ISO end date (YYYY-MM-DD) for custom historical ranges.",
                },
                "limit": {
                    "type": "INTEGER",
                    "description": "Max number of top products and recent sales to return (default: 5).",
                },
            },
        },
    },
    {
        "name": "get_expense_summary",
        "description": (
            "Retrieve verified company operating expenses, total expenditure, category-wise breakdown, "
            "and recent expense ledger entries. Supports historical date filtering (e.g. 'december 2024', '2024', or custom dates)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "period": {
                    "type": "STRING",
                    "description": "Time period: e.g. 'all', 'december 2024', '2024', 'this_month', 'last_month', 'last_30_days'.",
                },
                "start_date": {
                    "type": "STRING",
                    "description": "Optional ISO start date (YYYY-MM-DD).",
                },
                "end_date": {
                    "type": "STRING",
                    "description": "Optional ISO end date (YYYY-MM-DD).",
                },
                "category": {
                    "type": "STRING",
                    "description": "Optional category name filter (e.g. 'Rent', 'Salaries', 'Utilities').",
                },
                "limit": {
                    "type": "INTEGER",
                    "description": "Max recent expense records to include (default: 5).",
                },
            },
        },
    },
    {
        "name": "get_inventory_status",
        "description": (
            "Check warehouse inventory levels, total active SKUs, physical units in stock, "
            "and identify products at or below reorder threshold (low-stock restock alerts)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "low_stock_only": {
                    "type": "BOOLEAN",
                    "description": "If true, only returns items that urgently require restocking.",
                },
                "limit": {
                    "type": "INTEGER",
                    "description": "Maximum number of items to list (default: 10).",
                },
            },
        },
    },
    {
        "name": "forecast_revenue",
        "description": (
            "Forecast future company monthly revenues using trained machine learning models (XGBoost or SARIMA) "
            "grounded in historical sales data. Provides projected monthly revenues and growth trajectory."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "months_ahead": {
                    "type": "INTEGER",
                    "description": "Forecast horizon in months, from 1 to 24 (default: 6).",
                },
                "model_type": {
                    "type": "STRING",
                    "description": "ML algorithm to use: 'xgboost' or 'sarima' (default: 'xgboost').",
                },
            },
        },
    },
    {
        "name": "detect_transaction_anomalies",
        "description": (
            "Detect financial anomalies and price outliers using an Isolation Forest ML model. "
            "Can audit a specific transaction amount or scan recent company sales for suspicious activity."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "net_amount": {
                    "type": "NUMBER",
                    "description": "Optional specific transaction amount to test for an anomaly.",
                },
                "discount_pct": {
                    "type": "NUMBER",
                    "description": "Discount percentage applied (0 to 100).",
                },
                "limit": {
                    "type": "INTEGER",
                    "description": "Number of recent company transactions to scan if net_amount is not given (default: 5).",
                },
            },
        },
    },
    {
        "name": "get_business_health_analysis",
        "description": (
            "Evaluate composite company Business Health Score (0-100), letter grade (A-F), risk rating, "
            "and actionable operational recommendations based on 5 core financial KPIs: revenue growth, "
            "profit margin, expense control, inventory turnover, and invoice payment collection."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "revenue_growth": {
                    "type": "NUMBER",
                    "description": "Optional custom revenue growth ratio (e.g. 0.15 for 15%).",
                },
                "profit_margin": {
                    "type": "NUMBER",
                    "description": "Optional custom profit margin ratio (e.g. 0.22 for 22%).",
                },
                "expense_control": {
                    "type": "NUMBER",
                    "description": "Optional custom expense control score (0.0 to 1.0).",
                },
                "inventory_turnover": {
                    "type": "NUMBER",
                    "description": "Optional custom inventory turnover ratio.",
                },
                "payment_collection": {
                    "type": "NUMBER",
                    "description": "Optional custom receivable collection ratio (0.0 to 1.0).",
                },
            },
        },
    },
    {
        "name": "search_business_knowledge_base",
        "description": (
            "Search verified business knowledge base, official regulatory documents, MSME schemes, "
            "accounting standards, financial concepts, and working capital guides. "
            "Use this tool for conceptual explanations, government guidelines (e.g. RBI collateral-free rules), "
            "financial formulas, and best practices. Do NOT use this tool for live company sales or inventory numbers."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "The search query or concept to look up (e.g., 'collateral-free loan limit RBI', 'working capital cycle calculation', 'cash flow vs profit').",
                },
                "doc_type": {
                    "type": "STRING",
                    "description": "Optional filter for document type: 'official_source', 'internal_guide', or 'company_private'.",
                },
                "top_k": {
                    "type": "INTEGER",
                    "description": "Number of relevant passages to retrieve (default: 4).",
                },
            },
        },
    },
]

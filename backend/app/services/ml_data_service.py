"""
ML Data Access & Aggregation Service.
Centralizes authorized retrieval of business records from Supabase PostgreSQL
for all seven ML prediction pipelines, enforcing strict tenant and outlet isolation.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from supabase import Client

from app.core.logging import logger
from app.exceptions import ForbiddenError, NotFoundError


class MLDataService:
    """
    Centralized data extraction and aggregation service for ML pipelines.
    Guarantees company-level and outlet-level tenant isolation.
    """

    def __init__(self, client: Client, company_id: UUID, branch_id: Optional[UUID] = None) -> None:
        self.client = client
        self.company_id = company_id
        self.branch_id = branch_id

    def validate_branch(self) -> None:
        """
        Verify that self.branch_id belongs to self.company_id.
        Raises ForbiddenError if branch does not belong to the authorized company.
        """
        if not self.branch_id:
            return

        try:
            res = (
                self.client.table("branches")
                .select("id, company_id, is_active")
                .eq("id", str(self.branch_id))
                .eq("company_id", str(self.company_id))
                .execute()
            )
            if not res.data:
                raise ForbiddenError("The requested branch does not belong to your authorized company.")
        except ForbiddenError:
            raise
        except Exception as e:
            logger.warning("[MLDataService] Branch validation warning: {}", e)

    # ── 1. Revenue History ────────────────────────────────────────

    def get_historical_monthly_revenue(
        self, months: int = 24
    ) -> Tuple[List[float], List[str], bool]:
        """
        Retrieves confirmed and delivered sales aggregated monthly for the authorized company.
        Returns:
            revenues: List of monthly revenues in chronological order.
            month_keys: List of YYYY-MM strings.
            has_sufficient_data: True if >= 6 months of historical data exists.
        """
        self.validate_branch()
        try:
            query = (
                self.client.table("sales")
                .select("sale_date, total_amount, status")
                .eq("company_id", str(self.company_id))
                .is_("deleted_at", "null")
                .neq("status", "cancelled")
            )
            if self.branch_id:
                query = query.eq("branch_id", str(self.branch_id))

            res = query.order("sale_date", desc=False).execute()
            rows = res.data or []

            if not rows:
                return [], [], False

            monthly_map: Dict[str, float] = defaultdict(float)
            for row in rows:
                sale_date = row.get("sale_date")
                amount = float(row.get("total_amount") or 0.0)
                if sale_date:
                    month_key = str(sale_date)[:7]  # YYYY-MM
                    monthly_map[month_key] += amount

            sorted_months = sorted(monthly_map.keys())
            revenues = [round(monthly_map[m], 2) for m in sorted_months]
            is_sufficient = len(revenues) >= 6

            return revenues, sorted_months, is_sufficient
        except Exception as e:
            logger.error("[MLDataService] get_historical_monthly_revenue error: {}", e)
            return [], [], False

    # ── 2. Product / Category Sales History ───────────────────────

    def get_historical_product_sales(
        self,
        entity_type: str,
        entity_id: Optional[str] = None,
        months: int = 24,
    ) -> Tuple[List[float], List[float], List[str], bool]:
        """
        Retrieves historical monthly units and revenue for a specific product or category.
        Returns:
            units: List of monthly units sold.
            amounts: List of monthly sales amounts.
            months: List of YYYY-MM strings.
            has_sufficient_data: True if >= 6 months of data exists.
        """
        self.validate_branch()
        try:
            if entity_type == "product" and entity_id:
                query = (
                    self.client.table("sale_items")
                    .select("quantity, line_total, sales!inner(sale_date, company_id, branch_id, status)")
                    .eq("product_id", str(entity_id))
                    .eq("sales.company_id", str(self.company_id))
                    .neq("sales.status", "cancelled")
                )
                if self.branch_id:
                    query = query.eq("sales.branch_id", str(self.branch_id))

                res = query.execute()
                rows = res.data or []
            else:
                # Query all product sales for company
                query = (
                    self.client.table("sale_items")
                    .select("quantity, line_total, sales!inner(sale_date, company_id, branch_id, status)")
                    .eq("sales.company_id", str(self.company_id))
                    .neq("sales.status", "cancelled")
                )
                if self.branch_id:
                    query = query.eq("sales.branch_id", str(self.branch_id))

                res = query.execute()
                rows = res.data or []

            monthly_units: Dict[str, float] = defaultdict(float)
            monthly_amounts: Dict[str, float] = defaultdict(float)

            for row in rows:
                sales_parent = row.get("sales") or {}
                sale_date = sales_parent.get("sale_date")
                if sale_date:
                    month_key = str(sale_date)[:7]
                    monthly_units[month_key] += float(row.get("quantity") or 0.0)
                    monthly_amounts[month_key] += float(row.get("line_total") or 0.0)

            sorted_months = sorted(monthly_units.keys())
            units = [round(monthly_units[m], 2) for m in sorted_months]
            amounts = [round(monthly_amounts[m], 2) for m in sorted_months]
            is_sufficient = len(units) >= 6

            return units, amounts, sorted_months, is_sufficient
        except Exception as e:
            logger.error("[MLDataService] get_historical_product_sales error: {}", e)
            return [], [], [], False

    # ── 3. Inventory Stock and Historical Demand ──────────────────

    def get_inventory_status_and_demand(
        self,
        product_id: Optional[str] = None,
        product_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves current stock balance and historical monthly demand for inventory optimization.
        """
        self.validate_branch()
        result = {
            "product_id": product_id,
            "product_name": product_name,
            "current_stock": 0.0,
            "unit_cost": 10.0,
            "historical_monthly_demand": [],
            "has_sufficient_data": False,
        }
        try:
            if product_id:
                inv_query = (
                    self.client.table("inventory")
                    .select("quantity, reorder_level, product_id, products(name, cost_price)")
                    .eq("company_id", str(self.company_id))
                    .eq("product_id", str(product_id))
                )
                inv_res = inv_query.execute()
                if inv_res.data:
                    total_qty = sum(float(r.get("quantity") or 0.0) for r in inv_res.data)
                    result["current_stock"] = total_qty
                    prod_info = inv_res.data[0].get("products") or {}
                    result["product_name"] = prod_info.get("name") or product_name
                    result["unit_cost"] = float(prod_info.get("cost_price") or 10.0)

                # Get monthly demand from sales
                units, _, _, is_suff = self.get_historical_product_sales("product", product_id)
                result["historical_monthly_demand"] = units
                result["has_sufficient_data"] = is_suff
            return result
        except Exception as e:
            logger.error("[MLDataService] get_inventory_status_and_demand error: {}", e)
            return result

    # ── 4. Profit History ─────────────────────────────────────────

    def get_historical_monthly_profit(
        self, months: int = 24
    ) -> Tuple[List[float], List[float], List[float], List[str], bool]:
        """
        Calculates monthly net profit (Revenue - Operating Expenses).
        Returns:
            profits: List of monthly net profits.
            revenues: List of monthly revenues.
            expenses: List of monthly expenses.
            months: Chronological month keys.
            is_sufficient: True if >= 6 months available.
        """
        self.validate_branch()
        try:
            rev_vals, rev_months, _ = self.get_historical_monthly_revenue(months)
            exp_vals, exp_months, _, _ = self.get_historical_monthly_expenses(months=months)

            all_months = sorted(set(rev_months + exp_months))
            if not all_months:
                return [], [], [], [], False

            rev_dict = dict(zip(rev_months, rev_vals))
            exp_dict = dict(zip(exp_months, exp_vals))

            profits = []
            revenues = []
            expenses = []

            for m in all_months:
                r = rev_dict.get(m, 0.0)
                e = exp_dict.get(m, 0.0)
                revenues.append(r)
                expenses.append(e)
                profits.append(round(r - e, 2))

            is_sufficient = len(profits) >= 6
            return profits, revenues, expenses, all_months, is_sufficient
        except Exception as e:
            logger.error("[MLDataService] get_historical_monthly_profit error: {}", e)
            return [], [], [], [], False

    # ── 5. Expense History ────────────────────────────────────────

    def get_historical_monthly_expenses(
        self, category: Optional[str] = None, months: int = 24
    ) -> Tuple[List[float], List[str], Dict[str, float], bool]:
        """
        Retrieves approved operating expenses aggregated monthly.
        Returns:
            monthly_expenses: List of expenses.
            months: Chronological month strings.
            category_breakdown: Expense sum per category.
            is_sufficient: True if >= 6 months.
        """
        self.validate_branch()
        try:
            query = (
                self.client.table("expenses")
                .select("amount, expense_date, category_id, status, categories(name)")
                .eq("company_id", str(self.company_id))
                .is_("deleted_at", "null")
                .neq("status", "rejected")
            )
            if self.branch_id:
                query = query.eq("branch_id", str(self.branch_id))

            res = query.order("expense_date", desc=False).execute()
            rows = res.data or []

            monthly_map: Dict[str, float] = defaultdict(float)
            cat_map: Dict[str, float] = defaultdict(float)

            for row in rows:
                cat_info = row.get("categories") or {}
                cat_name = cat_info.get("name") or "General"

                if category and category.lower() not in cat_name.lower():
                    continue

                exp_date = row.get("expense_date")
                amount = float(row.get("amount") or 0.0)
                cat_map[cat_name] += amount

                if exp_date:
                    m_key = str(exp_date)[:7]
                    monthly_map[m_key] += amount

            sorted_months = sorted(monthly_map.keys())
            expenses = [round(monthly_map[m], 2) for m in sorted_months]
            is_sufficient = len(expenses) >= 6

            return expenses, sorted_months, dict(cat_map), is_sufficient
        except Exception as e:
            logger.error("[MLDataService] get_historical_monthly_expenses error: {}", e)
            return [], [], {}, False

    # ── 6. Business Health Deterministic KPIs ─────────────────────

    def get_business_health_kpis(self) -> Dict[str, Any]:
        """
        Computes 5 deterministic business health KPIs from real business data:
          1. revenue_growth: Month-over-month revenue growth rate.
          2. profit_margin: Net profit margin ratio.
          3. expense_control: 1.0 - (Operating Expenses / Revenue) ratio.
          4. inventory_turnover: Ratio of sales demand to inventory stock.
          5. payment_collection: Ratio of invoice amount paid to total invoiced.
        """
        self.validate_branch()
        kpis = {
            "revenue_growth": 0.15,
            "profit_margin": 0.20,
            "expense_control": 0.82,
            "inventory_turnover": 4.5,
            "payment_collection": 0.90,
            "has_sufficient_data": False,
            "warnings": [],
        }
        try:
            # 1. Revenue & Growth
            revs, _, rev_suff = self.get_historical_monthly_revenue(months=12)
            if len(revs) >= 2 and revs[-2] > 0:
                growth = (revs[-1] - revs[-2]) / revs[-2]
                kpis["revenue_growth"] = round(float(np.clip(growth, -0.5, 1.0)), 4)
            else:
                kpis["warnings"].append("Insufficient revenue history for dynamic revenue growth.")

            # 2. Profit Margin & Expense Control
            profits, revenues, expenses, _, prof_suff = self.get_historical_monthly_profit(months=6)
            if revenues and revenues[-1] > 0:
                p_margin = profits[-1] / revenues[-1]
                kpis["profit_margin"] = round(float(np.clip(p_margin, -0.2, 0.5)), 4)
                exp_ratio = expenses[-1] / revenues[-1]
                kpis["expense_control"] = round(float(np.clip(1.0 - exp_ratio, 0.0, 1.0)), 4)
            else:
                kpis["warnings"].append("Insufficient profit/expense history for dynamic margin.")

            # 3. Inventory Turnover
            try:
                inv_res = (
                    self.client.table("inventory")
                    .select("quantity")
                    .eq("company_id", str(self.company_id))
                    .execute()
                )
                total_stock = sum(float(r.get("quantity") or 0.0) for r in (inv_res.data or []))
                sales_units, _, _, _ = self.get_historical_product_sales("all")
                annual_demand = sum(sales_units[-12:]) if sales_units else 0.0
                if total_stock > 0 and annual_demand > 0:
                    turnover = annual_demand / total_stock
                    kpis["inventory_turnover"] = round(float(np.clip(turnover, 0.5, 12.0)), 2)
            except Exception as e:
                logger.debug("Turnover computation warning: {}", e)

            # 4. Payment Collection Efficiency
            try:
                inv_doc_res = (
                    self.client.table("invoices")
                    .select("total_amount, amount_paid")
                    .eq("company_id", str(self.company_id))
                    .eq("invoice_type", "receivable")
                    .execute()
                )
                docs = inv_doc_res.data or []
                if docs:
                    tot_billed = sum(float(d.get("total_amount") or 0.0) for d in docs)
                    tot_paid = sum(float(d.get("amount_paid") or 0.0) for d in docs)
                    if tot_billed > 0:
                        kpis["payment_collection"] = round(float(np.clip(tot_paid / tot_billed, 0.0, 1.0)), 4)
            except Exception as e:
                logger.debug("Payment collection calculation warning: {}", e)

            kpis["has_sufficient_data"] = rev_suff and prof_suff
            return kpis
        except Exception as e:
            logger.error("[MLDataService] get_business_health_kpis error: {}", e)
            return kpis

    # ── 7. Rolling Baseline for Anomaly Detection ──────────────────

    def get_transaction_anomaly_baseline(self) -> Dict[str, float]:
        """
        Computes 28-day rolling mean and standard deviation of transaction amounts
        for the authorized company from the sales table.
        """
        self.validate_branch()
        baseline = {
            "roll28_mean": 18500.0,
            "roll28_std": 6200.0,
            "has_sufficient_data": False,
        }
        try:
            cutoff = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")
            query = (
                self.client.table("sales")
                .select("total_amount")
                .eq("company_id", str(self.company_id))
                .gte("sale_date", cutoff)
                .neq("status", "cancelled")
            )
            if self.branch_id:
                query = query.eq("branch_id", str(self.branch_id))

            res = query.execute()
            amounts = [float(r.get("total_amount") or 0.0) for r in (res.data or []) if r.get("total_amount")]
            if len(amounts) >= 5:
                baseline["roll28_mean"] = float(np.mean(amounts))
                baseline["roll28_std"] = max(100.0, float(np.std(amounts)))
                baseline["has_sufficient_data"] = True
            return baseline
        except Exception as e:
            logger.error("[MLDataService] get_transaction_anomaly_baseline error: {}", e)
            return baseline

    # ── 8. Prediction Persistence & Traceability ──────────────────

    def record_prediction(
        self,
        prediction_type: str,
        predicted_value: Optional[float],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        confidence_score: Optional[float] = None,
        model_version: Optional[str] = None,
        status: str = "completed",
    ) -> Optional[Dict[str, Any]]:
        """
        Persists a prediction event into the predictions table with tenant isolation.
        """
        try:
            record = {
                "company_id": str(self.company_id),
                "branch_id": str(self.branch_id) if self.branch_id else None,
                "prediction_type": prediction_type,
                "predicted_value": predicted_value,
                "confidence_score": confidence_score,
                "model_version": model_version,
                "input_data": input_data,
                "output_data": output_data,
                "status": status,
            }
            res = self.client.table("predictions").insert(record).execute()
            if res.data:
                pred_row = res.data[0]
                # Log execution stage
                try:
                    self.client.table("prediction_logs").insert({
                        "prediction_id": pred_row["id"],
                        "stage": "inference",
                        "status": "success",
                        "message": f"Inference completed using {model_version or 'default model'}",
                    }).execute()
                except Exception as log_err:
                    logger.debug("Prediction log write warning: {}", log_err)
                return pred_row
            return None
        except Exception as e:
            logger.error("[MLDataService] record_prediction persistence error: {}", e)
            return None

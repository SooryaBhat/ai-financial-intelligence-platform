"""
v1 API router — aggregates all module routers under /api/v1
"""
from fastapi import APIRouter

from app.api.v1 import (
    activity_logs,
    audit_logs,
    branches,
    categories,
    chat,
    companies,
    customers,
    expenses,
    integrations,
    inventory,
    invoices,
    ml_models,
    notifications,
    payments,
    plans,
    predictions,
    products,
    purchases,
    reports,
    roles,
    sales,
    settings,
    stock_movements,
    suppliers,
    users,
    warehouses,
)

api_router = APIRouter(prefix="/api/v1")

# Platform
api_router.include_router(companies.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(plans.router)
api_router.include_router(branches.router)

# Business
api_router.include_router(customers.router)
api_router.include_router(suppliers.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(warehouses.router)
api_router.include_router(inventory.router)
api_router.include_router(stock_movements.router)
api_router.include_router(sales.router)
api_router.include_router(purchases.router)
api_router.include_router(invoices.router)
api_router.include_router(payments.router)
api_router.include_router(expenses.router)

# AI
api_router.include_router(ml_models.router)
api_router.include_router(predictions.router)
api_router.include_router(chat.router)
api_router.include_router(reports.router)

# System
api_router.include_router(notifications.router)
api_router.include_router(audit_logs.router)
api_router.include_router(activity_logs.router)
api_router.include_router(settings.router)
api_router.include_router(integrations.router)

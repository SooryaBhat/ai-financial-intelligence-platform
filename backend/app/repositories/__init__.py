"""Repositories package."""
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.activity_logs import ActivityLogRepository
from app.repositories.base import BaseRepository
from app.repositories.branches import BranchRepository
from app.repositories.categories import CategoryRepository
from app.repositories.chat import ChatMessageRepository, ChatSessionRepository
from app.repositories.companies import CompanyRepository
from app.repositories.customers import CustomerRepository
from app.repositories.expenses import ExpenseRepository
from app.repositories.integrations import IntegrationRepository
from app.repositories.inventory import InventoryRepository, StockMovementRepository
from app.repositories.invoices import InvoiceRepository
from app.repositories.ml_models import MLModelRepository
from app.repositories.notifications import NotificationRepository
from app.repositories.payments import PaymentRepository
from app.repositories.plans import PlanRepository
from app.repositories.predictions import PredictionLogRepository, PredictionRepository
from app.repositories.products import ProductRepository
from app.repositories.purchases import PurchaseRepository
from app.repositories.reports import ReportRepository
from app.repositories.roles import RoleRepository
from app.repositories.sales import SaleRepository
from app.repositories.settings import SettingsRepository
from app.repositories.suppliers import SupplierRepository
from app.repositories.users import UserRepository
from app.repositories.warehouses import WarehouseRepository

__all__ = [
    "BaseRepository",
    "CompanyRepository", "UserRepository", "RoleRepository",
    "PlanRepository", "BranchRepository",
    "CustomerRepository", "SupplierRepository", "CategoryRepository",
    "ProductRepository", "WarehouseRepository",
    "InventoryRepository", "StockMovementRepository",
    "SaleRepository", "PurchaseRepository",
    "InvoiceRepository", "PaymentRepository", "ExpenseRepository",
    "MLModelRepository", "PredictionRepository", "PredictionLogRepository",
    "ChatSessionRepository", "ChatMessageRepository", "ReportRepository",
    "NotificationRepository", "AuditLogRepository", "ActivityLogRepository",
    "SettingsRepository", "IntegrationRepository",
]

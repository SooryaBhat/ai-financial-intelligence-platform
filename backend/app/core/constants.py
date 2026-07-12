"""
Application-wide constants and enumerations.
These mirror the CHECK constraints defined in the database migrations,
ensuring the Python layer stays in sync with the DB schema.
"""
from enum import Enum


# ── Platform Domain ───────────────────────────────────────────

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


# ── Business Domain ───────────────────────────────────────────

class CategoryType(str, Enum):
    PRODUCT = "product"
    EXPENSE = "expense"


class ProductType(str, Enum):
    PRODUCT = "product"
    SERVICE = "service"


class StockMovementType(str, Enum):
    RECEIPT = "receipt"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    RETURN = "return"


class StockReferenceType(str, Enum):
    SALE = "sale"
    PURCHASE = "purchase"
    MANUAL = "manual"


class SaleStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PurchaseStatus(str, Enum):
    DRAFT = "draft"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class InvoiceType(str, Enum):
    RECEIVABLE = "receivable"
    PAYABLE = "payable"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    CHEQUE = "cheque"
    OTHER = "other"


class ExpenseStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ── AI Domain ─────────────────────────────────────────────────

class ModelType(str, Enum):
    FORECASTING = "forecasting"
    ANOMALY_DETECTION = "anomaly_detection"
    RECOMMENDATION = "recommendation"
    CLASSIFICATION = "classification"


class PredictionType(str, Enum):
    REVENUE = "revenue"
    EXPENSE = "expense"
    CASH_FLOW = "cash_flow"
    INVENTORY = "inventory"
    PROFIT = "profit"
    FRAUD_ALERT = "fraud_alert"


class PredictionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class PredictionLogStage(str, Enum):
    PREPROCESSING = "preprocessing"
    INFERENCE = "inference"
    POSTPROCESSING = "postprocessing"


class PredictionLogStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ReportType(str, Enum):
    PROFIT_LOSS = "profit_loss"
    CASH_FLOW = "cash_flow"
    BALANCE_SHEET = "balance_sheet"
    INVENTORY = "inventory"
    AI_INSIGHT = "ai_insight"
    SALES_SUMMARY = "sales_summary"
    EXPENSE_SUMMARY = "expense_summary"


class ReportStatus(str, Enum):
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


# ── System Domain ─────────────────────────────────────────────

class NotificationType(str, Enum):
    ALERT = "alert"
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class IntegrationProvider(str, Enum):
    ODOO = "odoo"
    ERPNEXT = "erpnext"
    ZOHO = "zoho"
    QUICKBOOKS = "quickbooks"
    BANK_API = "bank_api"
    CSV = "csv"
    EXCEL = "excel"


class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class SyncFrequency(str, Enum):
    MANUAL = "manual"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


# ── Misc ──────────────────────────────────────────────────────

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_CURRENCY = "USD"

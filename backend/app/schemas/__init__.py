"""Schemas package — re-exports all public schema types."""
from app.schemas.activity_logs import ActivityLogCreate, ActivityLogResponse
from app.schemas.audit_logs import AuditLogCreate, AuditLogResponse
from app.schemas.auth import (
    AuthUserResponse,
    LoginRequest,
    OnboardRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
)
from app.schemas.branches import BranchCreate, BranchResponse, BranchUpdate
from app.schemas.categories import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
    SendMessageRequest,
)
from app.schemas.common import (
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
)
from app.schemas.companies import CompanyCreate, CompanyResponse, CompanyUpdate
from app.schemas.customers import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.expenses import (
    ExpenseApproveRequest,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
)
from app.schemas.integrations import (
    IntegrationCreate,
    IntegrationResponse,
    IntegrationUpdate,
)
from app.schemas.inventory import (
    AdjustInventoryRequest,
    InventoryResponse,
    InventoryUpdate,
    StockMovementCreate,
    StockMovementResponse,
)
from app.schemas.invoices import InvoiceCreate, InvoiceResponse, InvoiceUpdate
from app.schemas.ml_models import MLModelCreate, MLModelResponse, MLModelUpdate
from app.schemas.notifications import (
    MarkReadRequest,
    NotificationCreate,
    NotificationResponse,
)
from app.schemas.payments import PaymentCreate, PaymentResponse, PaymentUpdate
from app.schemas.plans import PlanResponse, SubscriptionCreate, SubscriptionResponse
from app.schemas.predictions import (
    PredictionCreate,
    PredictionLogResponse,
    PredictionResponse,
    PredictionUpdate,
)
from app.schemas.products import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.purchases import PurchaseCreate, PurchaseResponse, PurchaseUpdate
from app.schemas.reports import ReportCreate, ReportResponse, ReportUpdate
from app.schemas.roles import (
    AssignPermissionsRequest,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.schemas.sales import SaleCreate, SaleResponse, SaleUpdate
from app.schemas.settings import SettingResponse, SettingUpsert
from app.schemas.suppliers import SupplierCreate, SupplierResponse, SupplierUpdate
from app.schemas.users import (
    CompanyUserCreate,
    CompanyUserResponse,
    CompanyUserUpdate,
    InviteUserRequest,
    UserResponse,
    UserUpdate,
)
from app.schemas.warehouses import WarehouseCreate, WarehouseResponse, WarehouseUpdate

__all__ = [
    # Common
    "PaginatedResponse", "PaginationParams", "SuccessResponse", "MessageResponse",
    # Auth
    "SignupRequest", "LoginRequest", "TokenResponse", "OnboardRequest", "RefreshRequest", "AuthUserResponse",
    # Platform
    "CompanyCreate", "CompanyResponse", "CompanyUpdate",
    "UserResponse", "UserUpdate", "CompanyUserCreate", "CompanyUserResponse", "CompanyUserUpdate", "InviteUserRequest",
    "RoleCreate", "RoleResponse", "RoleUpdate", "PermissionResponse", "AssignPermissionsRequest",
    "PlanResponse", "SubscriptionCreate", "SubscriptionResponse",
    "BranchCreate", "BranchResponse", "BranchUpdate",
    # Business
    "CustomerCreate", "CustomerResponse", "CustomerUpdate",
    "SupplierCreate", "SupplierResponse", "SupplierUpdate",
    "CategoryCreate", "CategoryResponse", "CategoryUpdate",
    "ProductCreate", "ProductResponse", "ProductUpdate",
    "WarehouseCreate", "WarehouseResponse", "WarehouseUpdate",
    "InventoryResponse", "InventoryUpdate", "AdjustInventoryRequest",
    "StockMovementCreate", "StockMovementResponse",
    "SaleCreate", "SaleResponse", "SaleUpdate",
    "PurchaseCreate", "PurchaseResponse", "PurchaseUpdate",
    "InvoiceCreate", "InvoiceResponse", "InvoiceUpdate",
    "PaymentCreate", "PaymentResponse", "PaymentUpdate",
    "ExpenseCreate", "ExpenseResponse", "ExpenseUpdate", "ExpenseApproveRequest",
    # AI
    "MLModelCreate", "MLModelResponse", "MLModelUpdate",
    "PredictionCreate", "PredictionResponse", "PredictionUpdate", "PredictionLogResponse",
    "ChatSessionCreate", "ChatSessionResponse", "ChatSessionUpdate",
    "ChatMessageCreate", "ChatMessageResponse", "SendMessageRequest",
    "ReportCreate", "ReportResponse", "ReportUpdate",
    # System
    "NotificationCreate", "NotificationResponse", "MarkReadRequest",
    "AuditLogCreate", "AuditLogResponse",
    "ActivityLogCreate", "ActivityLogResponse",
    "SettingUpsert", "SettingResponse",
    "IntegrationCreate", "IntegrationResponse", "IntegrationUpdate",
]

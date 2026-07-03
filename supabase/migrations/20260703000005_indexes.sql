-- ============================================================
-- Migration 005: Indexes
-- AI Financial Intelligence Platform
-- ============================================================
-- Covers all domains. Ordered by table dependency.
-- Strategy:
--   - All company_id columns indexed (tenant isolation queries)
--   - Composite indexes on (company_id, status) for filtered lists
--   - Composite indexes on (company_id, created_at DESC) for time-series
--   - Partial indexes with WHERE deleted_at IS NULL for soft-delete tables
--   - Unread notification index for fast badge counts
-- ============================================================


-- ────────────────────────────────────────────
-- PLATFORM DOMAIN
-- ────────────────────────────────────────────

CREATE INDEX idx_companies_plan_id
  ON companies (plan_id);

CREATE INDEX idx_companies_is_active
  ON companies (is_active)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_subscriptions_company_id
  ON subscriptions (company_id);

CREATE INDEX idx_subscriptions_status
  ON subscriptions (company_id, status);

CREATE INDEX idx_branches_company_id
  ON branches (company_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_roles_company_id
  ON roles (company_id);

CREATE INDEX idx_company_users_company_id
  ON company_users (company_id);

CREATE INDEX idx_company_users_user_id
  ON company_users (user_id);

CREATE INDEX idx_company_users_role_id
  ON company_users (role_id);

CREATE INDEX idx_role_permissions_permission_id
  ON role_permissions (permission_id);


-- ────────────────────────────────────────────
-- BUSINESS DOMAIN
-- ────────────────────────────────────────────

-- Customers
CREATE INDEX idx_customers_company_id
  ON customers (company_id)
  WHERE deleted_at IS NULL;

-- Suppliers
CREATE INDEX idx_suppliers_company_id
  ON suppliers (company_id)
  WHERE deleted_at IS NULL;

-- Categories
CREATE INDEX idx_categories_company_type
  ON categories (company_id, type)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_categories_parent_id
  ON categories (parent_id);

-- Products
CREATE INDEX idx_products_company_id
  ON products (company_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_products_category_id
  ON products (category_id);

CREATE INDEX idx_products_type
  ON products (company_id, type)
  WHERE deleted_at IS NULL;

-- Warehouses
CREATE INDEX idx_warehouses_company_id
  ON warehouses (company_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_warehouses_branch_id
  ON warehouses (branch_id);

-- Inventory
CREATE INDEX idx_inventory_company_id
  ON inventory (company_id);

CREATE INDEX idx_inventory_product_warehouse
  ON inventory (product_id, warehouse_id);

CREATE INDEX idx_inventory_low_stock
  ON inventory (company_id, product_id)
  WHERE quantity <= reorder_level;

-- Stock Movements
CREATE INDEX idx_stock_movements_company_id
  ON stock_movements (company_id);

CREATE INDEX idx_stock_movements_product_id
  ON stock_movements (product_id);

CREATE INDEX idx_stock_movements_warehouse_id
  ON stock_movements (warehouse_id);

CREATE INDEX idx_stock_movements_reference
  ON stock_movements (reference_type, reference_id);

CREATE INDEX idx_stock_movements_created_at
  ON stock_movements (company_id, created_at DESC);

-- Sales
CREATE INDEX idx_sales_company_id
  ON sales (company_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_sales_customer_id
  ON sales (customer_id);

CREATE INDEX idx_sales_status
  ON sales (company_id, status)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_sales_sale_date
  ON sales (company_id, sale_date DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_sales_branch_id
  ON sales (branch_id);

-- Sale Items
CREATE INDEX idx_sale_items_sale_id
  ON sale_items (sale_id);

CREATE INDEX idx_sale_items_product_id
  ON sale_items (product_id);

-- Purchases
CREATE INDEX idx_purchases_company_id
  ON purchases (company_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_purchases_supplier_id
  ON purchases (supplier_id);

CREATE INDEX idx_purchases_status
  ON purchases (company_id, status)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_purchases_purchase_date
  ON purchases (company_id, purchase_date DESC)
  WHERE deleted_at IS NULL;

-- Purchase Items
CREATE INDEX idx_purchase_items_purchase_id
  ON purchase_items (purchase_id);

CREATE INDEX idx_purchase_items_product_id
  ON purchase_items (product_id);

-- Invoices
CREATE INDEX idx_invoices_company_id
  ON invoices (company_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_invoices_customer_id
  ON invoices (customer_id);

CREATE INDEX idx_invoices_supplier_id
  ON invoices (supplier_id);

CREATE INDEX idx_invoices_sale_id
  ON invoices (sale_id);

CREATE INDEX idx_invoices_purchase_id
  ON invoices (purchase_id);

CREATE INDEX idx_invoices_status
  ON invoices (company_id, status)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_invoices_type_status
  ON invoices (company_id, invoice_type, status)
  WHERE deleted_at IS NULL;

-- Composite: overdue detection query (type + status + due_date)
CREATE INDEX idx_invoices_due_date
  ON invoices (company_id, invoice_type, due_date)
  WHERE status NOT IN ('paid','cancelled') AND deleted_at IS NULL;

-- Payments
CREATE INDEX idx_payments_company_id
  ON payments (company_id);

CREATE INDEX idx_payments_invoice_id
  ON payments (invoice_id);

CREATE INDEX idx_payments_payment_date
  ON payments (company_id, payment_date DESC);

-- Expenses
CREATE INDEX idx_expenses_company_id
  ON expenses (company_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_expenses_category_id
  ON expenses (category_id);

CREATE INDEX idx_expenses_status
  ON expenses (company_id, status)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_expenses_expense_date
  ON expenses (company_id, expense_date DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_expenses_branch_id
  ON expenses (branch_id);


-- ────────────────────────────────────────────
-- AI DOMAIN
-- ────────────────────────────────────────────

CREATE INDEX idx_ml_models_company_id
  ON ml_models (company_id);

CREATE INDEX idx_ml_models_type_active
  ON ml_models (model_type, is_active);

CREATE INDEX idx_predictions_company_id
  ON predictions (company_id);

CREATE INDEX idx_predictions_type_period
  ON predictions (company_id, prediction_type, period_start);

CREATE INDEX idx_predictions_ml_model_id
  ON predictions (ml_model_id);

CREATE INDEX idx_predictions_status
  ON predictions (company_id, status);

CREATE INDEX idx_prediction_logs_prediction_id
  ON prediction_logs (prediction_id);

CREATE INDEX idx_chat_sessions_company_user
  ON chat_sessions (company_id, user_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_chat_messages_session_id
  ON chat_messages (session_id);

-- Ordered for conversation rendering
CREATE INDEX idx_chat_messages_session_created
  ON chat_messages (session_id, created_at ASC);

CREATE INDEX idx_reports_company_id
  ON reports (company_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_reports_type_period
  ON reports (company_id, report_type, period_start DESC)
  WHERE deleted_at IS NULL;


-- ────────────────────────────────────────────
-- SYSTEM DOMAIN
-- ────────────────────────────────────────────

CREATE INDEX idx_notifications_user_company
  ON notifications (user_id, company_id);

-- Fast unread badge count
CREATE INDEX idx_notifications_unread
  ON notifications (user_id, is_read)
  WHERE is_read = false;

CREATE INDEX idx_audit_logs_company_id
  ON audit_logs (company_id);

CREATE INDEX idx_audit_logs_resource
  ON audit_logs (resource_type, resource_id);

CREATE INDEX idx_audit_logs_created_at
  ON audit_logs (company_id, created_at DESC);

CREATE INDEX idx_audit_logs_user_id
  ON audit_logs (user_id);

CREATE INDEX idx_activity_logs_company_id
  ON activity_logs (company_id);

CREATE INDEX idx_activity_logs_user_id
  ON activity_logs (user_id);

CREATE INDEX idx_activity_logs_created_at
  ON activity_logs (company_id, created_at DESC);

CREATE INDEX idx_settings_company_id
  ON settings (company_id);

CREATE INDEX idx_integrations_company_id
  ON integrations (company_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_integrations_provider
  ON integrations (company_id, provider)
  WHERE deleted_at IS NULL;

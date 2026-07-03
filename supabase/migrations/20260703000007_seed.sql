-- ============================================================
-- Migration 007: Seed Data
-- AI Financial Intelligence Platform
-- ============================================================
-- Seeds: plans, system roles, permissions, role-permission mappings
-- This data is required for the platform to function correctly
-- on first launch.
-- ============================================================


-- ──────────────────────────────────────────────────────────────
-- PLANS
-- Four tiers: Free, Starter, Pro, Enterprise
-- features JSONB controls which platform capabilities each tier unlocks.
-- ──────────────────────────────────────────────────────────────
INSERT INTO plans (id, name, description, price_monthly, price_yearly, max_users, max_branches, features, is_active)
VALUES
  (
    'a1000000-0000-0000-0000-000000000001',
    'Free',
    'Get started with core business management features at no cost.',
    0.00, 0.00, 3, 1,
    '{
      "sales": true,
      "purchases": true,
      "inventory": true,
      "invoicing": true,
      "expenses": true,
      "reports_basic": true,
      "ai_chat": false,
      "ml_forecasting": false,
      "anomaly_detection": false,
      "integrations": false,
      "multi_branch": false,
      "api_access": false,
      "priority_support": false
    }',
    true
  ),
  (
    'a1000000-0000-0000-0000-000000000002',
    'Starter',
    'For growing small businesses that need AI-powered insights.',
    29.00, 290.00, 10, 3,
    '{
      "sales": true,
      "purchases": true,
      "inventory": true,
      "invoicing": true,
      "expenses": true,
      "reports_basic": true,
      "reports_advanced": true,
      "ai_chat": true,
      "ml_forecasting": false,
      "anomaly_detection": false,
      "integrations": false,
      "multi_branch": true,
      "api_access": false,
      "priority_support": false
    }',
    true
  ),
  (
    'a1000000-0000-0000-0000-000000000003',
    'Pro',
    'Full AI Financial Intelligence with ML forecasting and ERP integrations.',
    79.00, 790.00, 25, 10,
    '{
      "sales": true,
      "purchases": true,
      "inventory": true,
      "invoicing": true,
      "expenses": true,
      "reports_basic": true,
      "reports_advanced": true,
      "ai_chat": true,
      "ml_forecasting": true,
      "anomaly_detection": true,
      "integrations": true,
      "multi_branch": true,
      "api_access": true,
      "priority_support": false
    }',
    true
  ),
  (
    'a1000000-0000-0000-0000-000000000004',
    'Enterprise',
    'Unlimited scale, custom integrations, and dedicated priority support.',
    199.00, 1990.00, NULL, NULL,
    '{
      "sales": true,
      "purchases": true,
      "inventory": true,
      "invoicing": true,
      "expenses": true,
      "reports_basic": true,
      "reports_advanced": true,
      "ai_chat": true,
      "ml_forecasting": true,
      "anomaly_detection": true,
      "integrations": true,
      "custom_integrations": true,
      "multi_branch": true,
      "api_access": true,
      "priority_support": true,
      "dedicated_support": true,
      "sla_guarantee": true
    }',
    true
  );


-- ──────────────────────────────────────────────────────────────
-- SYSTEM ROLES (company_id = NULL = platform-level)
-- These are built-in roles available to every company.
-- is_system = true prevents accidental deletion.
-- ──────────────────────────────────────────────────────────────
INSERT INTO roles (id, company_id, name, description, is_system)
VALUES
  ('b1000000-0000-0000-0000-000000000001', NULL, 'owner',       'Company owner with unrestricted access to all features and settings.',       true),
  ('b1000000-0000-0000-0000-000000000002', NULL, 'admin',       'Administrator with full access to all company data and user management.',    true),
  ('b1000000-0000-0000-0000-000000000003', NULL, 'manager',     'Manager with read/write access to operational data. Cannot manage users.',   true),
  ('b1000000-0000-0000-0000-000000000004', NULL, 'accountant',  'Access to all financial data, invoices, payments, and reports.',             true),
  ('b1000000-0000-0000-0000-000000000005', NULL, 'sales_rep',   'Create and manage sales, customers, and quotations.',                        true),
  ('b1000000-0000-0000-0000-000000000006', NULL, 'viewer',      'Read-only access to all company data. Cannot create or modify records.',     true);


-- ──────────────────────────────────────────────────────────────
-- PERMISSIONS
-- Granular resource + action pairs covering all platform features.
-- ──────────────────────────────────────────────────────────────
INSERT INTO permissions (resource, action, description)
VALUES
  -- Company & Users
  ('companies',     'read',     'View company profile and settings'),
  ('companies',     'update',   'Update company profile and settings'),
  ('users',         'read',     'View users and their roles'),
  ('users',         'create',   'Invite new users to the company'),
  ('users',         'update',   'Update user roles and access'),
  ('users',         'delete',   'Remove users from the company'),
  -- Customers
  ('customers',     'read',     'View customer records'),
  ('customers',     'create',   'Create new customers'),
  ('customers',     'update',   'Update customer information'),
  ('customers',     'delete',   'Soft-delete customer records'),
  -- Suppliers
  ('suppliers',     'read',     'View supplier records'),
  ('suppliers',     'create',   'Create new suppliers'),
  ('suppliers',     'update',   'Update supplier information'),
  ('suppliers',     'delete',   'Soft-delete supplier records'),
  -- Products & Categories
  ('products',      'read',     'View products and services'),
  ('products',      'create',   'Create new products'),
  ('products',      'update',   'Update product information and pricing'),
  ('products',      'delete',   'Soft-delete products'),
  ('categories',    'read',     'View categories'),
  ('categories',    'create',   'Create categories'),
  ('categories',    'update',   'Update categories'),
  ('categories',    'delete',   'Delete categories'),
  -- Inventory & Warehouses
  ('inventory',     'read',     'View current stock levels'),
  ('inventory',     'update',   'Adjust stock levels manually'),
  ('warehouses',    'read',     'View warehouse locations'),
  ('warehouses',    'create',   'Add warehouse locations'),
  ('warehouses',    'update',   'Update warehouse details'),
  ('warehouses',    'delete',   'Remove warehouse locations'),
  -- Sales
  ('sales',         'read',     'View sales orders'),
  ('sales',         'create',   'Create new sales orders'),
  ('sales',         'update',   'Update and confirm sales orders'),
  ('sales',         'delete',   'Cancel and soft-delete sales'),
  -- Purchases
  ('purchases',     'read',     'View purchase orders'),
  ('purchases',     'create',   'Create new purchase orders'),
  ('purchases',     'update',   'Update and confirm purchase orders'),
  ('purchases',     'delete',   'Cancel and soft-delete purchases'),
  -- Invoices
  ('invoices',      'read',     'View AR and AP invoices'),
  ('invoices',      'create',   'Create and issue invoices'),
  ('invoices',      'update',   'Update invoice details and status'),
  ('invoices',      'delete',   'Void and soft-delete invoices'),
  -- Payments
  ('payments',      'read',     'View payment records'),
  ('payments',      'create',   'Record incoming and outgoing payments'),
  -- Expenses
  ('expenses',      'read',     'View expense records'),
  ('expenses',      'create',   'Submit new expense claims'),
  ('expenses',      'update',   'Update expense details'),
  ('expenses',      'delete',   'Delete expense records'),
  ('expenses',      'approve',  'Approve or reject expense claims'),
  -- Reports
  ('reports',       'read',     'View and download generated reports'),
  ('reports',       'create',   'Generate new reports'),
  -- AI Features
  ('ai_chat',       'use',      'Use the AI Financial Assistant'),
  ('ml_models',     'read',     'View ML model details and prediction history'),
  ('predictions',   'read',     'View forecasts and anomaly detection results'),
  -- Settings & Integrations
  ('settings',      'read',     'View company settings'),
  ('settings',      'update',   'Modify company settings'),
  ('integrations',  'read',     'View configured ERP integrations'),
  ('integrations',  'create',   'Connect new ERP or data source integrations'),
  ('integrations',  'update',   'Reconfigure existing integrations'),
  ('integrations',  'delete',   'Disconnect integrations'),
  -- Audit
  ('audit_logs',    'read',     'View the financial audit trail');


-- ──────────────────────────────────────────────────────────────
-- ROLE → PERMISSION MAPPINGS
-- Assigns permissions to each system role.
-- ──────────────────────────────────────────────────────────────

-- owner: all permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'b1000000-0000-0000-0000-000000000001', id FROM permissions;

-- admin: all permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'b1000000-0000-0000-0000-000000000002', id FROM permissions;

-- manager: operational access, no user management or settings
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'b1000000-0000-0000-0000-000000000003', id
FROM   permissions
WHERE  (resource, action) IN (
  ('companies',    'read'),
  ('customers',    'read'), ('customers',   'create'), ('customers',   'update'),
  ('suppliers',    'read'), ('suppliers',   'create'), ('suppliers',   'update'),
  ('products',     'read'), ('products',    'create'), ('products',    'update'),
  ('categories',   'read'), ('categories',  'create'), ('categories',  'update'),
  ('inventory',    'read'), ('inventory',   'update'),
  ('warehouses',   'read'),
  ('sales',        'read'), ('sales',       'create'), ('sales',       'update'),
  ('purchases',    'read'), ('purchases',   'create'), ('purchases',   'update'),
  ('invoices',     'read'), ('invoices',    'create'), ('invoices',    'update'),
  ('payments',     'read'), ('payments',    'create'),
  ('expenses',     'read'), ('expenses',    'create'), ('expenses',    'update'), ('expenses', 'approve'),
  ('reports',      'read'), ('reports',     'create'),
  ('ai_chat',      'use'),
  ('predictions',  'read'),
  ('audit_logs',   'read')
);

-- accountant: financial data focus
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'b1000000-0000-0000-0000-000000000004', id
FROM   permissions
WHERE  (resource, action) IN (
  ('companies',    'read'),
  ('customers',    'read'),
  ('suppliers',    'read'),
  ('products',     'read'),
  ('inventory',    'read'),
  ('sales',        'read'),
  ('purchases',    'read'),
  ('invoices',     'read'), ('invoices',   'create'), ('invoices',  'update'),
  ('payments',     'read'), ('payments',   'create'),
  ('expenses',     'read'), ('expenses',   'approve'),
  ('reports',      'read'), ('reports',    'create'),
  ('ai_chat',      'use'),
  ('predictions',  'read'),
  ('audit_logs',   'read')
);

-- sales_rep: customer-facing and sales operations only
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'b1000000-0000-0000-0000-000000000005', id
FROM   permissions
WHERE  (resource, action) IN (
  ('customers',    'read'), ('customers',  'create'), ('customers',  'update'),
  ('products',     'read'),
  ('inventory',    'read'),
  ('sales',        'read'), ('sales',      'create'), ('sales',      'update'),
  ('invoices',     'read'), ('invoices',   'create'),
  ('payments',     'read'),
  ('expenses',     'read'), ('expenses',   'create'),
  ('reports',      'read'),
  ('ai_chat',      'use')
);

-- viewer: read-only access everywhere
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'b1000000-0000-0000-0000-000000000006', id
FROM   permissions
WHERE  action = 'read'
   OR  (resource = 'ai_chat' AND action = 'use');

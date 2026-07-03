-- ============================================================
-- Migration 001: Platform Domain
-- AI Financial Intelligence Platform
-- ============================================================
-- Tables: plans, companies, subscriptions, branches, roles,
--         permissions, role_permissions, users, company_users
-- ============================================================

-- Enable UUID generation
-- uuid-ossp extension not needed; gen_random_uuid() is built-in to PostgreSQL 13+

-- ──────────────────────────────────────────────────────────────
-- SHARED: updated_at auto-update trigger function
-- Reused by all tables that carry an updated_at column.
-- ──────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ──────────────────────────────────────────────────────────────
-- TABLE: plans
-- Subscription plans offered on the platform (Free/Starter/Pro/Enterprise).
-- Decoupled from companies so plans can change without modifying companies.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE plans (
  id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT          NOT NULL,
  description     TEXT,
  price_monthly   NUMERIC(10,2) NOT NULL DEFAULT 0,
  price_yearly    NUMERIC(10,2) NOT NULL DEFAULT 0,
  max_users       INT,                                   -- NULL = unlimited
  max_branches    INT,                                   -- NULL = unlimited
  features        JSONB         NOT NULL DEFAULT '{}',   -- Feature flag map per plan
  is_active       BOOLEAN       NOT NULL DEFAULT true,
  created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_plans_updated_at
  BEFORE UPDATE ON plans
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: companies
-- Root of multi-tenancy. Every business entity in the system.
-- All tenant tables reference company_id for strict isolation.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE companies (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  name                TEXT        NOT NULL,
  slug                TEXT        NOT NULL UNIQUE,         -- URL-safe identifier
  industry            TEXT,
  country             TEXT,
  currency            CHAR(3)     NOT NULL DEFAULT 'USD',  -- ISO 4217 default currency
  timezone            TEXT        NOT NULL DEFAULT 'UTC',
  logo_url            TEXT,
  plan_id             UUID        REFERENCES plans(id) ON DELETE SET NULL,
  subscription_status TEXT        NOT NULL DEFAULT 'trialing'
                        CHECK (subscription_status IN ('active','trialing','cancelled','past_due')),
  trial_ends_at       TIMESTAMPTZ,
  is_active           BOOLEAN     NOT NULL DEFAULT true,
  deleted_at          TIMESTAMPTZ,                         -- Soft delete
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_companies_updated_at
  BEFORE UPDATE ON companies
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: subscriptions
-- Full subscription lifecycle / billing history per company.
-- Separate from companies table to preserve a complete audit trail
-- of plan changes and billing events.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE subscriptions (
  id                       UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id               UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  plan_id                  UUID          NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
  status                   TEXT          NOT NULL DEFAULT 'trialing'
                             CHECK (status IN ('active','cancelled','trialing','past_due')),
  started_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  ended_at                 TIMESTAMPTZ,                        -- NULL if currently active
  billing_cycle            TEXT          NOT NULL DEFAULT 'monthly'
                             CHECK (billing_cycle IN ('monthly','yearly')),
  amount                   NUMERIC(10,2) NOT NULL,             -- Amount captured at subscription time
  external_subscription_id TEXT,                               -- Stripe / payment gateway reference
  created_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_subscriptions_updated_at
  BEFORE UPDATE ON subscriptions
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: branches
-- Organisational sub-units within a company (offices, store locations).
-- Scaffolded now as required by spec. Transactional tables carry a
-- nullable branch_id to support single-location companies today
-- and multi-location companies in the future.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE branches (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name        TEXT        NOT NULL,
  address     TEXT,
  city        TEXT,
  country     TEXT,
  phone       TEXT,
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  deleted_at  TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_branches_updated_at
  BEFORE UPDATE ON branches
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: roles
-- Named roles within a company (Admin, Manager, Accountant, Viewer).
-- company_id NULL = platform-level system role shared by all companies.
-- is_system = true means the role is built-in and cannot be deleted.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE roles (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  UUID        REFERENCES companies(id) ON DELETE CASCADE, -- NULL = system-level role
  name        TEXT        NOT NULL,
  description TEXT,
  is_system   BOOLEAN     NOT NULL DEFAULT false,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_roles_updated_at
  BEFORE UPDATE ON roles
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: permissions
-- Granular permission definitions. Decoupled from roles so they
-- can be freely composed into different role configurations.
-- resource = the entity (invoices, reports, ai_chat)
-- action   = the operation (create, read, update, delete, approve)
-- ──────────────────────────────────────────────────────────────
CREATE TABLE permissions (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  resource    TEXT        NOT NULL,
  action      TEXT        NOT NULL,
  description TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (resource, action)
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: role_permissions
-- Junction table: many-to-many between roles and permissions.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE role_permissions (
  role_id       UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: users
-- App-level profile extension of Supabase auth.users (1:1).
-- id = auth.users.id exactly. Supabase Auth handles JWT / sessions.
-- This table stores display data, preferences, and soft-delete state.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE users (
  id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email       TEXT        NOT NULL UNIQUE,
  full_name   TEXT,
  avatar_url  TEXT,
  phone       TEXT,
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  deleted_at  TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: company_users
-- Associates users with companies and assigns a role.
-- A single user can belong to multiple companies.
-- branch_id NULL = company-wide access (not restricted to one branch).
-- ──────────────────────────────────────────────────────────────
CREATE TABLE company_users (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id     UUID        NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
  branch_id   UUID        REFERENCES branches(id) ON DELETE SET NULL, -- NULL = all branches
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  invited_at  TIMESTAMPTZ,
  joined_at   TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (company_id, user_id)
);

CREATE TRIGGER trg_company_users_updated_at
  BEFORE UPDATE ON company_users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

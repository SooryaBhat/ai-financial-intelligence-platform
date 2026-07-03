-- ============================================================
-- Migration 004: System Domain
-- AI Financial Intelligence Platform
-- ============================================================
-- Tables: notifications, audit_logs, activity_logs,
--         settings, integrations
-- Depends on: 001_platform_domain
-- ============================================================


-- ──────────────────────────────────────────────────────────────
-- TABLE: notifications
-- In-app notifications delivered to users.
-- action_url provides a deep link to the relevant page.
-- Append-only from the system side (is_read is the only update).
-- ──────────────────────────────────────────────────────────────
CREATE TABLE notifications (
  id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type        TEXT        NOT NULL CHECK (type IN ('alert','info','warning','success')),
  title       TEXT        NOT NULL,
  message     TEXT,
  is_read     BOOLEAN     NOT NULL DEFAULT false,
  action_url  TEXT,                                   -- Deep link to relevant page
  metadata    JSONB       NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: audit_logs
-- Immutable record of every state-changing action on financial data.
-- Critical for compliance, forensic accounting, and fraud detection.
-- old_values / new_values capture the full before/after state as JSONB.
-- Never updated or deleted — append-only by design.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE audit_logs (
  id            UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id    UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  user_id       UUID        REFERENCES users(id) ON DELETE SET NULL,
  action        TEXT        NOT NULL CHECK (action IN ('CREATE','UPDATE','DELETE')),
  resource_type TEXT        NOT NULL,                 -- e.g. 'invoice', 'payment', 'sale'
  resource_id   UUID,                                 -- The affected record's UUID
  old_values    JSONB,                                -- State before the change
  new_values    JSONB,                                -- State after the change
  ip_address    TEXT,
  user_agent    TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: activity_logs
-- Lightweight log of read-access and navigation events
-- (logins, page views, report views, exports).
-- Kept separate from audit_logs to avoid polluting the critical
-- financial audit trail with non-mutating events.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE activity_logs (
  id            UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id    UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  user_id       UUID        REFERENCES users(id) ON DELETE SET NULL,
  action        TEXT        NOT NULL,                 -- e.g. 'login', 'view', 'export', 'download'
  resource_type TEXT,
  resource_id   UUID,
  metadata      JSONB       NOT NULL DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: settings
-- Key-value configuration per company.
-- JSONB value field avoids schema changes for new setting types.
-- Examples: fiscal_year_start, default_tax_rate, invoice_prefix,
--           low_stock_alert_enabled, ai_features_enabled.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE settings (
  id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  key         TEXT        NOT NULL,
  value       JSONB       NOT NULL,
  description TEXT,
  updated_by  UUID        REFERENCES users(id) ON DELETE SET NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (company_id, key)
);

CREATE TRIGGER trg_settings_updated_at
  BEFORE UPDATE ON settings
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: integrations
-- Configuration of external ERP / data source connections per company.
-- config stores connection parameters — must be encrypted at the
-- application layer before storage (never store raw credentials).
-- Supports: Odoo, ERPNext, Zoho Books, QuickBooks, Bank APIs, CSV, Excel.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE integrations (
  id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id      UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  provider        TEXT        NOT NULL
                    CHECK (provider IN ('odoo','erpnext','zoho','quickbooks','bank_api','csv','excel')),
  name            TEXT        NOT NULL,               -- e.g. 'Main Odoo Instance', 'HDFC Bank Feed'
  status          TEXT        NOT NULL DEFAULT 'inactive'
                    CHECK (status IN ('active','inactive','error')),
  config          JSONB       NOT NULL DEFAULT '{}',  -- Encrypted connection params
  last_synced_at  TIMESTAMPTZ,
  sync_frequency  TEXT        NOT NULL DEFAULT 'manual'
                    CHECK (sync_frequency IN ('manual','hourly','daily','weekly')),
  error_message   TEXT,                               -- Last sync error details
  created_by      UUID        REFERENCES users(id) ON DELETE SET NULL,
  deleted_at      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (company_id, provider, name)
);

CREATE TRIGGER trg_integrations_updated_at
  BEFORE UPDATE ON integrations
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

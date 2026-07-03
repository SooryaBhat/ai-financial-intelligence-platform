-- ============================================================
-- Migration 006: Row Level Security (RLS) Policies
-- AI Financial Intelligence Platform
-- ============================================================
-- Enforces multi-tenant data isolation at the database layer.
-- This is Supabase best practice: isolation is guaranteed by
-- Postgres itself, not just the application layer.
--
-- Design:
--   - A helper function get_user_company_ids() returns the set
--     of company_ids the current auth.uid() belongs to.
--   - Every tenant table gets a policy using this function.
--   - The service_role key bypasses RLS (for server-side ops).
-- ============================================================


-- ──────────────────────────────────────────────────────────────
-- HELPER FUNCTION: get_user_company_ids()
-- Returns all company_ids the currently authenticated user
-- belongs to (active memberships only).
-- SECURITY DEFINER: runs with function owner privileges so it
-- can read company_users without circular RLS dependency.
-- STABLE: safe to cache within a single query.
-- ──────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION get_user_company_ids()
RETURNS SETOF UUID
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT company_id
  FROM   company_users
  WHERE  user_id   = auth.uid()
    AND  is_active = true;
$$;


-- ──────────────────────────────────────────────────────────────
-- ENABLE RLS on all tenant tables
-- ──────────────────────────────────────────────────────────────
ALTER TABLE companies         ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE branches          ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles             ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_users     ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers         ENABLE ROW LEVEL SECURITY;
ALTER TABLE suppliers         ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories        ENABLE ROW LEVEL SECURITY;
ALTER TABLE products          ENABLE ROW LEVEL SECURITY;
ALTER TABLE warehouses        ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory         ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_movements   ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales             ENABLE ROW LEVEL SECURITY;
ALTER TABLE sale_items        ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases         ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_items    ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices          ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments          ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses          ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_models         ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_logs   ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages     ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports           ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications     ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs        ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs     ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings          ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations      ENABLE ROW LEVEL SECURITY;


-- ──────────────────────────────────────────────────────────────
-- PLATFORM DOMAIN POLICIES
-- ──────────────────────────────────────────────────────────────

-- plans: readable by all authenticated users (public catalog)
CREATE POLICY "plans_read_all"
  ON plans FOR SELECT
  USING (auth.uid() IS NOT NULL);

-- companies: user sees only their own companies
CREATE POLICY "companies_company_isolation"
  ON companies FOR ALL
  USING (id IN (SELECT get_user_company_ids()));

-- subscriptions
CREATE POLICY "subscriptions_company_isolation"
  ON subscriptions FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

-- branches
CREATE POLICY "branches_company_isolation"
  ON branches FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

-- roles: company-scoped roles + platform system roles (company_id IS NULL)
CREATE POLICY "roles_company_isolation"
  ON roles FOR ALL
  USING (
    company_id IN (SELECT get_user_company_ids())
    OR company_id IS NULL
  );

-- permissions: readable by all authenticated users (needed for RBAC checks)
CREATE POLICY "permissions_read_all"
  ON permissions FOR SELECT
  USING (auth.uid() IS NOT NULL);

-- company_users: user sees memberships within their companies
CREATE POLICY "company_users_company_isolation"
  ON company_users FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

-- users: users can read profiles of other users in their companies
CREATE POLICY "users_read_own_company_members"
  ON users FOR SELECT
  USING (
    id = auth.uid()
    OR id IN (
      SELECT cu.user_id
      FROM   company_users cu
      WHERE  cu.company_id IN (SELECT get_user_company_ids())
    )
  );

-- users can update only their own profile
CREATE POLICY "users_update_own_profile"
  ON users FOR UPDATE
  USING (id = auth.uid());


-- ──────────────────────────────────────────────────────────────
-- BUSINESS DOMAIN POLICIES
-- ──────────────────────────────────────────────────────────────

CREATE POLICY "customers_company_isolation"
  ON customers FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "suppliers_company_isolation"
  ON suppliers FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "categories_company_isolation"
  ON categories FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "products_company_isolation"
  ON products FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "warehouses_company_isolation"
  ON warehouses FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "inventory_company_isolation"
  ON inventory FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "stock_movements_company_isolation"
  ON stock_movements FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "sales_company_isolation"
  ON sales FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

-- sale_items: isolated via parent sale's company_id
CREATE POLICY "sale_items_company_isolation"
  ON sale_items FOR ALL
  USING (
    sale_id IN (
      SELECT id FROM sales
      WHERE  company_id IN (SELECT get_user_company_ids())
    )
  );

CREATE POLICY "purchases_company_isolation"
  ON purchases FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

-- purchase_items: isolated via parent purchase's company_id
CREATE POLICY "purchase_items_company_isolation"
  ON purchase_items FOR ALL
  USING (
    purchase_id IN (
      SELECT id FROM purchases
      WHERE  company_id IN (SELECT get_user_company_ids())
    )
  );

CREATE POLICY "invoices_company_isolation"
  ON invoices FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "payments_company_isolation"
  ON payments FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "expenses_company_isolation"
  ON expenses FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));


-- ──────────────────────────────────────────────────────────────
-- AI DOMAIN POLICIES
-- ──────────────────────────────────────────────────────────────

-- ml_models: company-scoped + platform-wide shared models (company_id IS NULL)
CREATE POLICY "ml_models_company_isolation"
  ON ml_models FOR ALL
  USING (
    company_id IN (SELECT get_user_company_ids())
    OR company_id IS NULL
  );

CREATE POLICY "predictions_company_isolation"
  ON predictions FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

-- prediction_logs: isolated via parent prediction's company_id
CREATE POLICY "prediction_logs_company_isolation"
  ON prediction_logs FOR ALL
  USING (
    prediction_id IN (
      SELECT id FROM predictions
      WHERE  company_id IN (SELECT get_user_company_ids())
    )
  );

CREATE POLICY "chat_sessions_company_isolation"
  ON chat_sessions FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

-- chat_messages: isolated via parent session's company_id
CREATE POLICY "chat_messages_company_isolation"
  ON chat_messages FOR ALL
  USING (
    session_id IN (
      SELECT id FROM chat_sessions
      WHERE  company_id IN (SELECT get_user_company_ids())
    )
  );

CREATE POLICY "reports_company_isolation"
  ON reports FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));


-- ──────────────────────────────────────────────────────────────
-- SYSTEM DOMAIN POLICIES
-- ──────────────────────────────────────────────────────────────

-- notifications: company isolation + user can only see their own
CREATE POLICY "notifications_user_isolation"
  ON notifications FOR ALL
  USING (
    company_id IN (SELECT get_user_company_ids())
    AND user_id = auth.uid()
  );

-- audit_logs: readable by all company members; only system writes
CREATE POLICY "audit_logs_company_isolation"
  ON audit_logs FOR SELECT
  USING (company_id IN (SELECT get_user_company_ids()));

-- activity_logs: readable by all company members; only system writes
CREATE POLICY "activity_logs_company_isolation"
  ON activity_logs FOR SELECT
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "settings_company_isolation"
  ON settings FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

CREATE POLICY "integrations_company_isolation"
  ON integrations FOR ALL
  USING (company_id IN (SELECT get_user_company_ids()));

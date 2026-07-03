-- ============================================================
-- Migration 002: Business Domain
-- AI Financial Intelligence Platform
-- ============================================================
-- Tables: customers, suppliers, categories, products,
--         warehouses, inventory, stock_movements,
--         sales, sale_items, purchases, purchase_items,
--         invoices, payments, expenses
-- Depends on: 001_platform_domain
-- ============================================================


-- ──────────────────────────────────────────────────────────────
-- TABLE: customers
-- Entities that buy from the company (B2B or B2C).
-- Kept separate from suppliers: different fields, different
-- business logic (Accounts Receivable vs Accounts Payable).
-- ──────────────────────────────────────────────────────────────
CREATE TABLE customers (
  id            UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id    UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name          TEXT          NOT NULL,
  email         TEXT,
  phone         TEXT,
  address       TEXT,
  city          TEXT,
  country       TEXT,
  tax_number    TEXT,                          -- VAT / GST / TIN
  credit_limit  NUMERIC(15,2) NOT NULL DEFAULT 0,
  currency      CHAR(3)       NOT NULL DEFAULT 'USD',
  notes         TEXT,
  deleted_at    TIMESTAMPTZ,
  created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_customers_updated_at
  BEFORE UPDATE ON customers
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: suppliers
-- Entities from which the company purchases goods/services.
-- Separate from customers by design: AP vs AR logic diverges
-- significantly as the platform grows.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE suppliers (
  id                 UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id         UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name               TEXT        NOT NULL,
  email              TEXT,
  phone              TEXT,
  address            TEXT,
  city               TEXT,
  country            TEXT,
  tax_number         TEXT,
  payment_terms_days INT         NOT NULL DEFAULT 30,  -- Net payment days
  currency           CHAR(3)     NOT NULL DEFAULT 'USD',
  notes              TEXT,
  deleted_at         TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_suppliers_updated_at
  BEFORE UPDATE ON suppliers
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: categories
-- Unified category table for BOTH products and expenses.
-- The type column discriminates between them, avoiding two
-- near-identical tables. Supports subcategories via parent_id.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE categories (
  id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name        TEXT        NOT NULL,
  type        TEXT        NOT NULL CHECK (type IN ('product','expense')),
  parent_id   UUID        REFERENCES categories(id) ON DELETE SET NULL,  -- Subcategories
  description TEXT,
  deleted_at  TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (company_id, name, type)
);

CREATE TRIGGER trg_categories_updated_at
  BEFORE UPDATE ON categories
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: products
-- Products and services sold or purchased by the company.
-- type = 'service' means no inventory tracking is applied.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE products (
  id            UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id    UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  category_id   UUID          REFERENCES categories(id) ON DELETE SET NULL,
  name          TEXT          NOT NULL,
  sku           TEXT,                                -- Stock Keeping Unit
  description   TEXT,
  unit          TEXT,                                -- e.g. 'kg', 'pcs', 'hr', 'box'
  cost_price    NUMERIC(15,4) NOT NULL DEFAULT 0,
  selling_price NUMERIC(15,4) NOT NULL DEFAULT 0,
  tax_rate      NUMERIC(5,2)  NOT NULL DEFAULT 0,    -- Percentage
  type          TEXT          NOT NULL DEFAULT 'product'
                  CHECK (type IN ('product','service')),
  is_active     BOOLEAN       NOT NULL DEFAULT true,
  deleted_at    TIMESTAMPTZ,
  created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Partial unique index: SKU must be unique per company, but only when set and not deleted
CREATE UNIQUE INDEX uidx_products_sku ON products (company_id, sku)
  WHERE sku IS NOT NULL AND deleted_at IS NULL;

CREATE TRIGGER trg_products_updated_at
  BEFORE UPDATE ON products
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: warehouses
-- Physical storage locations. Required for inventory management
-- and multi-branch stock tracking.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE warehouses (
  id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  branch_id   UUID        REFERENCES branches(id) ON DELETE SET NULL,  -- NULL if not branch-specific
  name        TEXT        NOT NULL,
  address     TEXT,
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  deleted_at  TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_warehouses_updated_at
  BEFORE UPDATE ON warehouses
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: inventory
-- Current stock level per product per warehouse.
-- One row per (product, warehouse) pair — the live stock balance.
-- quantity is updated by stock_movements (the source of truth).
-- ──────────────────────────────────────────────────────────────
CREATE TABLE inventory (
  id            UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id    UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  product_id    UUID          NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  warehouse_id  UUID          NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
  quantity      NUMERIC(15,4) NOT NULL DEFAULT 0,
  reorder_level NUMERIC(15,4) NOT NULL DEFAULT 0,    -- Alert threshold for low stock
  updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  UNIQUE (product_id, warehouse_id)
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: stock_movements
-- Immutable audit log of every inventory change.
-- This is the source of truth; inventory.quantity is derived from it.
-- quantity > 0 = stock IN, quantity < 0 = stock OUT.
-- No updated_at: stock movements are append-only, never modified.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE stock_movements (
  id             UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id     UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  product_id     UUID          NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
  warehouse_id   UUID          NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
  movement_type  TEXT          NOT NULL
                   CHECK (movement_type IN ('receipt','sale','adjustment','transfer_in','transfer_out','return')),
  quantity       NUMERIC(15,4) NOT NULL,              -- Positive = in, Negative = out
  reference_type TEXT          CHECK (reference_type IN ('sale','purchase','manual')),
  reference_id   UUID,                                -- FK to sale_id or purchase_id (polymorphic)
  notes          TEXT,
  created_by     UUID          REFERENCES users(id) ON DELETE SET NULL,
  created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: sales
-- Sales order / transaction header.
-- Represents a single sale event. customer_id NULL = walk-in customer.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE sales (
  id              UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id      UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  branch_id       UUID          REFERENCES branches(id) ON DELETE SET NULL,
  customer_id     UUID          REFERENCES customers(id) ON DELETE SET NULL,  -- NULL = walk-in
  sale_number     TEXT          NOT NULL,              -- Human-readable e.g. SL-2026-00001
  sale_date       DATE          NOT NULL DEFAULT CURRENT_DATE,
  status          TEXT          NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','confirmed','delivered','cancelled')),
  subtotal        NUMERIC(15,2) NOT NULL DEFAULT 0,
  discount_amount NUMERIC(15,2) NOT NULL DEFAULT 0,
  tax_amount      NUMERIC(15,2) NOT NULL DEFAULT 0,
  total_amount    NUMERIC(15,2) NOT NULL DEFAULT 0,
  currency        CHAR(3)       NOT NULL DEFAULT 'USD',
  notes           TEXT,
  created_by      UUID          REFERENCES users(id) ON DELETE SET NULL,
  deleted_at      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  UNIQUE (company_id, sale_number)
);

CREATE TRIGGER trg_sales_updated_at
  BEFORE UPDATE ON sales
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: sale_items
-- Line items for each sale. Stores a snapshot of price and quantity
-- at the time of the sale — not a live reference to product pricing.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE sale_items (
  id           UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  sale_id      UUID          NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
  product_id   UUID          NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
  warehouse_id UUID          REFERENCES warehouses(id) ON DELETE SET NULL,
  quantity     NUMERIC(15,4) NOT NULL,
  unit_price   NUMERIC(15,4) NOT NULL,               -- Price at time of sale (snapshot)
  discount_pct NUMERIC(5,2)  NOT NULL DEFAULT 0,
  tax_rate     NUMERIC(5,2)  NOT NULL DEFAULT 0,
  line_total   NUMERIC(15,2) NOT NULL,               -- Stored computed value
  created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: purchases
-- Purchase order header. Records what the company bought
-- from a supplier. Drives AP invoice generation.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE purchases (
  id               UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id       UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  branch_id        UUID          REFERENCES branches(id) ON DELETE SET NULL,
  supplier_id      UUID          REFERENCES suppliers(id) ON DELETE SET NULL,
  purchase_number  TEXT          NOT NULL,
  purchase_date    DATE          NOT NULL DEFAULT CURRENT_DATE,
  expected_delivery DATE,
  status           TEXT          NOT NULL DEFAULT 'draft'
                     CHECK (status IN ('draft','ordered','received','cancelled')),
  subtotal         NUMERIC(15,2) NOT NULL DEFAULT 0,
  tax_amount       NUMERIC(15,2) NOT NULL DEFAULT 0,
  total_amount     NUMERIC(15,2) NOT NULL DEFAULT 0,
  currency         CHAR(3)       NOT NULL DEFAULT 'USD',
  notes            TEXT,
  created_by       UUID          REFERENCES users(id) ON DELETE SET NULL,
  deleted_at       TIMESTAMPTZ,
  created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  UNIQUE (company_id, purchase_number)
);

CREATE TRIGGER trg_purchases_updated_at
  BEFORE UPDATE ON purchases
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: purchase_items
-- Line items for each purchase order.
-- received_qty supports partial delivery receipts.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE purchase_items (
  id           UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  purchase_id  UUID          NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
  product_id   UUID          NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
  warehouse_id UUID          REFERENCES warehouses(id) ON DELETE SET NULL,  -- Receiving warehouse
  quantity     NUMERIC(15,4) NOT NULL,
  unit_cost    NUMERIC(15,4) NOT NULL,               -- Cost at time of purchase (snapshot)
  tax_rate     NUMERIC(5,2)  NOT NULL DEFAULT 0,
  line_total   NUMERIC(15,2) NOT NULL,
  received_qty NUMERIC(15,4) NOT NULL DEFAULT 0,     -- For partial delivery tracking
  created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: invoices
-- Financial document for both Accounts Receivable (AR) and
-- Accounts Payable (AP). A single table using invoice_type
-- to avoid duplicating near-identical schemas.
-- amount_due is a generated column: total_amount - amount_paid.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE invoices (
  id             UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id     UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  invoice_type   TEXT          NOT NULL CHECK (invoice_type IN ('receivable','payable')),
  invoice_number TEXT          NOT NULL,
  invoice_date   DATE          NOT NULL DEFAULT CURRENT_DATE,
  due_date       DATE,
  customer_id    UUID          REFERENCES customers(id) ON DELETE SET NULL,  -- AR invoices
  supplier_id    UUID          REFERENCES suppliers(id) ON DELETE SET NULL,  -- AP invoices
  sale_id        UUID          REFERENCES sales(id) ON DELETE SET NULL,
  purchase_id    UUID          REFERENCES purchases(id) ON DELETE SET NULL,
  status         TEXT          NOT NULL DEFAULT 'draft'
                   CHECK (status IN ('draft','sent','partial','paid','overdue','cancelled')),
  subtotal       NUMERIC(15,2) NOT NULL DEFAULT 0,
  tax_amount     NUMERIC(15,2) NOT NULL DEFAULT 0,
  total_amount   NUMERIC(15,2) NOT NULL DEFAULT 0,
  amount_paid    NUMERIC(15,2) NOT NULL DEFAULT 0,
  amount_due     NUMERIC(15,2) GENERATED ALWAYS AS (total_amount - amount_paid) STORED,
  currency       CHAR(3)       NOT NULL DEFAULT 'USD',
  notes          TEXT,
  deleted_at     TIMESTAMPTZ,
  created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  UNIQUE (company_id, invoice_number)
);

CREATE TRIGGER trg_invoices_updated_at
  BEFORE UPDATE ON invoices
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: payments
-- Actual money received or paid against an invoice.
-- Linked to invoices and supports partial payments.
-- exchange_rate supports multi-currency transactions.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE payments (
  id             UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id     UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  invoice_id     UUID          NOT NULL REFERENCES invoices(id) ON DELETE RESTRICT,
  payment_date   DATE          NOT NULL DEFAULT CURRENT_DATE,
  amount         NUMERIC(15,2) NOT NULL,
  payment_method TEXT          CHECK (payment_method IN ('cash','bank_transfer','card','cheque','other')),
  reference      TEXT,                                -- Bank ref / cheque number
  currency       CHAR(3)       NOT NULL DEFAULT 'USD',
  exchange_rate  NUMERIC(10,6) NOT NULL DEFAULT 1,   -- Rate relative to company base currency
  notes          TEXT,
  created_by     UUID          REFERENCES users(id) ON DELETE SET NULL,
  created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_payments_updated_at
  BEFORE UPDATE ON payments
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: expenses
-- Direct business expenses not tied to a purchase order.
-- Examples: rent, utilities, salaries, travel, subscriptions.
-- Supports approval workflow via status + approved_by.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE expenses (
  id             UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id     UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  branch_id      UUID          REFERENCES branches(id) ON DELETE SET NULL,
  category_id    UUID          REFERENCES categories(id) ON DELETE SET NULL,
  description    TEXT          NOT NULL,
  amount         NUMERIC(15,2) NOT NULL,
  expense_date   DATE          NOT NULL DEFAULT CURRENT_DATE,
  payment_method TEXT          CHECK (payment_method IN ('cash','bank_transfer','card','cheque','other')),
  receipt_url    TEXT,                                -- Uploaded receipt file URL
  status         TEXT          NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending','approved','rejected')),
  approved_by    UUID          REFERENCES users(id) ON DELETE SET NULL,
  created_by     UUID          REFERENCES users(id) ON DELETE SET NULL,
  deleted_at     TIMESTAMPTZ,
  created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_expenses_updated_at
  BEFORE UPDATE ON expenses
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

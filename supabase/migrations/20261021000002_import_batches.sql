-- ============================================================
-- Migration 009: Data Import Batches & History
-- AI Financial Intelligence Platform
-- ============================================================
-- Tables: import_batches, import_batch_rows
-- Tracks file import batches, column mappings, validation summaries,
-- idempotency tokens, and execution results.
-- NOTE: Unapplied migration file per Step 7 instructions.
-- ============================================================

CREATE TABLE IF NOT EXISTS import_batches (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id        UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  branch_id         UUID REFERENCES branches(id) ON DELETE SET NULL,
  created_by        UUID REFERENCES users(id) ON DELETE SET NULL,
  entity_type       TEXT NOT NULL CHECK (entity_type IN ('products', 'sales', 'inventory', 'expenses', 'invoices')),
  source_format     TEXT NOT NULL CHECK (source_format IN ('csv', 'xlsx', 'pdf')),
  file_name         TEXT NOT NULL,
  file_size_bytes   BIGINT NOT NULL DEFAULT 0,
  total_rows        INT NOT NULL DEFAULT 0,
  valid_rows        INT NOT NULL DEFAULT 0,
  warning_rows      INT NOT NULL DEFAULT 0,
  invalid_rows      INT NOT NULL DEFAULT 0,
  duplicate_rows    INT NOT NULL DEFAULT 0,
  imported_rows     INT NOT NULL DEFAULT 0,
  status            TEXT NOT NULL DEFAULT 'uploaded'
                      CHECK (status IN (
                        'uploaded',
                        'preview_ready',
                        'validation_failed',
                        'awaiting_confirmation',
                        'importing',
                        'completed',
                        'failed'
                      )),
  idempotency_key   TEXT,
  column_mapping    JSONB NOT NULL DEFAULT '{}',
  validation_errors JSONB NOT NULL DEFAULT '[]',
  summary_details   JSONB NOT NULL DEFAULT '{}',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for company scoped retrieval and history
CREATE INDEX IF NOT EXISTS idx_import_batches_company
  ON import_batches (company_id, created_at DESC);

-- Index for idempotency checks
CREATE INDEX IF NOT EXISTS idx_import_batches_idempotency
  ON import_batches (company_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

-- Enable RLS
ALTER TABLE import_batches ENABLE ROW LEVEL SECURITY;

-- Company isolation policies
CREATE POLICY import_batches_company_isolation_policy
  ON import_batches
  FOR ALL
  USING (
    company_id IN (SELECT get_user_company_ids())
  );

-- Trigger for updated_at
CREATE TRIGGER trg_import_batches_updated_at
  BEFORE UPDATE ON import_batches
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

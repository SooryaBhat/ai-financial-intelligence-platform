-- ============================================================
-- Migration: 20261021000001_ml_predictions_and_outlets.sql
-- Description: Expand prediction types for all 7 ML pipelines,
--              add outlet (branch_id) tracking and model_version
--              to predictions table, and add optimized indexes.
-- Depends on: 20260703000003_ai_domain.sql, 20260703000005_indexes.sql
-- ============================================================

-- 1. Update prediction_type CHECK constraint to support all 7 ML pipelines
ALTER TABLE predictions
  DROP CONSTRAINT IF EXISTS predictions_prediction_type_check;

ALTER TABLE predictions
  ADD CONSTRAINT predictions_prediction_type_check
  CHECK (prediction_type IN (
    'revenue',
    'sales',
    'inventory',
    'profit',
    'expense',
    'business_health',
    'anomaly',
    'cash_flow',
    'fraud_alert'
  ));

-- 2. Add branch_id to track outlet-level predictions
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'predictions' AND column_name = 'branch_id'
  ) THEN
    ALTER TABLE predictions
      ADD COLUMN branch_id UUID REFERENCES branches(id) ON DELETE SET NULL;
  END IF;
END $$;

-- 3. Add model_version to track deployed model or fallback version
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'predictions' AND column_name = 'model_version'
  ) THEN
    ALTER TABLE predictions
      ADD COLUMN model_version TEXT;
  END IF;
END $$;

-- 4. Optimized indexes for tenant-isolated prediction queries
CREATE INDEX IF NOT EXISTS idx_predictions_company_type_created
  ON predictions (company_id, prediction_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_company_branch
  ON predictions (company_id, branch_id)
  WHERE branch_id IS NOT NULL;

-- 5. Comments for documentation and schema introspection
COMMENT ON COLUMN predictions.branch_id IS 'Optional branch / outlet UUID for outlet-specific ML predictions';
COMMENT ON COLUMN predictions.model_version IS 'Model version or artifact identifier (e.g. v2.6.0, AAGF, or fallback)';
COMMENT ON CONSTRAINT predictions_prediction_type_check ON predictions IS 'Supports revenue, sales, inventory, profit, expense, business_health, anomaly, cash_flow, and fraud_alert';

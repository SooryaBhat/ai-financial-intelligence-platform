-- ============================================================
-- Migration 003: AI Domain
-- AI Financial Intelligence Platform
-- ============================================================
-- Tables: ml_models, predictions, prediction_logs,
--         chat_sessions, chat_messages, reports
-- Depends on: 001_platform_domain
-- ============================================================


-- ──────────────────────────────────────────────────────────────
-- TABLE: ml_models
-- Registry of ML models deployed on the platform.
-- company_id NULL = shared platform-level model available to all tenants.
-- Stores versioning, algorithm metadata, and performance scores.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE ml_models (
  id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id     UUID         REFERENCES companies(id) ON DELETE CASCADE, -- NULL = platform-wide model
  name           TEXT         NOT NULL,
  model_type     TEXT         NOT NULL
                   CHECK (model_type IN ('forecasting','anomaly_detection','recommendation','classification')),
  target_metric  TEXT,                                  -- e.g. 'revenue', 'cash_flow', 'inventory'
  algorithm      TEXT,                                  -- e.g. 'xgboost', 'lstm', 'prophet', 'arima'
  version        TEXT,                                  -- e.g. '2.1.0'
  storage_path   TEXT,                                  -- Path to serialised model artifact (S3/bucket)
  is_active      BOOLEAN      NOT NULL DEFAULT true,
  trained_at     TIMESTAMPTZ,
  accuracy_score NUMERIC(6,4),                          -- e.g. 0.9312 (0.0 – 1.0)
  metadata       JSONB        NOT NULL DEFAULT '{}',    -- Hyperparams, feature list, training config
  created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_ml_models_updated_at
  BEFORE UPDATE ON ml_models
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: predictions
-- Stores generated predictions and forecasts, one row per run.
-- actual_value is populated later for model evaluation / drift tracking.
-- input_data and output_data capture full feature snapshots for
-- reproducibility and explainability.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE predictions (
  id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id       UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  ml_model_id      UUID          REFERENCES ml_models(id) ON DELETE SET NULL,
  prediction_type  TEXT          NOT NULL
                     CHECK (prediction_type IN ('revenue','expense','cash_flow','inventory','profit','fraud_alert')),
  period_start     DATE,                                  -- Forecast window start
  period_end       DATE,                                  -- Forecast window end
  predicted_value  NUMERIC(20,4),
  actual_value     NUMERIC(20,4),                         -- Back-filled for model evaluation
  confidence_score NUMERIC(6,4),                          -- 0.0 – 1.0
  input_data       JSONB         NOT NULL DEFAULT '{}',   -- Feature snapshot at inference time
  output_data      JSONB         NOT NULL DEFAULT '{}',   -- Full prediction payload / breakdown
  status           TEXT          NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','completed','failed')),
  created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_predictions_updated_at
  BEFORE UPDATE ON predictions
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: prediction_logs
-- Detailed execution log per prediction pipeline stage.
-- Separated from predictions to keep the predictions table
-- clean and fast to query. Append-only (no updated_at).
-- ──────────────────────────────────────────────────────────────
CREATE TABLE prediction_logs (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  prediction_id UUID        NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
  stage         TEXT        NOT NULL
                  CHECK (stage IN ('preprocessing','inference','postprocessing')),
  status        TEXT        NOT NULL CHECK (status IN ('success','error')),
  message       TEXT,
  duration_ms   INT,                                   -- Execution time in milliseconds
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: chat_sessions
-- One conversational session between a user and the AI Financial
-- Assistant. A user can have many sessions per company.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE chat_sessions (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title       TEXT,                                    -- Auto-generated or user-named
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  deleted_at  TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_chat_sessions_updated_at
  BEFORE UPDATE ON chat_sessions
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- TABLE: chat_messages
-- Individual messages within a chat session.
-- role: 'user' | 'assistant' | 'system'
-- tokens_used enables LLM cost tracking per message.
-- metadata stores tool calls, citations, model version used.
-- Append-only: no updated_at.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE chat_messages (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID        NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role        TEXT        NOT NULL CHECK (role IN ('user','assistant','system')),
  content     TEXT        NOT NULL,
  tokens_used INT,                                     -- For LLM cost tracking
  metadata    JSONB       NOT NULL DEFAULT '{}',       -- Tool calls, citations, model info
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ──────────────────────────────────────────────────────────────
-- TABLE: reports
-- Saved or generated reports (P&L, cash flow, AI insights, etc.).
-- Can be system-triggered (scheduled) or user-triggered (on-demand).
-- data stores the report payload as JSONB for flexible schema.
-- file_url points to an exported PDF/Excel if generated.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE reports (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id   UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  user_id      UUID        REFERENCES users(id) ON DELETE SET NULL,
  report_type  TEXT        NOT NULL
                 CHECK (report_type IN (
                   'profit_loss','cash_flow','balance_sheet',
                   'inventory','ai_insight','sales_summary','expense_summary'
                 )),
  title        TEXT        NOT NULL,
  period_start DATE,
  period_end   DATE,
  data         JSONB       NOT NULL DEFAULT '{}',      -- Full report payload
  file_url     TEXT,                                   -- Exported PDF / Excel URL
  status       TEXT        NOT NULL DEFAULT 'generating'
                 CHECK (status IN ('generating','ready','failed')),
  deleted_at   TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_reports_updated_at
  BEFORE UPDATE ON reports
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

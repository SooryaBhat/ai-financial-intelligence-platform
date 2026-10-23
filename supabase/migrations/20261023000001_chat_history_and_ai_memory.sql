-- ============================================================
-- Migration: 20261023000001_chat_history_and_ai_memory.sql
-- Description: Add chat session summary fields and ai_memories
--              table for long-term cross-conversation memory.
-- ============================================================

-- 1. Add summary columns to chat_sessions for long-conversation summaries
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'chat_sessions' AND column_name = 'summary'
  ) THEN
    ALTER TABLE chat_sessions ADD COLUMN summary TEXT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'chat_sessions' AND column_name = 'last_summarized_at'
  ) THEN
    ALTER TABLE chat_sessions ADD COLUMN last_summarized_at TIMESTAMPTZ;
  END IF;
END $$;

-- 2. Create ai_memories table for cross-conversation user/company memory
CREATE TABLE IF NOT EXISTS ai_memories (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id  UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
  category    TEXT NOT NULL DEFAULT 'preference'
                CHECK (category IN ('preference', 'reporting', 'business_fact', 'goal', 'context')),
  memory_key  TEXT,
  content     TEXT NOT NULL,
  confidence  NUMERIC(4,3) NOT NULL DEFAULT 1.0,
  is_active   BOOLEAN NOT NULL DEFAULT true,
  metadata    JSONB NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger for updated_at on ai_memories
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_ai_memories_updated_at'
  ) THEN
    CREATE TRIGGER trg_ai_memories_updated_at
      BEFORE UPDATE ON ai_memories
      FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
END $$;

-- Indexes for efficient isolated retrieval
CREATE INDEX IF NOT EXISTS idx_ai_memories_lookup
  ON ai_memories (company_id, user_id, is_active, category);

CREATE INDEX IF NOT EXISTS idx_ai_memories_created
  ON ai_memories (company_id, user_id, created_at DESC);

-- Enable Row Level Security
ALTER TABLE ai_memories ENABLE ROW LEVEL SECURITY;

-- RLS Policy: company and user isolation
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'ai_memories' AND policyname = 'ai_memories_isolation_policy'
  ) THEN
    CREATE POLICY "ai_memories_isolation_policy"
      ON ai_memories FOR ALL
      USING (
        company_id IN (SELECT get_user_company_ids())
        AND user_id = auth.uid()
      );
  END IF;
END $$;

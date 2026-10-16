-- ============================================================
-- Safe Rollback Script for Migration 20261015000001_knowledge_base_rag.sql
-- ALLADIN Knowledge Base RAG Domain
-- ============================================================
-- SAFEGUARD POLICY:
-- This script CANNOT unintentionally delete indexed documents or vector embeddings.
-- If document_chunks or knowledge_documents contains data, this script will ABORT
-- with a descriptive error.
--
-- To execute an intentional rollback of a populated database, the operator MUST
-- explicitly set this session parameter prior to running this script:
--   SET app.force_rag_rollback = 'true';
-- ============================================================

DO $$
DECLARE
  v_chunk_count INT := 0;
  v_doc_count   INT := 0;
  v_force       TEXT;
BEGIN
  -- Read safety override flag from current transaction/session settings
  BEGIN
    SELECT current_setting('app.force_rag_rollback', true) INTO v_force;
  EXCEPTION WHEN OTHERS THEN
    v_force := 'false';
  END;

  -- Verify if tables exist before counting
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'document_chunks') THEN
    EXECUTE 'SELECT COUNT(*) FROM public.document_chunks' INTO v_chunk_count;
  END IF;

  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'knowledge_documents') THEN
    EXECUTE 'SELECT COUNT(*) FROM public.knowledge_documents' INTO v_doc_count;
  END IF;

  -- Safety gate: abort if data exists and force flag is not explicitly enabled
  IF (v_chunk_count > 0 OR v_doc_count > 0) AND (v_force IS DISTINCT FROM 'true') THEN
    RAISE EXCEPTION 'ROLLBACK ABORTED: RAG tables contain data (% documents, % chunks). Dropping will destroy vector embeddings. To confirm deletion, run: SET app.force_rag_rollback = ''true''; then re-run rollback.', v_doc_count, v_chunk_count;
  END IF;

  RAISE NOTICE 'Rollback safety checks passed. Proceeding with safe removal of RAG database objects...';
END;
$$;

-- 1. Drop stored procedure with exact parameter signature
DROP FUNCTION IF EXISTS public.match_document_chunks(vector(768), FLOAT, INT, TEXT, UUID, TEXT);

-- 2. Drop RLS policies
DROP POLICY IF EXISTS "knowledge_documents_isolation" ON public.knowledge_documents;
DROP POLICY IF EXISTS "document_chunks_isolation"     ON public.document_chunks;

-- 3. Drop triggers
DROP TRIGGER IF EXISTS trg_knowledge_documents_updated_at ON public.knowledge_documents;

-- 4. Drop tables in strict reverse-dependency order
DROP TABLE IF EXISTS public.document_chunks CASCADE;
DROP TABLE IF EXISTS public.knowledge_documents CASCADE;

-- 5. Extension and core utility preservation:
-- Extension 'vector' is NOT dropped because other extensions or future migrations may rely on it.
-- Function 'set_updated_at()' is NOT dropped because it was defined in Migration 001 and is used across all tables.

DO $$
BEGIN
  RAISE NOTICE 'RAG database objects successfully removed. Existing ERP tables and core functions are completely untouched.';
END;
$$;

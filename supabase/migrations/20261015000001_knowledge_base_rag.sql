-- ============================================================
-- Migration 008 (20261015000001): Knowledge Base RAG Domain (Revised)
-- ALLADIN — AI-powered Ledger Learning and Analytics for Decision Intelligence Network
-- ============================================================
-- Tables: knowledge_documents, document_chunks
-- Functions: match_document_chunks (cosine similarity retrieval)
-- Depends on: 001_platform_domain, 006_rls_policies
-- Multi-Tenancy:
--   - Single source of truth: company_id on knowledge_documents ONLY.
--   - document_chunks derives tenant scoping strictly from parent document_id.
--   - Global shared knowledge: company_id IS NULL.
--   - Private tenant knowledge: company_id = <UUID>.
-- Security:
--   - SECURITY DEFINER with fixed search_path = public, pg_temp.
--   - Caller authorization checked via get_user_company_ids().
--   - Forged filter_company_id from untrusted callers is strictly rejected.
-- ============================================================

-- ──────────────────────────────────────────────────────────────
-- 1. EXTENSION: pgvector
-- Provides vector data type and distance operators (<=> cosine)
-- ──────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;


-- ──────────────────────────────────────────────────────────────
-- 2. TABLE: knowledge_documents
-- Master catalog of indexed knowledge base documents.
-- company_id NULL = shared platform-level knowledge (public MSME docs, guides).
-- company_id <UUID> = private company-uploaded proprietary knowledge.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_documents (
  id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id           UUID         REFERENCES companies(id) ON DELETE CASCADE, -- NULL = platform-wide shared knowledge
  doc_id               TEXT         NOT NULL,                                   -- e.g. 'OD-03', 'BG-01'
  title                TEXT         NOT NULL,
  author               TEXT,
  issuing_organization TEXT,
  publication_year     INT,
  topic_category       TEXT         NOT NULL,                                   -- e.g. 'accounting', 'sme_msme_india'
  content_type         TEXT         NOT NULL DEFAULT 'official_source'
                         CHECK (content_type IN ('official_source', 'book', 'internal_guide', 'AI_assisted_draft', 'fictional_case_study', 'company_private')),
  review_status        TEXT         NOT NULL DEFAULT 'unreviewed'
                         CHECK (review_status IN ('unreviewed', 'in_review', 'reviewed', 'needs_update', 'deprecated')),
  embedding_model      TEXT         NOT NULL DEFAULT 'gemini-embedding-001',    -- Enforces vector space compatibility
  embedding_dimension  INT          NOT NULL DEFAULT 768,
  license_terms        TEXT,
  source_url           TEXT,
  local_path           TEXT,
  metadata             JSONB        NOT NULL DEFAULT '{}',
  is_active            BOOLEAN      NOT NULL DEFAULT true,
  created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Partial unique indexes: universal compatibility across all PostgreSQL versions
CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_documents_tenant_doc
  ON knowledge_documents (company_id, doc_id)
  WHERE company_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_documents_global_doc
  ON knowledge_documents (doc_id)
  WHERE company_id IS NULL;

-- Trigger for auto-updating updated_at using existing set_updated_at() from Migration 001
CREATE TRIGGER trg_knowledge_documents_updated_at
  BEFORE UPDATE ON knowledge_documents
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ──────────────────────────────────────────────────────────────
-- 3. TABLE: document_chunks
-- Chunks of extracted text with vector embeddings and full-text search tsvector.
-- TENANT CONSISTENCY: company_id is intentionally omitted here to prevent
-- tenant desynchronization; tenant scoping is derived strictly via document_id.
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_chunks (
  id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id   UUID         NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  doc_id        TEXT         NOT NULL,
  chunk_index   INT          NOT NULL,
  content       TEXT         NOT NULL,
  section_title TEXT,
  page_number   INT,
  metadata      JSONB        NOT NULL DEFAULT '{}',
  embedding     vector(768),                                            -- 768-dim vector matching configured embedding service
  tsv           tsvector     GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_document_chunks_index UNIQUE (document_id, chunk_index)
);


-- ──────────────────────────────────────────────────────────────
-- 4. INDEXES
-- HNSW index for fast approximate nearest neighbor vector search
-- GIN index for PostgreSQL full-text search (ts_rank cover density)
-- B-tree indexes for foreign keys and topic queries
-- ──────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
  ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_document_chunks_tsv
  ON document_chunks USING gin (tsv);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
  ON document_chunks (document_id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id
  ON document_chunks (doc_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_company_id
  ON knowledge_documents (company_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_category
  ON knowledge_documents (topic_category);


-- ──────────────────────────────────────────────────────────────
-- 5. ROW LEVEL SECURITY (RLS)
-- Multi-tenant isolation verified at the database layer.
-- ──────────────────────────────────────────────────────────────
ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks     ENABLE ROW LEVEL SECURITY;

-- knowledge_documents policy: read global knowledge OR documents of caller's active companies
CREATE POLICY "knowledge_documents_isolation"
  ON knowledge_documents FOR SELECT
  USING (
    company_id IN (SELECT get_user_company_ids())
    OR company_id IS NULL
  );

-- document_chunks policy: derived strictly via parent document_id
CREATE POLICY "document_chunks_isolation"
  ON document_chunks FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM knowledge_documents kd
      WHERE kd.id = document_chunks.document_id
        AND (
          kd.company_id IN (SELECT get_user_company_ids())
          OR kd.company_id IS NULL
        )
    )
  );


-- ──────────────────────────────────────────────────────────────
-- 6. STORED PROCEDURE: match_document_chunks
-- Performs hybrid vector cosine similarity retrieval with strict
-- tenant isolation and similarity threshold filtering.
--
-- SECURITY SAFEGUARDS:
-- - Fixed search_path = public, pg_temp prevents search_path hijacking.
-- - filter_company_id is verified against get_user_company_ids() for
--   authenticated users. An attacker CANNOT access another company's
--   private documents simply by supplying a foreign UUID.
-- - Global platform-wide documents (company_id IS NULL) remain accessible.
-- ──────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION match_document_chunks(
  query_embedding       vector(768),
  match_threshold       FLOAT DEFAULT 0.65,
  match_count           INT   DEFAULT 5,
  filter_doc_type       TEXT  DEFAULT NULL,
  filter_company_id     UUID  DEFAULT NULL,
  filter_embedding_model TEXT DEFAULT 'gemini-embedding-001'
)
RETURNS TABLE (
  id            UUID,
  document_id   UUID,
  doc_id        TEXT,
  title         TEXT,
  author        TEXT,
  content       TEXT,
  section_title TEXT,
  page_number   INT,
  metadata      JSONB,
  similarity    FLOAT
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.document_id,
    dc.doc_id,
    kd.title,
    kd.author,
    dc.content,
    dc.section_title,
    dc.page_number,
    dc.metadata,
    (1 - (dc.embedding <=> query_embedding))::FLOAT AS similarity
  FROM document_chunks dc
  JOIN knowledge_documents kd ON dc.document_id = kd.id
  WHERE kd.is_active = true
    AND (1 - (dc.embedding <=> query_embedding)) >= match_threshold
    AND (filter_doc_type IS NULL OR kd.content_type = filter_doc_type)
    -- Enforce vector space compatibility (do not mix incompatible embedding models)
    AND (filter_embedding_model IS NULL OR kd.embedding_model = filter_embedding_model)
    AND (
      -- 1. Shared global knowledge is accessible to all
      kd.company_id IS NULL
      OR
      -- 2. Server-side service_role (background batch jobs) can query specified company
      (
        auth.role() = 'service_role'
        AND (filter_company_id IS NULL OR kd.company_id = filter_company_id)
      )
      OR
      -- 3. Authenticated end-users MUST belong to the company they are querying
      (
        auth.uid() IS NOT NULL
        AND kd.company_id IN (SELECT get_user_company_ids())
        AND (filter_company_id IS NULL OR kd.company_id = filter_company_id)
      )
    )
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Restrict execution: revoke from anonymous public, grant strictly to authenticated and service_role
REVOKE ALL ON FUNCTION match_document_chunks(vector(768), FLOAT, INT, TEXT, UUID, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION match_document_chunks(vector(768), FLOAT, INT, TEXT, UUID, TEXT) TO authenticated, service_role;

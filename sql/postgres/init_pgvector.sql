CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS tenant_document_chunks (
    chunk_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    classification TEXT NOT NULL,
    retention_state TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS tenant_document_chunks_tenant_doc_type_idx
ON tenant_document_chunks (tenant_id, doc_type, retention_state);

CREATE INDEX IF NOT EXISTS tenant_document_chunks_embedding_ivfflat
ON tenant_document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

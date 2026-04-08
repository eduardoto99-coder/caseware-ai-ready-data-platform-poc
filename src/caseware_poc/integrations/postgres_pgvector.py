from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import psycopg
from pgvector.psycopg import register_vector


@dataclass(slots=True)
class PgVectorConfig:
    dsn: str
    embedding_dimensions: int = 1536


class PgVectorDocumentStore:
    """Reference Aurora PostgreSQL/pgvector store for tenant-scoped semantic search."""

    def __init__(self, config: PgVectorConfig) -> None:
        self.config = config

    def connect(self) -> psycopg.Connection:
        connection = psycopg.connect(self.config.dsn)
        register_vector(connection)
        return connection

    def ensure_schema(self) -> None:
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS tenant_document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    retention_state TEXT NOT NULL,
                    source_uri TEXT NOT NULL,
                    chunk_text TEXT NOT NULL,
                    embedding VECTOR({self.config.embedding_dimensions}) NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS tenant_document_chunks_tenant_doc_type_idx
                ON tenant_document_chunks (tenant_id, doc_type, retention_state)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS tenant_document_chunks_embedding_ivfflat
                ON tenant_document_chunks
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
                """
            )

    def search(
        self,
        *,
        tenant_id: str,
        query_embedding: list[float],
        top_k: int,
        doc_type: str | None = None,
    ) -> list[dict[str, object]]:
        predicates = ["tenant_id = %(tenant_id)s", "retention_state = 'active'"]
        if doc_type:
            predicates.append("doc_type = %(doc_type)s")
        where_clause = " AND ".join(predicates)
        sql = f"""
        SELECT
            chunk_id,
            tenant_id,
            document_id,
            doc_type,
            classification,
            retention_state,
            source_uri,
            chunk_text,
            1 - (embedding <=> %(query_embedding)s::vector) AS similarity
        FROM tenant_document_chunks
        WHERE {where_clause}
        ORDER BY embedding <=> %(query_embedding)s::vector
        LIMIT %(top_k)s
        """
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                sql,
                {
                    "tenant_id": tenant_id,
                    "doc_type": doc_type,
                    "query_embedding": query_embedding,
                    "top_k": top_k,
                },
            )
            columns = [column.name for column in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def upsert_chunks(self, rows: Iterable[dict[str, object]]) -> None:
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO tenant_document_chunks (
                    chunk_id,
                    tenant_id,
                    document_id,
                    doc_type,
                    classification,
                    retention_state,
                    source_uri,
                    chunk_text,
                    embedding
                )
                VALUES (
                    %(chunk_id)s,
                    %(tenant_id)s,
                    %(document_id)s,
                    %(doc_type)s,
                    %(classification)s,
                    %(retention_state)s,
                    %(source_uri)s,
                    %(chunk_text)s,
                    %(embedding)s
                )
                ON CONFLICT (chunk_id) DO UPDATE SET
                    chunk_text = EXCLUDED.chunk_text,
                    embedding = EXCLUDED.embedding,
                    retention_state = EXCLUDED.retention_state
                """,
                rows,
            )

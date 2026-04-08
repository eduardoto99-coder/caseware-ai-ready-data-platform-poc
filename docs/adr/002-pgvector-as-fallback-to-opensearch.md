# ADR-002: pgvector as fallback to OpenSearch Serverless

## Status

Accepted

## Context

The platform needs a vector store for tenant-scoped document retrieval. Two backends were evaluated:

1. **OpenSearch Serverless** with HNSW/FAISS indexing and hybrid (lexical + vector) search.
2. **Aurora PostgreSQL with pgvector** using IVFFlat indexing and cosine distance.

## Decision

OpenSearch Serverless is the primary retrieval backend. pgvector serves as a lower-cost fallback for tenants with smaller document sets or during OpenSearch outages.

## Rationale

### OpenSearch as primary

- **Hybrid search**: Combines BM25 lexical matching with vector similarity in a single query, improving recall for domain-specific terms (e.g., "ASC 606") that pure embeddings may not capture.
- **Managed serverless**: No capacity planning or index shard management. Scales to zero when idle.
- **Tenant isolation at query time**: Boolean filters on `tenant_id` and `retention_state` are evaluated before KNN scoring, so cross-tenant results are structurally impossible.

### pgvector as fallback

- **Cost**: For tenants with fewer than 10,000 chunks, a shared Aurora PostgreSQL instance with pgvector is significantly cheaper than an OpenSearch Serverless collection.
- **Operational simplicity**: pgvector runs inside the existing Aurora cluster used for OLTP, so it does not require a separate service or deployment pipeline.
- **Acceptable latency**: IVFFlat with 100 lists and cosine distance returns top-4 results in under 50ms for indexes under 100K vectors.

### Why not pgvector-only

- pgvector does not support hybrid (lexical + vector) search in a single query. Accounting documents contain precise regulatory references (e.g., "IFRS 15.B38") where lexical matching is essential.
- IVFFlat recall degrades as the index grows past 500K vectors without retuning the list count.

## Trade-offs

- Running two retrieval backends increases integration surface and requires the router to select the backend per tenant or per query.
- pgvector's IVFFlat index must be periodically rebuilt (`REINDEX`) as new chunks are inserted, which briefly locks the table.

## When to revisit

- If OpenSearch Serverless costs become prohibitive, evaluate pgvector with HNSW (available in pgvector 0.5+) as a single-backend replacement.
- If the platform adds cross-tenant search (e.g., for global policy lookup), reassess the tenant-isolation model.

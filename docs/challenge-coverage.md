# Challenge Coverage

This file maps the original challenge requirements to concrete implementation artifacts in the repository.

## A. Incremental Ingestion

Implemented in:

- `src/caseware_poc/ingestion/sample_data.py`
- `src/caseware_poc/ingestion/pipeline.py`

Coverage:

- CDC-style microbatch simulation with `batch_01` through `batch_03`
- Inserts, updates, deletes, duplicates, and late-arriving events
- Incremental document ingestion for new/changed records
- No full reload logic in the serving path

## B. Medallion Architecture

Implemented in:

- `src/caseware_poc/transformations/lakehouse.py`

Coverage:

- Bronze: raw landing Parquet
- Silver: dedupe, latest-wins reconciliation, normalized entity snapshots
- Gold: curated serving tables for invoices, engagements, and control exceptions

## C. AI / RAG Layer

Implemented in:

- `src/caseware_poc/rag/chunking.py`
- `src/caseware_poc/rag/embedding.py`
- `src/caseware_poc/rag/index.py`
- `src/caseware_poc/rag/service.py`

Coverage:

- Chunking with narrative overlap and table-aware handling
- Vector generation and persisted shared index
- Metadata filtering for `tenant_id`, `doc_type`, and `retention_state`
- Explicit guardrail that keeps exact facts out of the embedding-first path

## D. Agent / Query Routing

Implemented in:

- `src/caseware_poc/serving/router.py`
- `src/caseware_poc/serving/sql_service.py`
- `src/caseware_poc/serving/query_service.py`
- `src/caseware_poc/serving/skills.py`

Coverage:

- Structured questions route to the SQL skill
- Narrative questions route to the RAG skill
- Mixed questions trigger the precision guardrail skill
- The API returns both the selected skill and the rules that fired

## E. Tenant Isolation

Implemented in:

- `src/caseware_poc/ingestion/sample_data.py`
- `src/caseware_poc/transformations/lakehouse.py`
- `src/caseware_poc/rag/index.py`
- `src/caseware_poc/serving/sql_service.py`

Coverage:

- Tenant ID carried from source to serving tables
- Tenant filter on all SQL queries
- Tenant filter enforced before vector similarity scoring
- No global retrieve-then-filter anti-pattern

## F. Data Quality and Observability

Implemented in:

- `src/caseware_poc/transformations/lakehouse.py`
- `src/caseware_poc/common/logging_utils.py`

Coverage:

- Schema drift detection
- Duplicate-event detection
- Freshness calculations
- Null/completeness checks
- Gold lineage references
- Retrieval logging, latency logging, attribution logging

## G. Architecture Trade-Offs

Documented in:

- `docs/architecture.md`
- `docs/aws-production-mapping.md`
- `docs/interview-walkthrough.md`

Coverage:

- Glue vs EMR Spark
- Microbatch vs streaming
- Shared vector index vs per-tenant index
- SQL vs embeddings for structured data
- Bronze/silver/gold layer responsibilities
- Local POC to AWS production evolution

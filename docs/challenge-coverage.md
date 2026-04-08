# Challenge Coverage

This file maps the original challenge requirements to concrete implementation artifacts in the repository.

The implementation is intentionally split into:

- a runnable local path
- a production-shaped reference path

Both paths cover the same architecture boundary, but they use different tools.

## A. Incremental Ingestion

Implemented in:

- `src/caseware_poc/ingestion/sample_data.py`
- `src/caseware_poc/ingestion/pipeline.py`
- `jobs/spark/cdc_to_bronze.py`
- `src/caseware_poc/integrations/kafka_cdc_consumer.py`

Coverage:

- CDC-style microbatch simulation with `batch_01` through `batch_03`
- Inserts, updates, deletes, duplicates, and late-arriving events
- Incremental document ingestion for new/changed records
- No full reload logic in the serving path
- Production-shaped Kafka/MSK -> Spark -> Iceberg bronze ingestion path

## B. Medallion Architecture

Implemented in:

- `src/caseware_poc/transformations/lakehouse.py`
- `jobs/spark/bronze_to_silver.py`
- `jobs/spark/silver_to_gold.py`
- `sql/iceberg/medallion_tables.sql`

Coverage:

- Bronze: raw landing Parquet
- Silver: dedupe, latest-wins reconciliation, normalized entity snapshots
- Gold: curated serving tables for invoices, engagements, and control exceptions
- Production-shaped Iceberg DDL and Spark jobs for the same medallion flow

## C. AI / RAG Layer

Implemented in:

- `src/caseware_poc/rag/chunking.py`
- `src/caseware_poc/rag/embedding.py`
- `src/caseware_poc/rag/index.py`
- `src/caseware_poc/rag/service.py`
- `src/caseware_poc/integrations/opensearch_vector_store.py`
- `src/caseware_poc/integrations/postgres_pgvector.py`
- `sql/opensearch/tenant_audit_documents_index.json`
- `sql/postgres/init_pgvector.sql`

Coverage:

- Chunking with narrative overlap and table-aware handling
- Vector generation and persisted shared index
- Metadata filtering for `tenant_id`, `doc_type`, and `retention_state`
- Explicit guardrail that keeps exact facts out of the embedding-first path
- Reference implementations for both OpenSearch and pgvector-backed retrieval

## D. Agent / Query Routing

Implemented in:

- `src/caseware_poc/serving/router.py`
- `src/caseware_poc/serving/sql_service.py`
- `src/caseware_poc/serving/query_service.py`
- `src/caseware_poc/serving/skills.py`
- `guardrails/`
- `src/caseware_poc/agents/prompt_loader.py`
- `src/caseware_poc/agents/guardrails.py`
- `src/caseware_poc/agents/langgraph_workflow.py`

Coverage:

- Structured questions route to the SQL skill
- Narrative questions route to the RAG skill
- Mixed questions trigger the precision guardrail skill
- The API returns both the selected skill and the rules that fired
- The production reference path shows LangGraph, Bedrock, Trino, and OpenSearch wired to the same repo-native guardrail files

## E. Tenant Isolation

Implemented in:

- `src/caseware_poc/ingestion/sample_data.py`
- `src/caseware_poc/transformations/lakehouse.py`
- `src/caseware_poc/rag/index.py`
- `src/caseware_poc/serving/sql_service.py`
- `guardrails/rules/tenant_isolation.yaml`
- `src/caseware_poc/agents/guardrails.py`

Coverage:

- Tenant ID carried from source to serving tables
- Tenant filter on all SQL queries
- Tenant filter enforced before vector similarity scoring
- No global retrieve-then-filter anti-pattern
- Reference tenant-boundary enforcement for future authenticated agent flows

## F. Data Quality and Observability

Implemented in:

- `src/caseware_poc/transformations/lakehouse.py`
- `src/caseware_poc/common/logging_utils.py`
- `src/caseware_poc/observability/cloudwatch_metrics.py`
- `src/caseware_poc/observability/langfuse_tracer.py`
- `src/caseware_poc/observability/newrelic_monitoring.py`
- `infra/cdk/stacks/observability_stack.py`

Coverage:

- Schema drift detection
- Duplicate-event detection
- Freshness calculations
- Null/completeness checks
- Gold lineage references
- Retrieval logging, latency logging, attribution logging
- Production-shaped CloudWatch alarms and dashboards
- Langfuse and New Relic reference wiring

## G. Architecture Trade-Offs

Documented in:

- `docs/architecture.md`
- `docs/aws-production-mapping.md`
- `docs/interview-walkthrough.md`
- `docs/terminology-mapping.md`

Coverage:

- Glue vs EMR Spark
- Trino vs Athena
- OpenSearch vs pgvector
- Microbatch vs streaming
- Shared vector index vs per-tenant index
- SQL vs embeddings for structured data
- Bronze/silver/gold layer responsibilities
- Local POC to AWS production evolution

## H. Role-Aligned Reference Stack

Implemented in:

- `infra/cdk/`
- `infra/k8s/`
- `jobs/spark/`
- `sql/`
- `src/caseware_poc/integrations/`
- `src/caseware_poc/agents/`
- `src/caseware_poc/observability/`
- `src/caseware_poc/production/reference_architecture.py`

Coverage:

- Spark
- Trino
- Kafka / MSK
- S3
- Glue Catalog
- Lake Formation
- Athena
- Iceberg
- EMR Serverless
- Aurora PostgreSQL
- pgvector
- OpenSearch Serverless
- Bedrock
- LangGraph
- Langfuse
- CloudWatch
- New Relic
- EKS
- AWS CDK

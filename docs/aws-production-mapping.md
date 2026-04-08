# AWS Production Mapping

This repository already uses an AWS- and platform-shaped architecture for the challenge. This file explains how each layer is expressed in the codebase and where lightweight stand-ins are used to avoid provisioning real infrastructure.

## Stack to Artifact Mapping

| Architecture layer | Primary target stack | Repo artifact | Demo note |
| --- | --- | --- | --- |
| Bronze, silver, and gold storage | S3 + Iceberg + Glue Catalog + Lake Formation | `jobs/spark/*.py`, `sql/iceberg/medallion_tables.sql`, `infra/cdk/constructs/lakehouse_construct.py`, `src/caseware_poc/integrations/glue_catalog.py` | Local Parquet and DuckDB are used to keep the POC inspectable |
| Structured transformation runtime | Spark on EMR / EMR Serverless | `jobs/spark/*.py`, `infra/cdk/stacks/data_platform_stack.py` | Local transformation code mirrors the same medallion logic |
| Exact structured serving | Trino over Iceberg, with Athena for governed analytics | `src/caseware_poc/integrations/trino_client.py`, `sql/trino/gold_serving_views.sql`, `infra/cdk/stacks/data_platform_stack.py` | DuckDB is used as a small-footprint SQL stand-in in the demo harness |
| Document retrieval | OpenSearch Serverless or Aurora PostgreSQL with pgvector | `src/caseware_poc/integrations/opensearch_vector_store.py`, `src/caseware_poc/integrations/postgres_pgvector.py`, `sql/opensearch/*`, `sql/postgres/*` | The runnable demo uses a local vector index to avoid external dependencies |
| Agent orchestration | Bedrock + LangGraph + LLM proxy | `src/caseware_poc/agents/langgraph_workflow.py`, `src/caseware_poc/integrations/bedrock_runtime.py`, `infra/k8s/llm-proxy-deployment.yaml` | The local API exposes the same routing and guardrail contracts without invoking live models |
| Observability | CloudWatch + Langfuse + New Relic | `src/caseware_poc/observability/*`, `infra/cdk/stacks/observability_stack.py`, `infra/k8s/langfuse/values.yaml`, `infra/k8s/newrelic/values.yaml` | Local JSON logging remains in place for the demo |
| Guardrails and context management | Repo-native skills, rules, contracts, and templates | `guardrails/*`, `src/caseware_poc/guardrails/registry.py`, `src/caseware_poc/agents/prompt_loader.py` | The same policy files are used across serving and agent layers |

## Glue vs EMR Spark

### Glue

Prefer Glue when:

- the team wants managed ETL with lower operational overhead
- pipelines are mostly scheduled transformations
- the platform already standardizes on Glue jobs and Data Catalog integration

### EMR Spark

Prefer EMR or EMR Serverless when:

- transformation logic becomes more complex or performance-sensitive
- the team needs stronger Spark control and tuning
- workloads include heavier joins, backfills, or lakehouse table maintenance

For this challenge, EMR-style Spark is the more natural production mapping because the problem statement emphasizes lakehouse patterns, medallion layers, and platform-grade transformation control.

## Trino vs Athena

### Athena

Prefer Athena when:

- workloads are mostly ad hoc analytics
- the team wants minimal infrastructure for SQL over S3/Iceberg
- concurrency and latency requirements are modest

### Trino

Prefer Trino when:

- the platform needs a long-lived governed serving layer
- AI tools need predictable query behavior against gold data products
- the team expects broader federation and interactive SQL workloads

This repo includes both, but the agent-facing exact-query path is centered on Trino.

## OpenSearch vs pgvector

### OpenSearch Serverless

Prefer OpenSearch when:

- hybrid lexical + vector retrieval matters
- operational search features are important
- the system benefits from dedicated search infrastructure

### Aurora PostgreSQL + pgvector

Prefer pgvector when:

- vector search needs to stay close to transactional or relational metadata
- the team prefers one operational database for retrieval metadata and embeddings
- SQL-native filtering and governance are strong requirements

The repo intentionally shows both patterns because either one could be defensible in a real architecture review.

## Shared vs Per-Tenant Vector Index

### Shared index

Pros:

- operationally simpler
- cheaper at small scale
- easier to benchmark and administer

Cons:

- stronger need for airtight filter enforcement
- noisier operational blast radius
- more careful governance required for multi-tenant search

### Per-tenant index

Pros:

- cleaner isolation boundary
- simpler audit story
- fewer noisy-neighbor concerns

Cons:

- more index lifecycle overhead
- more objects and operational cost
- weaker utilization when tenant footprints are small

The POC uses a shared index to keep the implementation compact, but it still enforces the critical design rule: filter first, score second.

## Bedrock / Agent Runtime Evolution

The serving layer in the POC is intentionally lightweight. The architecture still shows:

- LangGraph orchestration for multi-step flows
- Bedrock for grounded answer synthesis
- OpenSearch and Trino as explicit tools
- Langfuse, CloudWatch, and New Relic for agent observability
- repo-native `guardrails/` files for context management and hallucination control

The important boundary should remain unchanged:

- SQL owns exact financial truth
- RAG owns narrative context
- guardrails own mixed questions

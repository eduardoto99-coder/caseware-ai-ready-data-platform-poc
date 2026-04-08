# AWS Production Mapping

The local implementation is intentionally small. This file shows how the same contracts and boundaries would translate into a production AWS stack.

The repository now also contains production-shaped reference files for many of these services under `infra/`, `jobs/`, `sql/`, `guardrails/`, `src/caseware_poc/integrations/`, `src/caseware_poc/agents/`, and `src/caseware_poc/observability/`.

## Local to AWS Mapping

| Local POC component | Production AWS equivalent | Repo artifact |
| --- | --- | --- |
| Parquet bronze/silver/gold files | S3 + Iceberg | `jobs/spark/*.py`, `sql/iceberg/medallion_tables.sql`, `infra/cdk/constructs/lakehouse_construct.py` |
| Local table discovery | Glue Data Catalog | `src/caseware_poc/integrations/glue_catalog.py`, `infra/cdk/stacks/data_platform_stack.py` |
| Tenant-aware governed access assumptions | Lake Formation | `infra/cdk/constructs/lakehouse_construct.py`, `src/caseware_poc/integrations/trino_client.py` |
| DuckDB transforms | EMR / EMR Serverless Spark | `jobs/spark/*.py`, `infra/cdk/stacks/data_platform_stack.py` |
| DuckDB gold serving | Trino over Iceberg or Athena | `src/caseware_poc/integrations/trino_client.py`, `sql/trino/gold_serving_views.sql` |
| Local vector index | OpenSearch Serverless or Aurora PostgreSQL with pgvector | `src/caseware_poc/integrations/opensearch_vector_store.py`, `src/caseware_poc/integrations/postgres_pgvector.py`, `sql/opensearch/*`, `sql/postgres/*` |
| Local JSON logs | CloudWatch + Langfuse + New Relic | `src/caseware_poc/observability/*`, `infra/cdk/stacks/observability_stack.py`, `infra/k8s/langfuse/values.yaml`, `infra/k8s/newrelic/values.yaml` |
| Rules-based API | EKS-hosted API and LLM proxy | `infra/cdk/stacks/data_platform_stack.py`, `infra/k8s/llm-proxy-deployment.yaml` |
| Local orchestration inside scripts | MSK + EMR Serverless + Bedrock + EKS workflow | `jobs/spark/*.py`, `src/caseware_poc/agents/langgraph_workflow.py`, `infra/cdk/stacks/*.py` |
| Local guardrail registry | Repo-native guardrails + Bedrock/LangGraph prompt assembly | `guardrails/*`, `src/caseware_poc/guardrails/registry.py`, `src/caseware_poc/agents/prompt_loader.py` |

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

This repo includes both in the reference layer, but the agent-facing exact-query path is centered on Trino.

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

The current local serving layer is rules-based. The reference path shows how it evolves to:

- LangGraph orchestration for multi-step flows
- Bedrock for grounded answer synthesis
- OpenSearch and Trino as explicit tools
- Langfuse, CloudWatch, and New Relic for agent observability
- repo-native `guardrails/` files for context management and hallucination control

The important boundary should remain unchanged:

- SQL owns exact financial truth
- RAG owns narrative context
- guardrails own mixed questions

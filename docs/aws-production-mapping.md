# AWS Production Mapping

The local implementation is intentionally small. This file shows how the same contracts and boundaries would translate into a production AWS stack.

## Local to AWS Mapping

| Local POC component | Production AWS equivalent | Why |
| --- | --- | --- |
| Parquet landing files | S3 | Durable, low-cost lakehouse storage |
| Local table discovery | Glue Data Catalog | Shared metadata and schema governance |
| File-level access assumptions | Lake Formation | Fine-grained access control and table policies |
| DuckDB transforms | EMR / EMR Serverless Spark | Scalable transformation runtime |
| DuckDB gold serving | Athena, Trino, Redshift Serverless, or managed query APIs | Exact SQL serving depending on latency and concurrency needs |
| Local JSON logs | CloudWatch + OpenTelemetry | Centralized metrics, traces, and alerts |
| Shared vector index on local disk | OpenSearch Serverless vector engine or a managed vector store | Scalable semantic retrieval |
| Rules-based API | FastAPI on ECS/Fargate, Lambda, or EKS | Managed serving boundary |
| Local orchestration inside scripts | Step Functions + EventBridge + Lambda | Scheduled ingestion and operational workflows |

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

The current serving layer is rules-based. In production, it could evolve to:

- LangGraph or a lightweight orchestration layer for multi-step flows
- Bedrock or another managed LLM runtime for grounded answer synthesis
- tool-aware routing where SQL and retrieval are invoked as explicit tools rather than hidden implementation details

The important boundary should remain unchanged:

- SQL owns exact financial truth
- RAG owns narrative context
- guardrails own mixed questions

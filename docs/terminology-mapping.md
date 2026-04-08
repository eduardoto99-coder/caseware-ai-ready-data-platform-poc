# Terminology Mapping

This document answers a specific interview question: which platform, data, AI, governance, AWS, and operations terms were actually used in this POC, and which ones were intentionally left out.

Status meanings:

- `Used directly`: implemented in the repository runtime or serving flow
- `Used directly (challenge artifact)`: implemented in challenge-facing infrastructure, integration, SQL, Spark, or agent files
- `Represented conceptually`: not deployed as the named product/service, but the POC models the idea or documents how it maps to production
- `Not used intentionally`: left out to keep the reference implementation small, runnable, and focused on the core problem

## Architecture and Data Platform Terms

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| Lakehouse | Used directly | The repo uses a local lakehouse pattern with Parquet-backed bronze, silver, and gold layers described in [architecture.md](./architecture.md) and implemented in `src/caseware_poc/transformations/lakehouse.py`. |
| Warehouse pattern | Represented conceptually | The DuckDB gold-serving layer acts like a lightweight warehouse pattern for governed business queries, but the repo does not stand up a separate warehouse product. |
| Medallion architecture | Used directly | Bronze, silver, and gold layers are core to the implementation and are explicitly documented and materialized. |
| Data product | Used directly | `gold_invoice_summary`, `gold_engagement_status`, and `gold_control_exceptions` are treated as governed data products with stable semantics and lineage. |
| Interoperability | Represented conceptually | The repo emphasizes tenant-safe APIs, SQL products, and governed retrieval boundaries, but it does not integrate with external customer systems in the local runtime. |

## Data Movement and Modeling Terms

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| OLTP systems | Used directly | The structured source is explicitly modeled as an OLTP-style operational system emitting CDC events. |
| Ingestion | Used directly | Structured and document ingestion are implemented in `src/caseware_poc/ingestion/`. |
| Normalization | Used directly | Silver transformations standardize and normalize fields into queryable snapshots. |
| ETL / ELT | Used directly | The pattern is effectively ELT: raw data lands first, then transforms into silver and gold inside the analytical layer. |
| Data contract | Represented conceptually | The code enforces stable entity fields and gold-table semantics, but there is no separate formal contract registry in the POC. |
| Schema versioning / event versioning | Represented conceptually | The repo preserves raw payloads and includes schema drift checks, but it does not implement explicit version numbers for schemas or events. |
| Replication | Represented conceptually | CDC ingestion copies data from simulated source systems into the platform, which models replication behavior without a live replicator service. |
| Event sourcing | Represented conceptually | Bronze stores changes as an append-only event stream, but the full application is not built as an event-sourced system. |
| CDC / change tracking | Used directly | The structured path models inserts, updates, deletes, duplicates, and late/out-of-order changes. |
| Historical reprocessing | Used directly | Bronze is replayable and the entire pipeline can be rebuilt from raw data by rerunning bootstrap/demo flows. |
| Indexing | Used directly | The vector path builds a retrieval index, and the docs explain indexing as part of the AI path. |
| Partitioning | Used directly (challenge artifact) | Iceberg and Spark files show partitioned bronze/gold tables in `sql/iceberg/medallion_tables.sql` and `jobs/spark/silver_to_gold.py`. |

## AI and LLM Terms

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| Embeddings | Used directly | `src/caseware_poc/rag/embedding.py` creates deterministic local embeddings for the vector path. |
| Vector retrieval | Used directly | `src/caseware_poc/rag/index.py` performs tenant-scoped vector retrieval over chunk embeddings. |
| RAG | Used directly | The document path is a tenant-safe RAG implementation with citations and retrieval filters. |
| Agentic systems | Used directly (challenge artifact) | `src/caseware_poc/agents/langgraph_workflow.py` models a multi-step agent workflow with route selection, tool use, synthesis, and guardrail enforcement. |
| LLM tooling / AI platform integration | Used directly (challenge artifact) | Bedrock, LangGraph, Langfuse, repo-native guardrails, and the LLM proxy deployment are all represented in the repository. |

## Governance and Security Terms

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| AI-ready data | Used directly | The whole project is framed around preparing structured and unstructured data for safe AI use. |
| Governed data access | Used directly | Query routes are tenant-scoped, exact data is forced through gold tables, and retrieval applies metadata filters before scoring. |
| Tenant-aware controls / tenant isolation | Used directly | Tenant isolation is enforced in ingestion, transforms, SQL serving, vector retrieval, and routing. |
| Data classification | Used directly | Documents carry `classification` metadata. |
| Retention | Used directly | Documents carry `retention_state` metadata and retrieval filters on active records. |
| Auditability | Used directly | Bronze replayability, lineage references, and event logs support auditability. |
| Safe reuse | Used directly | Gold data products and tenant-safe retrieval are designed for safe downstream reuse. |
| Operational guardrails | Used directly | The `precision_guardrail` route prevents document chunks from being used as exact financial truth. |

## Reliability and Observability Terms

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| Data quality | Used directly | Quality checks are materialized in `src/caseware_poc/transformations/lakehouse.py`. |
| Lineage | Used directly | Gold tables include `lineage_ref` values back to source events. |
| Traceability | Used directly | Outputs can be traced through source event IDs, batch IDs, and logs. |
| Data dictionary controls | Represented conceptually | The POC documents stable field meanings, but it does not implement a dedicated data dictionary service. |
| Freshness monitoring | Used directly | The quality report computes freshness metrics from `updated_at` and `emitted_at`. |
| Alerting | Used directly (challenge artifact) | `infra/cdk/stacks/observability_stack.py` creates a CloudWatch alarm for freshness lag. |
| Observability | Used directly | Structured JSON logs are produced for ingestion, quality checks, SQL, retrieval, and index builds. |

## AWS and Platform Tools

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| S3 | Used directly (challenge artifact) | CDK, Spark, and Iceberg code use S3-backed bronze/silver/gold locations. |
| S3 Express | Not used intentionally | Lower-latency S3 classes are production optimization details, not necessary for a local interview POC. |
| Athena | Used directly (challenge artifact) | `infra/cdk/stacks/data_platform_stack.py` provisions an Athena workgroup for governed analytics. |
| Glue Catalog | Used directly (challenge artifact) | CDK and integration code define Glue Catalog databases and Iceberg table registration. |
| Lake Formation | Used directly (challenge artifact) | CDK code registers S3 lakehouse resources for governed access. |
| OpenSearch Serverless | Used directly (challenge artifact) | CDK, index JSON, and integration code define a tenant-aware OpenSearch vector store. |
| S3 Vector Storage | Represented conceptually | The repo persists vectors locally and maps this to AWS vector storage options in production. |
| Iceberg | Used directly (challenge artifact) | Spark jobs and SQL DDL define Iceberg-backed bronze, silver, and gold tables. |
| Lambda | Represented conceptually | The repo uses scripts and a local API; Lambda is part of the production orchestration mapping. |
| Step Functions | Represented conceptually | Workflow sequencing is local, with Step Functions described for production orchestration. |
| EKS | Used directly (challenge artifact) | CDK and Kubernetes values files model EKS-hosted Trino and observability components. |
| EMR / EMR Serverless | Used directly (challenge artifact) | CDK creates EMR Serverless application scaffolding and Spark jobs target that runtime. |

## Processing Frameworks

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| Spark | Used directly (challenge artifact) | `jobs/spark/` contains PySpark jobs for Kafka-to-Iceberg bronze and medallion transformations. |
| Trino | Used directly (challenge artifact) | Trino client code and serving SQL are part of the challenge stack. |
| MapReduce | Not used intentionally | It is historically relevant but not necessary to demonstrate the target architecture for this challenge. |

## Databases and Messaging Tools

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| MongoDB | Used directly (challenge artifact) | `docker/mongo/init/*`, `docker/connectors/mongodb-documents.json`, and `src/caseware_poc/integrations/mongo_document_source.py` model MongoDB as a document-heavy source system. |
| Amazon DocumentDB | Not used intentionally | MongoDB plus CDK-backed platform artifacts were enough to demonstrate document-source depth without adding a weaker interview signal. |
| MS SQL Server | Represented conceptually | The source system could be MS SQL Server in a real environment, but the POC simulates the source instead of connecting to one. |
| DynamoDB | Not used intentionally | No key-value operational store was needed for the core challenge. |
| Redis / Valkey | Not used intentionally | Caching and ephemeral state were not necessary for the local interview build. |
| SNS | Not used intentionally | There is no asynchronous production event fan-out requirement in this challenge POC. |
| SQS | Not used intentionally | Queueing is not necessary for the single-process reference implementation. |
| Kafka / Pub/Sub | Used directly (challenge artifact) | MSK/CDK scaffolding, Kafka consumer code, and Spark Structured Streaming jobs are included. |
| Aurora PostgreSQL | Used directly (challenge artifact) | CDK and connector code model Aurora PostgreSQL as a relational/vector backing store. |
| pgvector | Used directly (challenge artifact) | PostgreSQL schema, connector code, and vector-search patterns are included. |

## AI Platform and Agent Tools

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| AWS Bedrock | Used directly (challenge artifact) | Bedrock runtime wrapper and CDK Bedrock resources are included in code. |
| AWS AgentCore | Represented conceptually | The repo models agent runtime concepts directly in LangGraph and guardrail code instead of adding an AgentCore-specific implementation. |
| LangGraph | Used directly (challenge artifact) | The repo now includes a LangGraph workflow that ties guardrail skills, Trino, OpenSearch, Bedrock, and Langfuse together. |
| Langfuse | Used directly (challenge artifact) | A Langfuse tracer wrapper and Kubernetes values are included. |
| MCP | Represented conceptually | The skill-and-tool idea aligns with MCP-style context and tool connectivity, but the POC does not implement an MCP server. |
| LaunchDarkly | Not used intentionally | Feature flagging is useful for controlled rollout, but not required to prove the platform architecture. |
| AWS Knowledge Bases | Used directly (challenge artifact) | `infra/cdk/stacks/ai_platform_stack.py` defines a Bedrock Knowledge Base and S3 data source. |
| AWS Textract | Represented conceptually | The hard OCR-like document simulates the kind of document that Textract would help extract in production. |
| LLM proxy layer | Used directly (challenge artifact) | The LangGraph workflow plus guardrail assets model a central policy and tool-routing layer. |

## DevOps and Operations

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| CI/CD pipelines | Represented conceptually | The repo has tests and infra code, but no hosted CI/CD workflow file was added yet. |
| Infrastructure as code | Used directly (challenge artifact) | The CDK application and constructs under `infra/cdk/` are infrastructure-as-code artifacts. |
| CloudWatch | Used directly (challenge artifact) | CDK defines CloudWatch log groups and the repo includes EMF metric rendering. |
| New Relic | Used directly (challenge artifact) | EKS values and config helpers show how New Relic would be wired into the stack. |
| OpenTelemetry | Represented conceptually | The observability design is compatible with OpenTelemetry-style traces and metrics, but the POC uses a simpler local logger. |

## Why Some Terms Were Not Implemented

The main reason some terms were not used directly is scope discipline.

This repository is supposed to prove hands-on depth in:

- CDC and ingestion
- medallion lakehouse modeling
- SQL vs RAG separation
- tenant isolation
- quality and observability
- production trade-off thinking

If the repo had tried to stand up every AWS service, streaming broker, database type, and LLM orchestration framework named in the broader ecosystem, it would have become less credible as a focused interview exercise. The local build therefore implements the core architecture directly and documents the rest as production mappings or intentional omissions.

## Best Interview Framing

If asked whether a specific term was “used,” the strongest answer is:

1. Say whether it was implemented directly, represented conceptually, or intentionally not used.
2. Explain why that choice was appropriate for a small but production-shaped POC.
3. Show where the production mapping is documented if it was not implemented locally.

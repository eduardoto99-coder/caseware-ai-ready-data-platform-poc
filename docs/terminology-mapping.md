# Terminology Mapping

This document answers a specific interview question: which platform, data, AI, governance, AWS, and operations terms were actually used in this POC, and which ones were intentionally left out.

Status meanings:

- `Used directly`: implemented in the local code or runtime behavior
- `Represented conceptually`: not deployed as the named product/service, but the POC models the idea or documents how it maps to production
- `Not used intentionally`: left out to keep the reference implementation small, runnable, and focused on the core problem

## Architecture and Data Platform Terms

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| Lakehouse | Used directly | The repo uses a local lakehouse pattern with Parquet-backed bronze, silver, and gold layers described in [architecture.md](./architecture.md) and implemented in `src/caseware_poc/transformations/lakehouse.py`. |
| Warehouse pattern | Represented conceptually | The DuckDB gold-serving layer acts like a lightweight warehouse pattern for governed business queries, but the repo does not stand up a separate warehouse product. |
| Medallion architecture | Used directly | Bronze, silver, and gold layers are core to the implementation and are explicitly documented and materialized. |
| Data product | Used directly | `gold_invoice_summary`, `gold_engagement_status`, and `gold_control_exceptions` are treated as governed data products with stable semantics and lineage. |
| Interoperability | Represented conceptually | The POC is local, but it emphasizes clean data contracts, tenant-safe APIs, and production mapping for secure interoperability with downstream AI or customer systems. |

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
| Partitioning | Represented conceptually | Tenant and batch boundaries exist, but physical Parquet partitioning by tenant/date was intentionally not added to keep the POC compact. |

## AI and LLM Terms

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| Embeddings | Used directly | `src/caseware_poc/rag/embedding.py` creates deterministic local embeddings for the vector path. |
| Vector retrieval | Used directly | `src/caseware_poc/rag/index.py` performs tenant-scoped vector retrieval over chunk embeddings. |
| RAG | Used directly | The document path is a tenant-safe RAG implementation with citations and retrieval filters. |
| Agentic systems | Represented conceptually | The serving layer is rules-based rather than a full autonomous agent, but it models agent-facing routing, skill selection, and tool choice. |
| LLM tooling / AI platform integration | Represented conceptually | The repo deliberately avoids external model dependencies, but the routing, chunking, retrieval, and production mapping documents the broader AI platform integration story. |

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
| Alerting | Not used intentionally | The POC records the signals that would drive alerting, but it does not wire a notification system because there is no long-running scheduler in the local build. |
| Observability | Used directly | Structured JSON logs are produced for ingestion, quality checks, SQL, retrieval, and index builds. |

## AWS and Platform Tools

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| S3 | Represented conceptually | Local Parquet files stand in for S3 and the mapping is documented in [aws-production-mapping.md](./aws-production-mapping.md). |
| S3 Express | Not used intentionally | Lower-latency S3 classes are production optimization details, not necessary for a local interview POC. |
| Athena | Represented conceptually | DuckDB plays the role of serverless SQL over lakehouse-style data for the local build. |
| Glue Catalog | Represented conceptually | Table metadata is local in the POC, with Glue Catalog described as the production metadata layer. |
| Lake Formation | Represented conceptually | Governance is enforced in code and docs locally; Lake Formation is discussed as the production governance control plane. |
| OpenSearch Serverless | Represented conceptually | The local vector index stands in for a managed vector/search backend. |
| S3 Vector Storage | Represented conceptually | The repo persists vectors locally and maps this to AWS vector storage options in production. |
| Iceberg | Represented conceptually | The POC uses Parquet only; Iceberg is documented as the production table format for schema evolution and snapshots. |
| Lambda | Represented conceptually | The repo uses scripts and a local API; Lambda is part of the production orchestration mapping. |
| Step Functions | Represented conceptually | Workflow sequencing is local, with Step Functions described for production orchestration. |
| EKS | Not used intentionally | Container orchestration would be excessive for a local reference implementation of this size. |
| EMR / EMR Serverless | Represented conceptually | Local transforms stand in for Spark-style processing, with EMR discussed as the production runtime. |

## Processing Frameworks

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| Spark | Represented conceptually | The transformation logic is written so it can map cleanly to Spark, but the local POC uses DuckDB/Python for simplicity and reproducibility. |
| Trino | Represented conceptually | DuckDB serves the same broad analytical-query purpose locally, while Trino is discussed as a production option. |
| MapReduce | Not used intentionally | It is historically relevant but not necessary to demonstrate the target architecture for this challenge. |

## Databases and Messaging Tools

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| MongoDB | Not used intentionally | The challenge did not require a document application database; document ingestion is file-backed in this POC. |
| Amazon DocumentDB | Not used intentionally | Same reason as MongoDB; not required to demonstrate the core platform slice. |
| MS SQL Server | Represented conceptually | The source system could be MS SQL Server in a real environment, but the POC simulates the source instead of connecting to one. |
| DynamoDB | Not used intentionally | No key-value operational store was needed for the core challenge. |
| Redis / Valkey | Not used intentionally | Caching and ephemeral state were not necessary for the local interview build. |
| SNS | Not used intentionally | There is no asynchronous production event fan-out requirement in the local POC. |
| SQS | Not used intentionally | Queueing is not necessary for the single-process reference implementation. |
| Kafka / Pub/Sub | Represented conceptually | The CDC event stream models streaming/event thinking, but the POC uses microbatches instead of a real broker. |
| Aurora PostgreSQL | Represented conceptually | A production serving layer could use Aurora PostgreSQL, but the local POC keeps all exact querying in DuckDB. |
| pgvector | Represented conceptually | The local vector index serves the same retrieval role without adding a relational vector store. |

## AI Platform and Agent Tools

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| AWS Bedrock | Represented conceptually | The repo avoids managed-model dependencies, but Bedrock is identified as the production model/embedding platform. |
| AWS AgentCore | Represented conceptually | The POC has skill and routing concepts, while AgentCore is part of the documented production evolution. |
| LangGraph | Represented conceptually | Query orchestration is deliberately simpler than LangGraph, but the production docs call it out as a natural next step. |
| Langfuse | Represented conceptually | The repo logs retrieval and routing signals locally, while Langfuse is a plausible production observability/evaluation layer. |
| MCP | Represented conceptually | The skill-and-tool idea aligns with MCP-style context and tool connectivity, but the POC does not implement an MCP server. |
| LaunchDarkly | Not used intentionally | Feature flagging is useful for controlled rollout, but not required to prove the platform architecture. |
| AWS Knowledge Bases | Represented conceptually | The local RAG path stands in for managed retrieval infrastructure. |
| AWS Textract | Represented conceptually | The hard OCR-like document simulates the kind of document that Textract would help extract in production. |
| LLM proxy layer | Represented conceptually | The routing layer plays a lightweight proxy role for policy, logging, and path selection, but not a full model gateway. |

## DevOps and Operations

| Term | Status | How it appears in this POC |
| --- | --- | --- |
| CI/CD pipelines | Represented conceptually | The repo has tests and clean commands, but no hosted CI/CD workflow file was added yet. |
| Infrastructure as code | Not used intentionally | This build stays local and code-centric; IaC would be added if the next step were a deployable AWS reference environment. |
| CloudWatch | Represented conceptually | Local JSON logs map naturally to CloudWatch in the production design. |
| New Relic | Not used intentionally | The challenge did not require a third-party APM platform, and CloudWatch/OpenTelemetry are the more natural AWS-aligned mapping. |
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

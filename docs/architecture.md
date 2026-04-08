# Architecture

## 1. Problem Statement

The platform must support two different classes of AI-facing workloads for a multi-tenant accounting and audit SaaS product:

1. Structured operational and financial data that must remain exact, aggregatable, and lineage-aware
2. Unstructured audit artifacts that benefit from semantic retrieval and grounded narrative answers

The design challenge is not just ingestion or retrieval in isolation. It is the end-to-end control plane required to make both paths safe and useful in the same system: replayable ingestion, bronze/silver/gold shaping, tenant isolation, exact-vs-semantic query routing, and observability.

## 2. Scope and Assumptions

This POC optimizes for clarity and runnable depth rather than infrastructure breadth.

- The structured source is simulated as CDC-style JSONL batches containing inserts, updates, deletes, duplicates, and late/out-of-order events.
- The document source is simulated as policy, workpaper, note, and issue-summary records.
- Local Parquet files stand in for a lakehouse landing zone.
- DuckDB stands in for the analytical serving engine.
- The vector path uses a deterministic local embedding adapter to keep the repository runnable without external credentials.
- The serving layer is a thin rules-based interface rather than a full LLM agent runtime. The key design goal is the routing discipline, not generative polish.
- The repository also includes a production-shaped reference layer with CDK, Spark, Kafka, Iceberg, Trino, Aurora PostgreSQL/pgvector, OpenSearch, Bedrock, LangGraph, Langfuse, EKS, CloudWatch, and New Relic code so the stack aligns more closely with the target role.
- Repo-native LLM safety policy lives in `guardrails/` and is consumed by both the local runtime and the production-shaped agent path.

## 3. End-to-End Data Flow

### Structured path

1. Sample CDC batches are generated with `tenant_id`, `entity_id`, `updated_at`, `emitted_at`, and `source_sequence`.
2. Bronze ingestion writes immutable batch Parquet files.
3. Bronze preserves both the inferred payload object and a raw `payload_json` string for replayability and schema resilience.
4. Silver deduplicates on `event_id`, reconciles out-of-order changes by `(updated_at, source_sequence, emitted_at)`, and produces latest-entity snapshots.
5. Gold creates curated business tables that are ready for exact SQL and agent/tool usage.

### Unstructured path

1. Documents are landed into a bronze document table.
2. The chunker normalizes OCR text, detects table-like sections, and uses overlap only for narrative sections.
3. Chunks are embedded and stored in a shared vector index with chunk metadata.
4. Retrieval enforces tenant and retention filters before similarity scoring.
5. Answers are assembled from retrieved chunks with citations and logs.

### Serving path

1. The router inspects the question.
2. Exact-value questions route to the SQL skill.
3. Narrative questions route to the RAG skill.
4. Mixed questions trigger a precision guardrail flow: SQL answers exact values and RAG supplies contextual evidence only.

### Production reference path

In addition to the runnable local flow, the repository now includes:

1. CDK infrastructure code for S3, Glue Catalog, Lake Formation, EMR Serverless, MSK, Aurora PostgreSQL/pgvector, OpenSearch Serverless, EKS, CloudWatch, Bedrock roles, Langfuse secrets, and New Relic secrets
2. Spark jobs for Kafka-to-Iceberg bronze ingestion and bronze-to-silver-to-gold transforms
3. Trino SQL DDL and serving views
4. Integration code for Trino, Postgres/pgvector, OpenSearch, Bedrock, Kafka, and Glue
5. LangGraph agent orchestration with repo-native guardrail skills, rules, templates, and enforcement code for hallucination control and context management

## 4. Bronze, Silver, Gold Design

### Bronze

Bronze is raw, append-only, and replayable.

- Stores source payloads without enforcing business semantics
- Retains batch identity and source file metadata
- Preserves `payload_json` explicitly to avoid brittle downstream coupling to inferred nested schemas

This is important because replayability is not optional in a production data platform. When logic changes, bronze needs to be trustworthy enough to rebuild silver and gold without reaching back into OLTP systems.

### Silver

Silver is where operational rawness becomes governed data.

- Deduplicates repeated `event_id` values
- Reconciles late and out-of-order events using business timestamps and source sequence
- Produces entity snapshots for invoices, customers, engagements, controls, and journal entries
- Carries forward lineage references to the winning source event

This is also the right place for quality checks and normalization because downstream consumers should not need to understand CDC edge cases.

### Gold

Gold is intentionally opinionated.

- `gold_invoice_summary`
- `gold_engagement_status`
- `gold_control_exceptions`

These tables favor stable business definitions over source-system fidelity. Each row includes lineage references back to the source events that shaped it.

## 5. RAG Design

### Chunking strategy

- Narrative sections use paragraph-first chunking with overlap to preserve local context.
- OCR and table-like fragments are kept intact because splitting inside a table can destroy meaning.
- The chunker preserves the hard example in the dataset: a workpaper with OCR-like spacing and table content.

### Why overlap is selective

Narrative sections benefit from overlap because policy explanations often spill across paragraphs. Table fragments do not; overlap across table rows usually lowers retrieval quality and makes citations harder to interpret.

### When not to use embeddings

The platform deliberately does not use embeddings for exact balances, counts, invoice state, or aggregations. Those live in gold tables and are served through SQL. Documents are for explanation, policy, workpaper context, and issue narratives. This is the key architectural boundary in the system.

## 6. Tenant Isolation

Tenant isolation is enforced across every stage:

- Source events and documents include `tenant_id`
- Silver and gold tables retain `tenant_id`
- SQL serving always parameterizes by `tenant_id`
- Vector retrieval filters by `tenant_id` before scoring
- Guardrail responses never retrieve globally and filter later

The shared vector index is acceptable in the POC because metadata filtering is enforced ahead of ranking. In production, the trade-off between shared and per-tenant indexes depends on scale, noisy-neighbor risk, governance complexity, and operational cost.

## 7. Quality, Lineage, and Observability

The POC includes:

- Schema drift checks against expected bronze columns
- Duplicate-event detection
- Freshness measurements using `updated_at` versus `emitted_at`
- Completeness checks for key gold-table attributes
- Lineage references from gold back to source events
- JSON logging for ingestion, indexing, SQL serving, RAG retrieval, and quality runs

For the AI path, the logs record:

- tenant filter used
- retrieved chunk IDs
- attribution URIs
- retrieval latency

## 8. Trade-Offs

### Microbatch vs true streaming

Microbatching is the right choice for this exercise. It still demonstrates incremental ingestion, replayability, and late-data handling without introducing the operational overhead of a streaming runtime. For 15 to 30 minute SLAs, this is often the more pragmatic production choice as well.

### Shared vector index vs per-tenant index

The POC uses a shared index with mandatory metadata filtering because it is easier to operate locally and still demonstrates tenant-safe retrieval. At larger scale or under stricter isolation requirements, per-tenant indexes may become preferable.

### Local deterministic embeddings vs managed embedding service

The local embedding adapter keeps the repo reproducible and testable. In production, this would likely be replaced with Bedrock Titan embeddings, OpenAI embeddings, or another managed provider with stronger semantic performance and centralized governance.

### DuckDB vs distributed engines

DuckDB is intentionally small and transparent. The production mapping moves the same data contracts to S3, Iceberg, Glue, Lake Formation, and EMR/Serverless compute where scale or team workflow requires it.

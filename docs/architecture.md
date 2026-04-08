# Architecture

## 1. Problem Statement

The platform must support two different classes of AI-facing workloads for a multi-tenant accounting and audit SaaS product:

1. Structured operational and financial data that must remain exact, aggregatable, and lineage-aware
2. Unstructured audit artifacts that benefit from semantic retrieval and grounded narrative answers

The design challenge is not just ingestion or retrieval in isolation. It is the end-to-end control plane required to make both paths safe and useful in the same system: replayable ingestion, bronze/silver/gold shaping, tenant isolation, exact-vs-semantic query routing, and observability.

## 2. Scope and Assumptions

This POC optimizes for production-shaped clarity rather than deployability.

- The structured source is simulated as CDC-style JSONL batches containing inserts, updates, deletes, duplicates, and late/out-of-order events.
- The document source is simulated as policy, workpaper, note, and issue-summary records.
- The repository uses production-style boundaries and service names even when some components are simulated or locally substituted for demo purposes.
- Parquet and DuckDB exist to keep the POC inspectable and runnable without provisioning cloud resources, but the architecture is still expressed as S3, Iceberg, Spark, Trino, OpenSearch, pgvector, Bedrock, and LangGraph.
- Repo-native LLM safety policy lives in `guardrails/` and is consumed by both the runtime services and the agent orchestration layer.
- Dockerized PostgreSQL and MongoDB sources exist for walkthroughs where showing concrete OLTP systems and CDC plumbing is more valuable than keeping the demo purely file-backed.

## 3. End-to-End Data Flow

### Structured path

1. The challenge models structured ingestion as CDC flowing from PostgreSQL OLTP systems into Kafka/MSK topics.
2. Bronze lands raw events into Iceberg-shaped bronze tables on S3.
3. Bronze preserves the raw payload and `payload_json` for replayability and schema resilience.
4. Spark-shaped transforms deduplicate on `event_id`, reconcile out-of-order changes by `(updated_at, source_sequence, emitted_at)`, and produce latest-entity silver snapshots.
5. Gold creates curated business tables ready for exact SQL and agent/tool usage through Trino.

### Unstructured path

1. Documents are modeled as coming from a document-heavy source such as MongoDB, with metadata required for tenant-aware retrieval.
2. The chunker normalizes OCR text, detects table-like sections, and uses overlap only for narrative sections.
3. Chunks are embedded and modeled for OpenSearch Serverless or Aurora PostgreSQL with pgvector.
4. Retrieval enforces tenant and retention filters before similarity scoring.
5. Answers are assembled from retrieved chunks with citations, warnings, and observability events.

### Serving path

1. The router inspects the question.
2. Exact-value questions route to the SQL skill backed by gold products.
3. Narrative questions route to the RAG skill backed by tenant-scoped retrieval.
4. Mixed questions trigger a precision guardrail flow: SQL answers exact values and RAG supplies contextual evidence only.
5. LangGraph and Bedrock are represented for the multi-step agent layer, while the local API keeps the same contracts visible for the demo.

The repository expresses that architecture through:

1. CDK infrastructure code for S3, Glue Catalog, Lake Formation, EMR Serverless, MSK, Aurora PostgreSQL/pgvector, OpenSearch Serverless, EKS, CloudWatch, Bedrock resources, Langfuse secrets, and New Relic secrets
2. Docker demo assets for PostgreSQL, MongoDB, Kafka, Debezium/Kafka Connect, and OpenSearch
3. Spark jobs for Kafka-to-Iceberg bronze ingestion and bronze-to-silver-to-gold transforms
4. Trino SQL DDL and serving views
5. Integration code for Trino, Postgres/pgvector, MongoDB, OpenSearch, Debezium/Kafka Connect, Bedrock, Kafka, and Glue
6. LangGraph agent orchestration with repo-native guardrail skills, rules, templates, and enforcement code for hallucination control and context management

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

The POC uses a shared index with mandatory metadata filtering because it keeps the challenge compact while still demonstrating tenant-safe retrieval. At larger scale or under stricter isolation requirements, per-tenant indexes may become preferable.

### Demo-friendly adapters vs managed services

Some repository components use lightweight adapters so the code can be inspected and exercised without real cloud provisioning. That does not change the architecture. It only changes how the POC is demonstrated.

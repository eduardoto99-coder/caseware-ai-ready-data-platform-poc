# Caseware AI-Ready Data Platform POC

A production-shaped POC for a multi-tenant accounting and audit data platform. The goal is not to provide a fully deployable cloud environment. The goal is to present one coherent architecture for the challenge, with real-looking code for the layers and tools the role cares about: Spark, Kafka, Trino, Iceberg, S3, Glue Catalog, Lake Formation, EMR, OpenSearch, Aurora PostgreSQL/pgvector, EKS, Bedrock, LangGraph, Langfuse, CloudWatch, New Relic, and AWS CDK.

Where the repository uses lightweight stand-ins such as DuckDB or deterministic local embeddings, those are implementation shortcuts inside the same architecture, not a second architecture.

## What It Demonstrates

- Incremental structured ingestion with replayable bronze landing files
- Late-arriving and duplicate event handling in silver transformations
- Curated gold tables for exact financial and operational questions
- Chunking and vector indexing for policies, workpapers, notes, and issue summaries
- Tenant isolation across storage, transforms, retrieval, and serving
- Agent-facing routing that keeps exact numbers in SQL and narrative context in RAG
- Repo-native guardrail skills, rules, contracts, and templates for LLM safety and context management
- Data quality checks, lineage references, and structured JSON observability
- Production-shaped code and infrastructure artifacts for the stack named in the challenge

## Architecture

```mermaid
flowchart LR
    A["OLTP CDC events via Kafka/MSK"] --> B["Bronze Iceberg tables on S3"]
    D["Audit and policy documents"] --> E["Document landing plus metadata"]
    B --> C["Spark bronze to silver normalization"]
    C --> F["Gold Iceberg data products served through Trino"]
    E --> G["Chunking plus embeddings plus OpenSearch or pgvector retrieval"]
    F --> H["Exact Accounting SQL skill"]
    G --> I["Tenant-Safe Policy RAG skill"]
    H --> J["LangGraph routing plus guardrails"]
    I --> J
    J --> K["Grounded response with citations, warnings, and observability"]
```

## Repo Layout

```text
docs/
  architecture.md
  aws-production-mapping.md
  challenge-coverage.md
  interview-walkthrough.md
  llm-guardrails.md
  production-reference-stack.md
  skills-and-rules.md
  terminology-mapping.md
guardrails/
  context/
  rules/
  skills/
  templates/
infra/
  cdk/
  k8s/
jobs/
  spark/
sql/
  iceberg/
  opensearch/
  postgres/
  trino/
scripts/
  run_demo.py
  serve_api.py
src/caseware_poc/
  agents/
  common/
  guardrails/
  ingestion/
  integrations/
  observability/
  production/
  rag/
  serving/
  transformations/
  app.py
  platform.py
tests/
```

## Quickstart

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
python scripts/run_demo.py
pytest
python scripts/serve_api.py
```

Optional dependencies for the production-shaped stack artifacts:

```bash
pip install -e '.[reference]'
```

API endpoints:

- `GET /health`
- `POST /bootstrap`
- `POST /query`
- `GET /guardrails`

Example query payload:

```json
{
  "tenant_id": "tenant_alpha",
  "question": "What is the total invoice amount overdue for tenant alpha this month?"
}
```

## Core Design Choices

- Structured accounting data stays in SQL-backed gold tables. It is never treated as an embedding-first problem.
- Documents are chunked and indexed for semantic retrieval, but tenant filters are applied before scoring.
- Bronze preserves raw payloads plus `payload_json` so silver can evolve independently from JSON schema inference quirks.
- The vector path can be demonstrated locally with deterministic embeddings, but the architecture and interfaces are shaped for OpenSearch or pgvector.
- Mixed questions trigger a guardrail flow: SQL owns exact values, documents only provide context.
- The repository uses production-shaped service boundaries even when some components are demo-friendly stand-ins.

## Demo Questions

- `What is the total invoice amount overdue for tenant alpha this month?`
- `What does tenant alpha's revenue recognition policy say about deferred revenue?`
- `What does the OCR workpaper table say about onboarding services and what exact amount is overdue?`
- `Which controls have exceptions for tenant beta?`
- `What does tenant beta's deferred revenue policy say about implementation fees?`

## Verification

- `pytest` covers routing, chunking, bootstrap, SQL, RAG, and guardrail behavior
- `scripts/run_demo.py` resets the environment, rebuilds the full platform slice, and runs the example questions end to end

## Documentation

- [Architecture](docs/architecture.md)
- [Challenge Coverage](docs/challenge-coverage.md)
- [LLM Guardrails](docs/llm-guardrails.md)
- [Production Reference Stack](docs/production-reference-stack.md)
- [Skills and Rules](docs/skills-and-rules.md)
- [Terminology Mapping](docs/terminology-mapping.md)
- [AWS Production Mapping](docs/aws-production-mapping.md)
- [Interview Walkthrough](docs/interview-walkthrough.md)

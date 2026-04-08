# AI-Ready Data Platform POC

This repo is the solution I would walk through for a multi-tenant accounting and audit data platform challenge. It is meant to look like the kind of system I would build for the role, but it is not meant to be deployed as-is.

## What The POC Covers

- Structured data path: PostgreSQL OLTP -> Debezium / Kafka Connect -> Kafka -> Spark -> Iceberg on S3 with Glue Catalog / Lake Formation -> Trino and Athena for governed querying.
- Unstructured data path: MongoDB documents -> chunking for narrative text and OCR/table-like text -> OpenSearch Serverless or Aurora PostgreSQL with pgvector -> Bedrock for grounded synthesis.
- Agent path: route exact questions to SQL, narrative questions to retrieval, and mixed questions to a guardrail path where SQL owns the exact answer and documents only provide context.
- Platform concerns: tenant isolation, lineage, retention, citation-first answers, observability, and CDK / EKS infrastructure artifacts.

## How It Is Organized

### Source systems and ingestion

- `docker/compose.yaml`
Local source-system story for PostgreSQL, MongoDB, Kafka, Debezium/Kafka Connect, and OpenSearch.
- `docker/postgres/init/001_caseware_oltp.sql`
OLTP schema plus CDC publication setup.
- `docker/mongo/init/001_seed_documents.js`
Example document records with tenant metadata, classification, and retention state.
- `docker/connectors/postgres-cdc.json`
Debezium PostgreSQL connector config.
- `docker/connectors/mongodb-documents.json`
Debezium MongoDB connector config.
- `src/caseware_poc/integrations/debezium_connect.py`
Small Kafka Connect client for registering or checking connectors.
- `src/caseware_poc/integrations/kafka_cdc_consumer.py`
CDC microbatch consumer shape.
- `src/caseware_poc/integrations/mongo_document_source.py`
MongoDB document-source integration.

### Lakehouse and serving

- `jobs/spark/cdc_to_bronze.py`
Kafka to Iceberg bronze ingestion.
- `jobs/spark/bronze_to_silver.py`
Silver snapshot build with duplicate cleanup and late/out-of-order reconciliation.
- `jobs/spark/silver_to_gold.py`
Gold invoice product build with lineage references.
- `sql/iceberg/medallion_tables.sql`
Bronze, silver, and gold Iceberg table definitions.
- `sql/trino/gold_serving_views.sql`
Trino views over gold products.
- `src/caseware_poc/integrations/trino_client.py`
Trino client used for exact answers.

### Retrieval and AI

- `src/caseware_poc/rag/chunking.py`
Chunking logic for narrative text and OCR/table-like fragments.
- `sql/opensearch/tenant_audit_documents_index.json`
OpenSearch index definition for tenant-aware retrieval.
- `sql/postgres/init_pgvector.sql`
PostgreSQL / pgvector schema and indexing.
- `src/caseware_poc/integrations/opensearch_vector_store.py`
OpenSearch retrieval client.
- `src/caseware_poc/integrations/postgres_pgvector.py`
pgvector store for the alternative vector path.
- `src/caseware_poc/integrations/bedrock_runtime.py`
Bedrock answer-synthesis wrapper.

### Guardrails and orchestration

- `guardrails/skills/*.md`
Human-readable skill files describing when SQL, RAG, or the mixed guardrail path should be used.
- `guardrails/rules/*.md`
Rule files for routing, retrieval, response behavior, tenant isolation, tooling, and context budget.
- `guardrails/contracts/answer_contracts.yaml`
Structured answer-shape expectations per route.
- `guardrails/templates/response_contract.txt`
Response contract injected into the agent prompt.
- `guardrails/templates/trino_overdue_query.sql`
Example exact query template.
- `src/caseware_poc/guardrails/registry.py`
Loader for the guardrail files.
- `src/caseware_poc/serving/router.py`
Keyword-based route selection.
- `src/caseware_poc/agents/langgraph_workflow.py`
LangGraph workflow showing tenant validation, route selection, retrieval, synthesis, and final guardrail checks.
- `src/caseware_poc/agents/guardrails.py`
Small guardrail functions for tenant checks, citation minimums, SQL-first exactness, and context budgeting.

### Observability and infrastructure

- `src/caseware_poc/observability/cloudwatch_metrics.py`
CloudWatch metric emission shape.
- `src/caseware_poc/observability/langfuse_tracer.py`
Langfuse tracing wrapper.
- `src/caseware_poc/observability/newrelic_monitoring.py`
New Relic integration shape.
- `infra/cdk/`
CDK stacks for the data platform, AI platform, and observability layers.
- `infra/k8s/`
Kubernetes manifests and Helm values for Trino, Langfuse, New Relic, OpenSearch setup, Spark operator, and the LLM proxy.

## Main Technology Choices

The repo uses the tools that matter most for the challenge: PostgreSQL, MongoDB, Debezium, Kafka, Spark, S3, Glue Catalog, Lake Formation, Iceberg, Trino, Athena, OpenSearch Serverless, Aurora PostgreSQL, pgvector, Bedrock, LangGraph, Langfuse, CloudWatch, New Relic, EKS, CDK, and Docker.

I did not try to squeeze in every adjacent AWS service. DocumentDB, DynamoDB, Redis, SNS, SQS, LaunchDarkly, AgentCore, Textract, Step Functions, Lambda, OpenTelemetry, and S3 Vector Storage are either outside the core architecture boundary or would broaden the repo without making the challenge answer stronger.

## AI Delivery Files

To make the repo usable with agent-driven workflows, it also includes:

- `AGENTS.md` for Codex-style repository instructions
- `CLAUDE.md` for Claude Code memory
- `.claude/commands/*.md` for Claude Code slash-command workflows

These files are there for AI delivery and review workflows. The runtime guardrail behavior still comes from the files under `guardrails/`.

## Suggested Walkthrough

1. `README.md`
2. `docker/postgres/init/001_caseware_oltp.sql`
3. `docker/connectors/postgres-cdc.json`
4. `jobs/spark/cdc_to_bronze.py`
5. `jobs/spark/bronze_to_silver.py`
6. `sql/iceberg/medallion_tables.sql`
7. `sql/trino/gold_serving_views.sql`
8. `src/caseware_poc/rag/chunking.py`
9. `src/caseware_poc/integrations/opensearch_vector_store.py`
10. `src/caseware_poc/serving/router.py`
11. `guardrails/skills/exact_accounting_sql.md`
12. `guardrails/rules/tooling.md`
13. `src/caseware_poc/agents/langgraph_workflow.py`
14. `infra/cdk/stacks/data_platform_stack.py`
15. `infra/cdk/stacks/ai_platform_stack.py`
16. `infra/cdk/stacks/observability_stack.py`

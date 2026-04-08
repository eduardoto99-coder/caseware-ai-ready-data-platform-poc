# Production Reference Stack

This repository now has a second track beyond the local runnable POC: a production-shaped reference layer that uses the technologies emphasized by the target role.

The intent is not that every file here is runnable in the current local environment. The intent is that you can show real-looking, system-shaped code for the stack a production team would actually discuss.

## Design Principle

The repo is intentionally split into:

- `local runnable path`
- `production reference path`

The local path proves the architecture works end to end.

The production reference path proves you understand the real stack and how the system would evolve using the technologies named in the role.

## Production Reference Directories

### `infra/cdk/`

AWS CDK reference app and stacks.

- `app.py`
  CDK entrypoint
- `stacks/data_platform_stack.py`
  S3, Glue Catalog, Athena, EMR Serverless, Kafka/MSK Serverless, Aurora PostgreSQL, and EKS
- `stacks/ai_platform_stack.py`
  OpenSearch Serverless, Bedrock Knowledge Base resources, and ECR for the LLM proxy
- `stacks/observability_stack.py`
  CloudWatch dashboards/log groups and secrets for New Relic and Langfuse

### `infra/k8s/`

Reference Kubernetes and Helm-style values for EKS-hosted platform services.

- `trino/values.yaml`
- `langfuse/values.yaml`
- `newrelic/values.yaml`
- `opensearch/index-management.yaml`
- `llm-proxy-deployment.yaml`

### `jobs/spark/`

Spark/Iceberg jobs for the production reference path.

- `cdc_to_bronze.py`
  Kafka CDC -> Iceberg bronze
- `bronze_to_silver.py`
  bronze CDC -> silver normalized snapshots
- `silver_to_gold.py`
  silver snapshots -> gold business data products

These files show Spark, Iceberg, Glue Catalog, and S3-oriented job logic directly in code.

### `src/caseware_poc/production/`

This directory is intentionally small.

- `reference_architecture.py`
  narrative model of the dual-track design, used to explain the relationship between the runnable local path and the production reference path

### `sql/`

Production-facing DDL and serving SQL.

- `sql/iceberg/medallion_tables.sql`
  Iceberg DDL for bronze/silver/gold
- `sql/trino/gold_serving_views.sql`
  Trino serving views
- `sql/postgres/init_pgvector.sql`
  PostgreSQL/pgvector schema and indices
- `sql/opensearch/tenant_audit_documents_index.json`
  OpenSearch index definition

### `src/caseware_poc/integrations/`

Connectors that model the production runtime.

- `trino_client.py`
- `postgres_pgvector.py`
- `opensearch_vector_store.py`
- `kafka_cdc_consumer.py`
- `glue_catalog.py`
- `bedrock_runtime.py`

These are the files you would walk through when someone asks, “How would this actually query Trino?” or “How would you use pgvector or OpenSearch?”

### `src/caseware_poc/agents/`

Production-shaped agent orchestration and LLM guardrails.

- `prompt_loader.py`
  loads repo-native guardrail assets
- `guardrails.py`
  tenant, citation, numeric-authority, and context-budget checks
- `langgraph_workflow.py`
  LangGraph orchestration tying Trino, OpenSearch, Bedrock, and Langfuse together

### `src/caseware_poc/observability/`

Observability integrations for the production path.

- `langfuse_tracer.py`
- `cloudwatch_metrics.py`
- `newrelic_monitoring.py`

### `guardrails/`

This is the answer to the “skills and rules” requirement in the way you intended it.

- `context/`
  global system instructions
- `skills/`
  role-specific LLM skill contracts
- `rules/`
  hard routing, retrieval, response, tenant, tooling, and context-budget policies
- `contracts/`
  required response shapes
- `templates/`
  shared output and query templates

These files are repo-native guardrail assets, not just Python constants.

## Key Technologies Now Represented in Code

Directly represented in production-shaped files:

- Spark
- Kafka / MSK
- Trino
- S3
- Glue Catalog
- Athena
- Iceberg
- EMR Serverless
- Aurora PostgreSQL
- pgvector
- OpenSearch Serverless
- EKS
- Bedrock
- LangGraph
- Langfuse
- CloudWatch
- New Relic
- AWS CDK

Still primarily conceptual or lightly represented:

- AWS AgentCore
- Step Functions
- Lambda
- S3 Vector Storage
- LaunchDarkly

Lake Formation and AWS Knowledge Bases are represented directly in the CDK layer.

## Best Way To Present This

Tell the team:

1. the local path is the executable proof
2. the production reference path is the stack-aligned proof
3. the two paths intentionally share the same architecture boundaries even though they use different tooling

That framing makes the repo look disciplined instead of inconsistent.

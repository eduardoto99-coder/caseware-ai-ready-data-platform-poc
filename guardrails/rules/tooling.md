---
tooling:
  skills:
    exact_accounting_sql:
      allowed_tools:
        - trino_client
      forbidden_tools:
        - opensearch_vector_store_for_exact_facts
        - postgres_pgvector_for_exact_facts
      execution_order:
        - trino_client
    tenant_safe_policy_rag:
      allowed_tools:
        - opensearch_vector_store
        - postgres_pgvector
        - bedrock_runtime
      forbidden_tools:
        - trino_client_as_primary_narrative_source
      execution_order:
        - opensearch_vector_store
        - bedrock_runtime
    precision_guardrail:
      allowed_tools:
        - trino_client
        - opensearch_vector_store
        - postgres_pgvector
        - bedrock_runtime
      forbidden_tools:
        - vector_store_as_exact_source
      execution_order:
        - trino_client
        - opensearch_vector_store
        - bedrock_runtime
---

The tool policy mirrors the codebase that is actually in this repo. SQL owns exact facts; retrieval and Bedrock only add narrative context.

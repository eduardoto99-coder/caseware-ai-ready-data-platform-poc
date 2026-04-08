Review the repo through the narrative retrieval path.

Focus on:

- `src/caseware_poc/rag/chunking.py`
- `src/caseware_poc/integrations/opensearch_vector_store.py`
- `src/caseware_poc/integrations/postgres_pgvector.py`
- `guardrails/rules/retrieval.md`

Answer these questions:

1. How are tenant and retention filters enforced?
2. How does the chunking logic treat OCR/table-like text differently?
3. Why should exact values not come from this path?

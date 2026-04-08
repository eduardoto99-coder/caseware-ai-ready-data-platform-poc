# Interview Walkthrough

This file is a suggested narrative for presenting the repository in a technical interview.

## 1. Lead with the Problem Boundary

Start here:

“This POC is a vertical slice of a multi-tenant AI-ready accounting data platform. I kept the scope intentionally small, but I made the boundaries production-shaped: incremental ingestion, medallion layers, exact SQL for structured data, tenant-safe RAG for documents, and explicit routing and observability.”

That immediately signals architectural intent rather than just feature implementation.

## 2. Show the Structured Path First

Walk through:

1. `src/caseware_poc/ingestion/sample_data.py`
2. `src/caseware_poc/ingestion/pipeline.py`
3. `src/caseware_poc/transformations/lakehouse.py`

Talking points:

- I simulated a CDC feed instead of full reloads.
- The sample data includes duplicates, deletes, and late-arriving events because those are the cases that separate toy pipelines from platform work.
- Bronze preserves replayability.
- Silver handles dedupe and latest-wins reconciliation.
- Gold tables are shaped for exact agent/tool queries.

## 3. Then Show the Unstructured Path

Walk through:

1. `src/caseware_poc/rag/chunking.py`
2. `src/caseware_poc/rag/embedding.py`
3. `src/caseware_poc/rag/index.py`

Talking points:

- I included a deliberately hard OCR-style workpaper because exactness is where RAG systems often fail.
- Narrative sections and table fragments are chunked differently.
- The vector path is tenant-aware and retention-aware.
- I kept embeddings local and deterministic so the repo is runnable without credentials, but the abstraction is intentionally swappable.
- The same repository also shows how this layer maps to OpenSearch and pgvector, so the challenge still demonstrates the right target tools.

## 4. Show the Decision Boundary

Walk through:

1. `src/caseware_poc/serving/router.py`
2. `src/caseware_poc/serving/skills.py`
3. `src/caseware_poc/serving/query_service.py`

Talking points:

- The platform exposes explicit skills and rules.
- Structured finance questions route to SQL.
- Policy and narrative questions route to RAG.
- Mixed questions trigger a guardrail so exact values never come from OCR or document chunks.

This is one of the most important design choices in the repository. It proves you understand not just how to build RAG, but when not to use it.

## 5. Use the Demo Script

Run:

```bash
python scripts/run_demo.py
```

Recommended questions to narrate:

- `What is the total invoice amount overdue for tenant alpha this month?`
- `What does tenant alpha's revenue recognition policy say about deferred revenue?`
- `What does the OCR workpaper table say about onboarding services and what exact amount is overdue?`

Explain why each route was selected and why that route is the safer one.

## 6. Close with Trade-Offs

These are the best trade-offs to discuss:

- Why microbatching is often enough for 15 to 30 minute SLAs
- Why structured financial data should not be embedding-first
- Why a shared vector index is acceptable only if tenant filters are enforced before scoring
- Why bronze needs to remain replayable even in a small POC
- Why the POC uses production-shaped boundaries even where some components are simulated

## 7. Strong Ending

Close with something like:

“I intentionally treated this as one production-shaped POC architecture. Some components are simulated so the repository is practical to walk through, but the contracts, guardrails, and tool boundaries are the same ones I would discuss in a real platform design review.”

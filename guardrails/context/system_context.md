# AI-Ready Accounting Platform Context

This platform serves multi-tenant accounting and audit workloads.

Core operating constraints:

- Structured financial truth must come from governed SQL-accessible gold tables.
- Narrative context may come from tenant-scoped retrieval over policies, workpapers, notes, and issue summaries.
- Tenant isolation is mandatory and must be enforced before retrieval or query execution.
- Retrieval answers must include citations when they use document evidence.
- OCR or document tables are not authoritative for exact balances, counts, or regulatory facts when a structured source exists.
- If exact financial intent and document intent appear together, the system must use a guardrail path.

Preferred behavior:

- Be explicit about which tool path was selected and why.
- Favor precision over fluency for financial questions.
- Return warnings when grounding is weak or evidence is missing.
- Avoid answering outside the tenant-scoped evidence boundary.

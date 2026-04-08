# Skills and Rules

The serving layer uses explicit skills and routing rules so the platform can explain why a question followed a specific path.

## Skills

Defined in `src/caseware_poc/serving/skills.py`.

### `exact_accounting_sql`

- Purpose: Answer exact financial and operational questions from curated gold tables
- Contract: Deterministic SQL plus governed records and lineage references
- Use for: balances, totals, counts, invoice status, engagement status, control exception metrics

### `tenant_safe_policy_rag`

- Purpose: Retrieve tenant-scoped narrative evidence from policies, workpapers, notes, and issue summaries
- Contract: Grounded narrative output with citations and metadata filters applied before scoring
- Use for: explanations, policies, workpaper interpretation, narrative context

### `precision_guardrail`

- Purpose: Prevent OCR or narrative documents from being treated as authoritative sources for exact numbers
- Contract: SQL-owned exact answer plus document context only when appropriate
- Use for: mixed questions like “what does the workpaper say and what exact amount is overdue?”

## Rules

Defined in `src/caseware_poc/serving/router.py`.

### SQL route

Triggered by terms that imply exactness, aggregation, or operational state:

- `invoice`
- `overdue`
- `total`
- `amount`
- `engagement`
- `status`
- `control`
- `exception`

### RAG route

Triggered by narrative or policy terms:

- `policy`
- `workpaper`
- `note`
- `why`
- `explain`
- `deferred revenue`

### Mixed guardrail route

Triggered when the same question contains exact-value intent and document-oriented cues.

Example:

- “What does the OCR workpaper table say about onboarding services and what exact amount is overdue?”

The response will:

1. Answer the exact amount from `gold_invoice_summary`
2. Provide workpaper context with citations
3. Emit an explicit warning that the guardrail was applied

## Why this matters

The repo intentionally avoids the common failure mode of letting every question fall into a generic chat or RAG flow. The skill-and-rule design demonstrates:

- separation of concerns
- explicit tool selection
- predictable behavior
- debuggable routing decisions
- safer handling of structured financial data

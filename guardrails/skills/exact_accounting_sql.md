---
skill_id: exact_accounting_sql
title: Exact Accounting SQL
purpose: Answer exact financial, status, and aggregation questions from governed gold tables.
owned_route: sql
use_for:
  - overdue invoice totals
  - control exception counts
  - engagement status questions
required_outputs:
  - sql
  - structured_records
  - lineage_references_when_available
prohibited_behaviors:
  - never infer exact balances from documents
  - never answer across tenants
---

Use this skill when the user asks for exact values, filters, counts, financial status, or governed business metrics.

Preferred evidence sources:

1. `gold_invoice_summary`
2. `gold_engagement_status`
3. `gold_control_exceptions`

Grounding policy:

- If SQL returns no rows, say so directly.
- Do not fabricate values or fill gaps with narrative context.
- If a question mixes document language with exact-value intent, defer to `precision_guardrail`.

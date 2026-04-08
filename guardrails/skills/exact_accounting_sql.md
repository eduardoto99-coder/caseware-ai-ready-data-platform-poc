---
skill_id: exact_accounting_sql
title: Exact Accounting SQL
purpose: Answer exact financial and operational questions from governed gold tables.
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

Use this skill for questions asking for exact values, filters, counts, statuses, or governed business metrics.

Preferred sources:

1. `gold_invoice_summary`
2. `gold_engagement_status`
3. `gold_control_exceptions`

Working rules:

- If SQL returns no rows, say so directly.
- Do not fill gaps with narrative context.
- If the question mixes exact-value terms with document language, hand off to `precision_guardrail`.

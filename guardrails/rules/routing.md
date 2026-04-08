---
routing:
  skill_bindings:
    sql: exact_accounting_sql
    rag: tenant_safe_policy_rag
    mixed_guardrail: precision_guardrail
  sql_terms:
    - invoice
    - invoices
    - overdue
    - amount
    - total
    - sum
    - count
    - control
    - controls
    - status
    - exception
    - exceptions
    - balance
    - balances
  rag_terms:
    - policy
    - policies
    - workpaper
    - note
    - notes
    - explain
    - why
    - say
    - guidance
    - revenue recognition
    - deferred revenue
    - issue summary
  precision_doc_terms:
    - table
    - ocr
    - document
    - policy
    - workpaper
  mixed_route_warning: Exact financial values must come from structured SQL, while documents may only provide context.
---

Route by intent, not by whichever store happens to have matching text. Mixed prompts go through the guarded path on purpose.

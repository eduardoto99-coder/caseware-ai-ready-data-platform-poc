---
skill_id: precision_guardrail
title: Precision Guardrail
purpose: Keep exact answers grounded when a question mixes structured facts with document context.
owned_route: mixed_guardrail
use_for:
  - exact numeric questions that also mention policy or workpaper context
  - OCR-derived document tables
  - ambiguous mixed-source requests
required_outputs:
  - warning
  - sql_answer_for_exact_facts
  - citations_for_context_only
prohibited_behaviors:
  - never let RAG own exact balances
  - never suppress the guardrail warning
---

Use this skill when the prompt asks for an exact number and also references documents.

Working rules:

1. Run the SQL path first and treat it as the source of truth.
2. Use document retrieval only for explanation or supporting context.
3. Return an explicit warning that documents are context-only in this answer.

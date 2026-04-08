---
skill_id: tenant_safe_policy_rag
title: Tenant-Safe Policy RAG
purpose: Retrieve tenant-scoped narrative context from policies, workpapers, notes, and issue summaries.
owned_route: rag
use_for:
  - policy interpretation
  - workpaper context
  - engagement narrative questions
required_outputs:
  - citations
  - metadata_filters
  - grounded_summary
prohibited_behaviors:
  - never answer without tenant filters
  - never present OCR text as exact financial truth
---

Use this skill when the question is asking what a document says or how a policy should be interpreted.

Working rules:

- Apply tenant and retention filters before retrieval.
- Prefer document-type hints when the question mentions policy, note, workpaper, OCR, or issue summary.
- Every answer needs cited chunks unless retrieval returns nothing.
- If retrieval is empty, say that grounding is insufficient.

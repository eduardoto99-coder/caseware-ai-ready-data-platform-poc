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

Use this skill when the user asks what a document says, why a policy exists, or what narrative evidence supports an explanation.

Grounding policy:

- Apply tenant and retention filters before retrieval.
- Prefer document-type hints when the question mentions policy, note, workpaper, OCR, or issue summary.
- Every answer must reference cited chunks unless retrieval returns nothing.
- If retrieval is empty, say that grounding is insufficient.

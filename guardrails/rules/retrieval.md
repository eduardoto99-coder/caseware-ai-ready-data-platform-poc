---
retrieval:
  required_metadata_filters:
    - tenant_id
    - retention_state
  fixed_filters:
    retention_state: active
  max_results: 4
  require_citations: true
  doc_type_hints:
    policy:
      - policy
      - policies
    workpaper:
      - workpaper
      - ocr
      - table
    engagement_note:
      - note
      - notes
    issue_summary:
      - issue
      - issue summary
  ranking:
    lexical_overlap_boost: 0.25
    policy_doc_boost: 0.18
    workpaper_doc_boost: 0.18
    note_doc_boost: 0.12
    issue_doc_boost: 0.12
---

Retrieval only runs inside the tenant boundary. Document metadata is part of the access policy, not a cosmetic filter.

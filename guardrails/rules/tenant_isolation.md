---
tenant_isolation:
  require_authenticated_tenant_match: true
  mandatory_sql_filters:
    - tenant_id
  mandatory_retrieval_filters:
    - tenant_id
    - retention_state
  forbid_cross_tenant_citations: true
  failure_mode: hard_fail
---

Tenant isolation is enforced before query execution or retrieval ranking. If the tenant scope is wrong, fail the request.

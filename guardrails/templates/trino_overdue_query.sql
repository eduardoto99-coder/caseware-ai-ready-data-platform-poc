SELECT
    tenant_id,
    SUM(invoice_amount) AS total_overdue_amount,
    COUNT(*) AS overdue_invoice_count
FROM iceberg.caseware_audit_lakehouse.v_gold_invoice_summary
WHERE tenant_id = ?
  AND is_overdue = true
GROUP BY tenant_id

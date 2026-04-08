-- Trino serving views with explicit tenant-aware filters expected at query time.

CREATE OR REPLACE VIEW iceberg.caseware_audit_lakehouse.v_gold_invoice_summary AS
SELECT
    tenant_id,
    invoice_id,
    invoice_number,
    engagement_name,
    customer_name,
    invoice_amount,
    status,
    is_overdue,
    aging_bucket,
    lineage_ref
FROM iceberg.caseware_audit_lakehouse.gold_invoice_summary;

CREATE OR REPLACE VIEW iceberg.caseware_audit_lakehouse.v_gold_control_exceptions AS
SELECT
    tenant_id,
    control_id,
    control_name,
    engagement_name,
    severity,
    status,
    exception_count,
    lineage_ref
FROM iceberg.caseware_audit_lakehouse.gold_control_exceptions;

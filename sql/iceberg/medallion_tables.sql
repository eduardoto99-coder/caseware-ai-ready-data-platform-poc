-- Trino/Iceberg DDL for the lakehouse tables used in this POC.

CREATE TABLE IF NOT EXISTS iceberg.caseware_audit_lakehouse.bronze_structured_events (
    event_id VARCHAR,
    entity_name VARCHAR,
    op VARCHAR,
    tenant_id VARCHAR,
    entity_id VARCHAR,
    updated_at TIMESTAMP(6) WITH TIME ZONE,
    emitted_at TIMESTAMP(6) WITH TIME ZONE,
    source_sequence BIGINT,
    payload_json VARCHAR,
    source_system VARCHAR,
    batch_id VARCHAR,
    source_file VARCHAR
)
WITH (
    format = 'PARQUET',
    location = 's3://caseware-ai-platform-dev-bronze/structured_events/',
    partitioning = ARRAY['tenant_id', 'month(emitted_at)']
);

CREATE TABLE IF NOT EXISTS iceberg.caseware_audit_lakehouse.silver_invoice_snapshot (
    tenant_id VARCHAR,
    invoice_id VARCHAR,
    customer_id VARCHAR,
    engagement_id VARCHAR,
    invoice_number VARCHAR,
    invoice_amount DOUBLE,
    currency VARCHAR,
    status VARCHAR,
    due_date DATE,
    invoice_date DATE,
    updated_at TIMESTAMP(6) WITH TIME ZONE,
    source_event_id VARCHAR,
    source_batch_id VARCHAR
)
WITH (
    format = 'PARQUET',
    location = 's3://caseware-ai-platform-dev-silver/invoice_snapshot/',
    format_version = 2,
    partitioning = ARRAY['tenant_id', 'month(invoice_date)']
);

CREATE TABLE IF NOT EXISTS iceberg.caseware_audit_lakehouse.gold_invoice_summary (
    tenant_id VARCHAR,
    invoice_id VARCHAR,
    invoice_number VARCHAR,
    engagement_id VARCHAR,
    engagement_name VARCHAR,
    customer_id VARCHAR,
    customer_name VARCHAR,
    invoice_amount DOUBLE,
    currency VARCHAR,
    status VARCHAR,
    invoice_date DATE,
    due_date DATE,
    days_past_due INTEGER,
    is_overdue BOOLEAN,
    aging_bucket VARCHAR,
    updated_at TIMESTAMP(6) WITH TIME ZONE,
    lineage_ref VARCHAR
)
WITH (
    format = 'PARQUET',
    location = 's3://caseware-ai-platform-dev-gold/invoice_summary/',
    format_version = 2,
    partitioning = ARRAY['tenant_id', 'month(invoice_date)']
);

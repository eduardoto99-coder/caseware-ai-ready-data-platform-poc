CREATE SCHEMA IF NOT EXISTS accounting;

CREATE TABLE IF NOT EXISTS accounting.customers (
    customer_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_status TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS accounting.engagements (
    engagement_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    engagement_name TEXT NOT NULL,
    engagement_status TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS accounting.invoices (
    invoice_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    engagement_id TEXT NOT NULL,
    invoice_number TEXT NOT NULL,
    invoice_amount NUMERIC(18,2) NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS accounting.controls (
    control_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    engagement_id TEXT NOT NULL,
    control_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    exception_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO accounting.customers (customer_id, tenant_id, customer_name, customer_status)
VALUES
    ('cust_alpha_001', 'tenant_alpha', 'Alpha Manufacturing', 'active'),
    ('cust_beta_001', 'tenant_beta', 'Beta Advisory', 'active')
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO accounting.engagements (engagement_id, tenant_id, customer_id, engagement_name, engagement_status)
VALUES
    ('eng_alpha_001', 'tenant_alpha', 'cust_alpha_001', 'FY26 Audit', 'active'),
    ('eng_beta_001', 'tenant_beta', 'cust_beta_001', 'SOX Readiness', 'active')
ON CONFLICT (engagement_id) DO NOTHING;

INSERT INTO accounting.invoices (
    invoice_id,
    tenant_id,
    customer_id,
    engagement_id,
    invoice_number,
    invoice_amount,
    currency,
    status,
    invoice_date,
    due_date
)
VALUES
    ('inv_alpha_001', 'tenant_alpha', 'cust_alpha_001', 'eng_alpha_001', 'INV-1001', 12500.00, 'USD', 'overdue', CURRENT_DATE - INTERVAL '45 days', CURRENT_DATE - INTERVAL '15 days'),
    ('inv_beta_001', 'tenant_beta', 'cust_beta_001', 'eng_beta_001', 'INV-2001', 8200.00, 'USD', 'current', CURRENT_DATE - INTERVAL '10 days', CURRENT_DATE + INTERVAL '20 days')
ON CONFLICT (invoice_id) DO NOTHING;

INSERT INTO accounting.controls (
    control_id,
    tenant_id,
    engagement_id,
    control_name,
    severity,
    status,
    exception_count
)
VALUES
    ('ctrl_alpha_001', 'tenant_alpha', 'eng_alpha_001', 'Revenue Cutoff Review', 'high', 'open', 2),
    ('ctrl_beta_001', 'tenant_beta', 'eng_beta_001', 'Deferred Revenue Approval', 'medium', 'closed', 0)
ON CONFLICT (control_id) DO NOTHING;

ALTER TABLE accounting.customers REPLICA IDENTITY FULL;
ALTER TABLE accounting.engagements REPLICA IDENTITY FULL;
ALTER TABLE accounting.invoices REPLICA IDENTITY FULL;
ALTER TABLE accounting.controls REPLICA IDENTITY FULL;

CREATE PUBLICATION caseware_cdc_publication
FOR TABLE accounting.customers, accounting.engagements, accounting.invoices, accounting.controls;


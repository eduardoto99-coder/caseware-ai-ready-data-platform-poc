from __future__ import annotations

from pyspark.sql import SparkSession


def build_spark_session() -> SparkSession:
    return (
        SparkSession.builder.appName("caseware-silver-to-gold")
        .config("spark.sql.catalog.caseware", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.caseware.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
        .config("spark.sql.catalog.caseware.warehouse", "s3://caseware-ai-platform-dev/")
        .config("spark.sql.catalog.caseware.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .getOrCreate()
    )


def main() -> None:
    spark = build_spark_session()

    spark.sql(
        """
        CREATE OR REPLACE TABLE caseware.caseware_audit_lakehouse.gold_invoice_summary
        USING iceberg
        PARTITIONED BY (tenant_id, months(invoice_date))
        AS
        SELECT
            inv.tenant_id,
            inv.invoice_id,
            inv.invoice_number,
            inv.engagement_id,
            eng.engagement_name,
            inv.customer_id,
            cust.customer_name,
            inv.invoice_amount,
            inv.currency,
            inv.status,
            inv.invoice_date,
            inv.due_date,
            datediff(current_date(), inv.due_date) AS days_past_due,
            CASE
                WHEN inv.status = 'overdue' OR inv.due_date < current_date() THEN true
                ELSE false
            END AS is_overdue,
            CASE
                WHEN datediff(current_date(), inv.due_date) BETWEEN 1 AND 30 THEN '0_30'
                WHEN datediff(current_date(), inv.due_date) BETWEEN 31 AND 60 THEN '31_60'
                WHEN datediff(current_date(), inv.due_date) > 60 THEN '61_plus'
                ELSE 'current'
            END AS aging_bucket,
            inv.updated_at,
            concat('invoice:', inv.source_event_id, '|customer:', cust.source_event_id, '|engagement:', eng.source_event_id) AS lineage_ref
        FROM caseware.caseware_audit_lakehouse.silver_invoice_snapshot inv
        LEFT JOIN caseware.caseware_audit_lakehouse.silver_customer_snapshot cust
            ON inv.tenant_id = cust.tenant_id AND inv.customer_id = cust.customer_id
        LEFT JOIN caseware.caseware_audit_lakehouse.silver_engagement_snapshot eng
            ON inv.tenant_id = eng.tenant_id AND inv.engagement_id = eng.engagement_id
        WHERE NOT inv.is_deleted
        """
    )


if __name__ == "__main__":
    main()

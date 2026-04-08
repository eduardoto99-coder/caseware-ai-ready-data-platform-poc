from __future__ import annotations

from pyspark.sql import SparkSession


def build_spark_session() -> SparkSession:
    return (
        SparkSession.builder.appName("caseware-bronze-to-silver")
        .config("spark.sql.catalog.caseware", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.caseware.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
        .config("spark.sql.catalog.caseware.warehouse", "s3://caseware-ai-platform-dev/")
        .config("spark.sql.catalog.caseware.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .getOrCreate()
    )


def main() -> None:
    spark = build_spark_session()

    # The merge separates duplicate-event cleanup from latest-entity ranking so retried CDC
    # messages do not overwrite fresher business state.
    spark.sql(
        """
        MERGE INTO caseware.caseware_audit_lakehouse.silver_invoice_snapshot AS target
        USING (
            WITH deduped AS (
                SELECT *,
                       row_number() OVER (
                           PARTITION BY event_id
                           ORDER BY emitted_at DESC, source_sequence DESC
                       ) AS duplicate_rank
                FROM caseware.caseware_audit_lakehouse.bronze_structured_events
                WHERE entity_name = 'invoice'
            ),
            ranked AS (
                SELECT *,
                       row_number() OVER (
                           PARTITION BY tenant_id, entity_id
                           ORDER BY updated_at DESC, source_sequence DESC, emitted_at DESC
                       ) AS entity_rank
                FROM deduped
                WHERE duplicate_rank = 1
            )
            SELECT
                tenant_id,
                entity_id AS invoice_id,
                get_json_object(payload_json, '$.customer_id') AS customer_id,
                get_json_object(payload_json, '$.engagement_id') AS engagement_id,
                get_json_object(payload_json, '$.invoice_number') AS invoice_number,
                CAST(get_json_object(payload_json, '$.invoice_amount') AS DOUBLE) AS invoice_amount,
                get_json_object(payload_json, '$.currency') AS currency,
                get_json_object(payload_json, '$.status') AS status,
                CAST(get_json_object(payload_json, '$.due_date') AS DATE) AS due_date,
                CAST(get_json_object(payload_json, '$.invoice_date') AS DATE) AS invoice_date,
                updated_at,
                event_id AS source_event_id,
                batch_id AS source_batch_id,
                op = 'delete' AS is_deleted
            FROM ranked
            WHERE entity_rank = 1
        ) AS source
        ON target.tenant_id = source.tenant_id AND target.invoice_id = source.invoice_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    )


if __name__ == "__main__":
    main()

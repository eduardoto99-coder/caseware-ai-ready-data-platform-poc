from __future__ import annotations

import logging
import time

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from caseware_poc.observability.cloudwatch_metrics import emit_pipeline_metrics


logger = logging.getLogger(__name__)

BRONZE_TABLE = "caseware.caseware_audit_lakehouse.bronze_structured_events"
SILVER_TABLE = "caseware.caseware_audit_lakehouse.silver_invoice_snapshot"
QUARANTINE_TABLE = "caseware.caseware_audit_lakehouse.silver_invoice_quarantine"


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


def rank_latest_invoice_events(spark: SparkSession) -> DataFrame:
    return spark.sql(
        f"""
        WITH deduped AS (
            SELECT *,
                   row_number() OVER (
                       PARTITION BY event_id
                       ORDER BY emitted_at DESC, source_sequence DESC
                   ) AS duplicate_rank
            FROM {BRONZE_TABLE}
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
            event_id,
            batch_id,
            payload_json,
            updated_at,
            emitted_at,
            source_sequence,
            get_json_object(payload_json, '$.customer_id') AS customer_id,
            get_json_object(payload_json, '$.engagement_id') AS engagement_id,
            get_json_object(payload_json, '$.invoice_number') AS invoice_number,
            get_json_object(payload_json, '$.invoice_amount') AS raw_invoice_amount,
            CAST(get_json_object(payload_json, '$.invoice_amount') AS DOUBLE) AS invoice_amount,
            get_json_object(payload_json, '$.currency') AS currency,
            get_json_object(payload_json, '$.status') AS status,
            get_json_object(payload_json, '$.due_date') AS raw_due_date,
            CAST(get_json_object(payload_json, '$.due_date') AS DATE) AS due_date,
            get_json_object(payload_json, '$.invoice_date') AS raw_invoice_date,
            CAST(get_json_object(payload_json, '$.invoice_date') AS DATE) AS invoice_date,
            op = 'delete' AS is_deleted
        FROM ranked
        WHERE entity_rank = 1
        """
    )


def annotate_quality_issues(candidate_invoices: DataFrame) -> DataFrame:
    candidate_invoices.createOrReplaceTempView("candidate_invoices")
    return candidate_invoices.sparkSession.sql(
        """
        SELECT *,
               filter(
                   array(
                       CASE WHEN tenant_id IS NULL OR trim(tenant_id) = '' THEN 'missing_tenant_id' END,
                       CASE WHEN invoice_id IS NULL OR trim(invoice_id) = '' THEN 'missing_invoice_id' END,
                       CASE WHEN raw_invoice_amount IS NULL OR trim(raw_invoice_amount) = '' THEN 'missing_invoice_amount' END,
                       CASE
                           WHEN raw_invoice_amount IS NOT NULL
                            AND trim(raw_invoice_amount) <> ''
                            AND invoice_amount IS NULL
                           THEN 'invalid_invoice_amount'
                       END,
                       CASE WHEN raw_due_date IS NULL OR trim(raw_due_date) = '' THEN 'missing_due_date' END,
                       CASE
                           WHEN raw_due_date IS NOT NULL
                            AND trim(raw_due_date) <> ''
                            AND due_date IS NULL
                           THEN 'invalid_due_date'
                       END,
                       CASE WHEN raw_invoice_date IS NULL OR trim(raw_invoice_date) = '' THEN 'missing_invoice_date' END,
                       CASE
                           WHEN raw_invoice_date IS NOT NULL
                            AND trim(raw_invoice_date) <> ''
                            AND invoice_date IS NULL
                           THEN 'invalid_invoice_date'
                       END
                   ),
                   issue -> issue IS NOT NULL
               ) AS quality_errors
        FROM candidate_invoices
        """
    )


def ensure_quarantine_table(spark: SparkSession) -> None:
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {QUARANTINE_TABLE} (
            tenant_id STRING,
            invoice_id STRING,
            event_id STRING,
            batch_id STRING,
            payload_json STRING,
            raw_invoice_amount STRING,
            raw_due_date STRING,
            raw_invoice_date STRING,
            quality_errors ARRAY<STRING>,
            updated_at TIMESTAMP,
            emitted_at TIMESTAMP,
            source_sequence BIGINT,
            quarantined_at TIMESTAMP
        )
        USING iceberg
        PARTITIONED BY (tenant_id)
        """
    )


def merge_curated_invoices(curated_invoices: DataFrame) -> None:
    curated_invoices.createOrReplaceTempView("curated_invoices")
    curated_invoices.sparkSession.sql(
        f"""
        MERGE INTO {SILVER_TABLE} AS target
        USING curated_invoices AS source
        ON target.tenant_id = source.tenant_id AND target.invoice_id = source.invoice_id
        WHEN MATCHED THEN UPDATE SET
            customer_id = source.customer_id,
            engagement_id = source.engagement_id,
            invoice_number = source.invoice_number,
            invoice_amount = source.invoice_amount,
            currency = source.currency,
            status = source.status,
            due_date = source.due_date,
            invoice_date = source.invoice_date,
            updated_at = source.updated_at,
            source_event_id = source.source_event_id,
            source_batch_id = source.source_batch_id,
            is_deleted = source.is_deleted
        WHEN NOT MATCHED THEN INSERT (
            tenant_id,
            invoice_id,
            customer_id,
            engagement_id,
            invoice_number,
            invoice_amount,
            currency,
            status,
            due_date,
            invoice_date,
            updated_at,
            source_event_id,
            source_batch_id,
            is_deleted
        )
        VALUES (
            source.tenant_id,
            source.invoice_id,
            source.customer_id,
            source.engagement_id,
            source.invoice_number,
            source.invoice_amount,
            source.currency,
            source.status,
            source.due_date,
            source.invoice_date,
            source.updated_at,
            source.source_event_id,
            source.source_batch_id,
            source.is_deleted
        )
        """
    )


def main() -> None:
    start = time.perf_counter()
    spark = build_spark_session()
    ensure_quarantine_table(spark)

    raw_invoice_events = spark.table(BRONZE_TABLE).where("entity_name = 'invoice'")
    raw_input_count = raw_invoice_events.count()

    # Deduplicate first, then validate the latest entity state so retries do not create
    # duplicate quarantine rows or overwrite fresher invoice snapshots.
    candidate_invoices = rank_latest_invoice_events(spark).cache()
    validated_invoices = annotate_quality_issues(candidate_invoices).cache()

    curated_invoices = (
        validated_invoices.filter("size(quality_errors) = 0")
        .select(
            "tenant_id",
            "invoice_id",
            "customer_id",
            "engagement_id",
            "invoice_number",
            "invoice_amount",
            "currency",
            "status",
            "due_date",
            "invoice_date",
            "updated_at",
            F.col("event_id").alias("source_event_id"),
            F.col("batch_id").alias("source_batch_id"),
            "is_deleted",
        )
        .cache()
    )
    quarantined_invoices = (
        validated_invoices.filter("size(quality_errors) > 0")
        .select(
            "tenant_id",
            "invoice_id",
            "event_id",
            "batch_id",
            "payload_json",
            "raw_invoice_amount",
            "raw_due_date",
            "raw_invoice_date",
            "quality_errors",
            "updated_at",
            "emitted_at",
            "source_sequence",
            F.current_timestamp().alias("quarantined_at"),
        )
        .cache()
    )

    candidate_count = validated_invoices.count()
    curated_count = curated_invoices.count()
    quarantined_count = quarantined_invoices.count()

    if quarantined_count:
        quarantined_invoices.writeTo(QUARANTINE_TABLE).append()
    if curated_count:
        merge_curated_invoices(curated_invoices)

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "bronze_to_silver reconciliation raw_input=%s candidates=%s curated=%s quarantined=%s",
        raw_input_count,
        candidate_count,
        curated_count,
        quarantined_count,
    )
    emit_pipeline_metrics(
        stage="bronze_to_silver_invoice_validation",
        records_in=candidate_count,
        records_out=curated_count,
        quarantined=quarantined_count,
        duration_ms=duration_ms,
    )


if __name__ == "__main__":
    main()

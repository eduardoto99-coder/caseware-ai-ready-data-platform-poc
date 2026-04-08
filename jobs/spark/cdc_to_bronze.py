from __future__ import annotations

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, from_json, to_timestamp
from pyspark.sql.types import StringType, StructField, StructType


CDC_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), False),
        StructField("entity_name", StringType(), False),
        StructField("op", StringType(), False),
        StructField("tenant_id", StringType(), False),
        StructField("entity_id", StringType(), False),
        StructField("updated_at", StringType(), False),
        StructField("emitted_at", StringType(), False),
        StructField("source_sequence", StringType(), False),
        StructField("payload_json", StringType(), False),
        StructField("source_system", StringType(), False),
        StructField("event_version", StringType(), True),
        StructField("batch_id", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)


def build_spark_session() -> SparkSession:
    return (
        SparkSession.builder.appName("caseware-cdc-to-bronze")
        .config("spark.sql.catalog.caseware", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.caseware.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
        .config("spark.sql.catalog.caseware.warehouse", "s3://caseware-ai-platform-dev-bronze/")
        .config("spark.sql.catalog.caseware.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .getOrCreate()
    )


def main() -> None:
    spark = build_spark_session()
    raw_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "${KAFKA_BOOTSTRAP_SERVERS}")
        .option("subscribe", "cdc.invoices,cdc.customers,cdc.engagements,cdc.controls")
        .option("startingOffsets", "earliest")
        .load()
    )

    # Bronze keeps Kafka envelope metadata next to the parsed event so replay, lineage,
    # and CDC troubleshooting do not depend on downstream tables.
    parsed = raw_stream.select(
        col("topic"),
        col("partition"),
        col("offset"),
        current_timestamp().alias("bronze_ingested_at"),
        from_json(col("value").cast("string"), CDC_SCHEMA).alias("event"),
    ).select(
        "topic",
        "partition",
        "offset",
        "bronze_ingested_at",
        col("event.event_id").alias("event_id"),
        col("event.entity_name").alias("entity_name"),
        col("event.op").alias("op"),
        col("event.tenant_id").alias("tenant_id"),
        col("event.entity_id").alias("entity_id"),
        to_timestamp(col("event.updated_at")).alias("updated_at"),
        to_timestamp(col("event.emitted_at")).alias("emitted_at"),
        col("event.source_sequence").cast("long").alias("source_sequence"),
        col("event.payload_json").alias("payload_json"),
        col("event.source_system").alias("source_system"),
        col("event.batch_id").alias("batch_id"),
        col("event.source_file").alias("source_file"),
        col("event.event_version").alias("event_version"),
    )

    (
        parsed.writeStream.outputMode("append")
        .format("iceberg")
        .option("checkpointLocation", "s3://caseware-ai-platform-dev-bronze/checkpoints/cdc_to_bronze/")
        .toTable("caseware.caseware_audit_lakehouse.bronze_structured_events")
    )


if __name__ == "__main__":
    main()

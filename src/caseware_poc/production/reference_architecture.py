from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReferenceArchitecture:
    """Narrative model of the dual-track design used in this repository."""

    runnable_local_path: tuple[str, ...] = (
        "sample data generator",
        "DuckDB bronze/silver/gold lakehouse",
        "local deterministic embeddings",
        "FastAPI serving layer",
    )
    production_reference_path: tuple[str, ...] = (
        "S3 + Glue Catalog + Iceberg",
        "EMR Serverless Spark transforms",
        "Kafka/MSK CDC ingestion",
        "Trino serving over Iceberg",
        "Aurora PostgreSQL with pgvector",
        "OpenSearch Serverless retrieval",
        "Bedrock + LangGraph agent orchestration",
        "Langfuse + CloudWatch + New Relic observability",
        "EKS-hosted serving and analytics components",
    )

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            "runnable_local_path": self.runnable_local_path,
            "production_reference_path": self.production_reference_path,
        }

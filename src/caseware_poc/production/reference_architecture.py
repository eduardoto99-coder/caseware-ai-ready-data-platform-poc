from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReferenceArchitecture:
    """Narrative model of the production-shaped POC architecture used in this repository."""

    platform_layers: tuple[str, ...] = (
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
    demo_shortcuts: tuple[str, ...] = (
        "sample data generator for CDC events and documents",
        "DuckDB-backed demo harness for exact SQL flows",
        "deterministic local embeddings for credential-free retrieval demos",
        "FastAPI query surface for walkthroughs and tests",
    )

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            "platform_layers": self.platform_layers,
            "demo_shortcuts": self.demo_shortcuts,
        }

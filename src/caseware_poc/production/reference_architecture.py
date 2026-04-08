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
    challenge_capabilities: tuple[str, ...] = (
        "CDC-style microbatch ingestion from OLTP systems",
        "Bronze, silver, and gold medallion data products",
        "Tenant-scoped vector retrieval with metadata filtering",
        "Structured-vs-unstructured routing with precision guardrails",
        "Agent orchestration with repo-native skills and rules",
        "Observability, lineage, and governance-oriented controls",
    )

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            "platform_layers": self.platform_layers,
            "challenge_capabilities": self.challenge_capabilities,
        }

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReferencePlatformConfig:
    project: str = "caseware-ai-platform"
    environment: str = "dev"
    region: str = "us-east-1"
    account_id: str = "111111111111"
    data_bucket_prefix: str = "caseware-ai-platform"
    kafka_topic_names: list[str] = field(
        default_factory=lambda: [
            "cdc.customers",
            "cdc.engagements",
            "cdc.invoices",
            "cdc.controls",
            "documents.audit",
        ]
    )
    trino_catalog_name: str = "iceberg"
    glue_database_name: str = "caseware_audit_lakehouse"
    aurora_database_name: str = "caseware_ai"
    opensearch_collection_name: str = "tenant-audit-docs"
    bedrock_knowledge_base_name: str = "caseware-audit-kb"
    langfuse_secret_name: str = "/caseware/langfuse/public-private-keys"
    newrelic_secret_name: str = "/caseware/newrelic/license-key"

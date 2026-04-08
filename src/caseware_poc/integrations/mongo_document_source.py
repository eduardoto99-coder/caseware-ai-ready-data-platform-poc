from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient


@dataclass(slots=True)
class MongoDocumentSourceConfig:
    uri: str
    database: str
    collection: str


class MongoDocumentSource:
    """Reference MongoDB document source for policy, workpaper, and note ingestion."""

    def __init__(self, config: MongoDocumentSourceConfig) -> None:
        self.config = config
        self.client = MongoClient(config.uri)

    @property
    def collection(self):
        return self.client[self.config.database][self.config.collection]

    def fetch_documents_since(self, updated_after: datetime) -> list[dict[str, Any]]:
        cursor = self.collection.find(
            {"updated_at": {"$gte": updated_after}},
            {
                "_id": 0,
                "tenant_id": 1,
                "document_id": 1,
                "title": 1,
                "doc_type": 1,
                "classification": 1,
                "retention_state": 1,
                "updated_at": 1,
                "source_uri": 1,
                "text": 1,
            },
        ).sort("updated_at", 1)
        return list(cursor)

    def seed_healthcheck(self) -> dict[str, Any]:
        return {
            "database": self.config.database,
            "collection": self.config.collection,
            "document_count": self.collection.count_documents({}),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import boto3
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection


@dataclass(slots=True)
class OpenSearchConfig:
    hosts: list[dict[str, object]]
    index_name: str
    region_name: str | None = None
    service_name: str = "aoss"
    username: str | None = None
    password: str | None = None


class OpenSearchDocumentIndex:
    """Reference OpenSearch Serverless client for hybrid lexical/vector retrieval."""

    def __init__(self, config: OpenSearchConfig) -> None:
        self.config = config
        auth: Any = None
        connection_class = None
        if config.region_name:
            credentials = boto3.Session().get_credentials()
            auth = AWSV4SignerAuth(credentials, config.region_name, config.service_name)
            connection_class = RequestsHttpConnection
        elif config.username and config.password:
            auth = (config.username, config.password)
        client_kwargs: dict[str, Any] = {
            "hosts": config.hosts,
            "http_auth": auth,
            "use_ssl": True,
            "verify_certs": True,
        }
        if connection_class is not None:
            client_kwargs["connection_class"] = connection_class
        self.client = OpenSearch(**client_kwargs)

    def ensure_index(self) -> None:
        if self.client.indices.exists(self.config.index_name):
            return
        self.client.indices.create(
            index=self.config.index_name,
            body={
                "settings": {"index": {"knn": True}},
                "mappings": {
                    "properties": {
                        "tenant_id": {"type": "keyword"},
                        "document_id": {"type": "keyword"},
                        "doc_type": {"type": "keyword"},
                        "classification": {"type": "keyword"},
                        "retention_state": {"type": "keyword"},
                        "chunk_text": {"type": "text"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "engine": "faiss",
                                "space_type": "cosinesimil",
                            },
                        },
                    }
                },
            },
        )

    def tenant_scoped_search(
        self,
        *,
        tenant_id: str,
        query_text: str,
        top_k: int,
        query_vector: list[float] | None = None,
        doc_type: str | None = None,
    ) -> dict[str, Any]:
        # Tenant and retention constraints live in bool.filter so cross-tenant data is never
        # eligible for either lexical or vector scoring.
        filters: list[dict[str, object]] = [
            {"term": {"tenant_id": tenant_id}},
            {"term": {"retention_state": "active"}},
        ]
        if doc_type:
            filters.append({"term": {"doc_type": doc_type}})
        should_clauses: list[dict[str, object]] = [
            {
                "match": {
                    "chunk_text": {
                        "query": query_text,
                        "operator": "and",
                    }
                }
            }
        ]
        if query_vector is not None:
            should_clauses.append(
                {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": top_k,
                        }
                    }
                }
            )
        body = {
            "size": top_k,
            "query": {
                "bool": {
                    "filter": filters,
                    "should": should_clauses,
                    "minimum_should_match": 1,
                }
            },
        }
        return self.client.search(index=self.config.index_name, body=body)

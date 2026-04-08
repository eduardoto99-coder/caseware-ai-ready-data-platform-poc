from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import trino


@dataclass(slots=True)
class TrinoConnectionConfig:
    host: str
    port: int
    user: str
    catalog: str
    schema: str
    http_scheme: str = "https"
    verify: bool = True


class TrinoServingClient:
    """Reference Trino client for Iceberg-backed gold data products."""

    def __init__(self, config: TrinoConnectionConfig) -> None:
        self.config = config

    def query_gold_product(self, *, tenant_id: str, sql: str) -> list[dict[str, Any]]:
        connection = trino.dbapi.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            catalog=self.config.catalog,
            schema=self.config.schema,
            http_scheme=self.config.http_scheme,
            verify=self.config.verify,
            session_properties={
                "query_max_run_time": "5m",
            },
            client_tags=["caseware-ai-platform", "tenant-aware-serving"],
        )
        cursor = connection.cursor()
        cursor.execute(
            "SET SESSION iceberg.security = 'lakeformation'",
        )
        cursor.execute(sql, (tenant_id,))
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

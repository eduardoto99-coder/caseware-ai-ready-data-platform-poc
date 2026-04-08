from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import request


@dataclass(slots=True)
class KafkaConnectConfig:
    base_url: str


class DebeziumConnectorClient:
    """Reference Kafka Connect client for registering Debezium source connectors."""

    def __init__(self, config: KafkaConnectConfig) -> None:
        self.config = config

    def put_connector_config(
        self, connector_name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.config.base_url}/connectors/{connector_name}/config",
            data=body,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))

    def connector_status(self, connector_name: str) -> dict[str, Any]:
        req = request.Request(
            f"{self.config.base_url}/connectors/{connector_name}/status",
            method="GET",
        )
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))

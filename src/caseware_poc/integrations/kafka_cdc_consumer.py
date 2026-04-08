from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from confluent_kafka import Consumer


@dataclass(slots=True)
class KafkaCdcConfig:
    brokers: str
    group_id: str
    topic: str
    security_protocol: str = "SASL_SSL"
    sasl_mechanism: str = "AWS_MSK_IAM"


class KafkaCdcMicrobatchConsumer:
    """Reference Kafka/MSK CDC consumer that writes batches for Spark/Iceberg jobs."""

    def __init__(self, config: KafkaCdcConfig) -> None:
        self.config = config
        self.consumer = Consumer(
            {
                "bootstrap.servers": config.brokers,
                "group.id": config.group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
                "security.protocol": config.security_protocol,
                "sasl.mechanism": config.sasl_mechanism,
            }
        )

    def poll_batch(self, max_messages: int = 5000, timeout_seconds: float = 5.0) -> list[dict[str, Any]]:
        self.consumer.subscribe([self.config.topic])
        batch: list[dict[str, Any]] = []
        while len(batch) < max_messages:
            message = self.consumer.poll(timeout_seconds)
            if message is None:
                break
            if message.error():
                raise RuntimeError(str(message.error()))
            batch.append(json.loads(message.value().decode("utf-8")))
        return batch

    def commit(self) -> None:
        self.consumer.commit()

from __future__ import annotations

from dataclasses import dataclass

from caseware_poc.common.config import AppConfig
from caseware_poc.common.logging_utils import JsonLogger


@dataclass(slots=True)
class PlatformRuntime:
    config: AppConfig
    logger: JsonLogger

    @classmethod
    def create(cls, config: AppConfig) -> "PlatformRuntime":
        return cls(
            config=config,
            logger=JsonLogger(config.log_dir / "platform_events.jsonl"),
        )

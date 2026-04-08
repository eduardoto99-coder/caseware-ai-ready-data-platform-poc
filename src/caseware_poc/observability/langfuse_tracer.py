from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langfuse import Langfuse


@dataclass(slots=True)
class LangfuseConfig:
    public_key: str
    secret_key: str
    host: str


class LangfuseTracer:
    """Reference trace emitter for agent runs, retrieval, and model calls."""

    def __init__(self, config: LangfuseConfig) -> None:
        self.client = Langfuse(
            public_key=config.public_key,
            secret_key=config.secret_key,
            host=config.host,
        )

    def trace_query(self, *, tenant_id: str, route: str, input_payload: dict[str, Any], output_payload: dict[str, Any]) -> None:
        trace = self.client.trace(
            name="caseware-ai-query",
            user_id=tenant_id,
            input=input_payload,
            output=output_payload,
            tags=[route, "tenant-aware"],
        )
        trace.score(name="citation_coverage", value=1.0 if output_payload.get("citations") else 0.0)

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
    """Trace emitter for agent runs with span-level latency and token tracking."""

    def __init__(self, config: LangfuseConfig) -> None:
        self.client = Langfuse(
            public_key=config.public_key,
            secret_key=config.secret_key,
            host=config.host,
        )

    def trace_query(
        self,
        *,
        tenant_id: str,
        route: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        timings: dict[str, float] | None = None,
        token_usage: dict[str, int] | None = None,
        retrieval_summary: dict[str, float] | None = None,
        guardrail_passed: bool = True,
        model_id: str | None = None,
    ) -> None:
        trace = self.client.trace(
            name="caseware-ai-query",
            user_id=tenant_id,
            input=input_payload,
            output=output_payload,
            tags=[route, "tenant-aware"],
            metadata={"guardrail_passed": guardrail_passed},
        )

        # Score citation coverage so retrieval quality is visible in the Langfuse dashboard.
        citations = output_payload.get("citations", [])
        trace.score(name="citation_coverage", value=1.0 if citations else 0.0)
        trace.score(name="citation_count", value=float(len(citations)))
        trace.score(name="guardrail_passed", value=1.0 if guardrail_passed else 0.0)

        # Per-node spans give visibility into where time is spent across route, retrieval,
        # synthesis, and final guardrail enforcement.
        if timings:
            for node_name, duration_ms in timings.items():
                trace.span(
                    name=node_name, metadata={"duration_ms": round(duration_ms, 2)}
                )

        # Token usage from Bedrock so cost and throughput are tracked per query.
        if token_usage:
            trace.generation(
                name="bedrock-synthesis",
                model=model_id or "unknown",
                usage={
                    "input": token_usage.get("input_tokens", 0),
                    "output": token_usage.get("output_tokens", 0),
                },
                metadata={"total_tokens": token_usage.get("total_tokens", 0)},
            )

        # Retrieval quality signals help detect ranking regressions and context-budget drift.
        sql_rows = output_payload.get("sql_rows", [])
        if citations or retrieval_summary:
            best_score = (
                retrieval_summary.get("top_hit_score", 0.0)
                if retrieval_summary
                else 0.0
            )
            budget_chars = (
                retrieval_summary.get("chunk_budget_chars", 0.0)
                if retrieval_summary
                else 0.0
            )
            used_chars = (
                retrieval_summary.get("budget_used_chars", 0.0)
                if retrieval_summary
                else 0.0
            )
            trace.score(name="top_hit_score", value=best_score)
            if budget_chars:
                trace.score(name="budget_utilization", value=used_chars / budget_chars)
            if retrieval_summary and "chunks_returned" in retrieval_summary:
                trace.score(
                    name="retrieved_chunk_count",
                    value=retrieval_summary["chunks_returned"],
                )
            if retrieval_summary and "chunks_kept" in retrieval_summary:
                trace.score(
                    name="kept_chunk_count", value=retrieval_summary["chunks_kept"]
                )

        if sql_rows:
            trace.score(name="sql_row_count", value=float(len(sql_rows)))

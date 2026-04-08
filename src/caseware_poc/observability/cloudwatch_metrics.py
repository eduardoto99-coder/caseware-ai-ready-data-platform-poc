from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_NAMESPACE = "Caseware/AIPlatform"
_DEFAULT_UNIT = "Count"
_LATENCY_UNIT = "Milliseconds"


def emit_embedded_metric(
    namespace: str,
    dimensions: dict[str, str],
    metrics: dict[str, float],
    units: dict[str, str] | None = None,
) -> str:
    """Return CloudWatch Embedded Metric Format payload for structured logging.

    The CloudWatch agent picks up EMF payloads from stdout when running on EKS
    or Lambda, so writing to the logger is enough to emit real metrics.
    """
    metric_units = units or {}
    payload = json.dumps(
        {
            "_aws": {
                "Timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": namespace,
                        "Dimensions": [list(dimensions.keys())],
                        "Metrics": [
                            {
                                "Name": name,
                                "Unit": metric_units.get(name, _DEFAULT_UNIT),
                            }
                            for name in metrics
                        ],
                    }
                ],
            },
            **dimensions,
            **metrics,
        },
        sort_keys=True,
    )
    logger.info(payload)
    return payload


def emit_query_metrics(
    *,
    tenant_id: str,
    route: str,
    latency_ms: float,
    citation_count: int,
    sql_row_count: int,
    guardrail_passed: bool,
    timings: dict[str, float] | None = None,
    retrieval_summary: dict[str, float] | None = None,
) -> str:
    """Emit per-query metrics for the AI platform CloudWatch dashboard."""
    metrics = {
        "QueryLatencyMs": latency_ms,
        "CitationCount": float(citation_count),
        "SqlRowCount": float(sql_row_count),
        "GuardrailPassed": 1.0 if guardrail_passed else 0.0,
    }
    units = {
        "QueryLatencyMs": _LATENCY_UNIT,
    }
    if timings:
        timing_metric_names = {
            "validate_tenant": "ValidateTenantLatencyMs",
            "route": "RouteLatencyMs",
            "sql_retrieval": "SqlRetrievalLatencyMs",
            "rag_retrieval": "RagRetrievalLatencyMs",
            "synthesize": "SynthesisLatencyMs",
            "guardrails": "GuardrailLatencyMs",
        }
        for timing_name, timing_value in timings.items():
            metric_name = timing_metric_names.get(timing_name)
            if not metric_name:
                continue
            metrics[metric_name] = timing_value
            units[metric_name] = _LATENCY_UNIT
    if retrieval_summary:
        if "chunks_returned" in retrieval_summary:
            metrics["RetrievedChunks"] = retrieval_summary["chunks_returned"]
        if "chunks_kept" in retrieval_summary:
            metrics["RetrievedChunksKept"] = retrieval_summary["chunks_kept"]
        if "top_hit_score" in retrieval_summary:
            metrics["TopHitScore"] = retrieval_summary["top_hit_score"]
        budget_chars = retrieval_summary.get("chunk_budget_chars", 0.0)
        used_chars = retrieval_summary.get("budget_used_chars", 0.0)
        if budget_chars:
            metrics["ContextBudgetUsedPct"] = used_chars / budget_chars
    return emit_embedded_metric(
        namespace=_NAMESPACE,
        dimensions={"tenant_id": tenant_id, "route": route},
        metrics=metrics,
        units=units,
    )


def emit_pipeline_metrics(
    *,
    stage: str,
    records_in: int,
    records_out: int,
    quarantined: int,
    duration_ms: float,
) -> str:
    """Emit per-stage data pipeline metrics."""
    return emit_embedded_metric(
        namespace=_NAMESPACE,
        dimensions={"stage": stage},
        metrics={
            "RecordsIn": float(records_in),
            "RecordsOut": float(records_out),
            "Quarantined": float(quarantined),
            "StageDurationMs": duration_ms,
        },
        units={"StageDurationMs": _LATENCY_UNIT},
    )

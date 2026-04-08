import json

from caseware_poc.observability.cloudwatch_metrics import emit_query_metrics


def test_emit_query_metrics_includes_node_latencies_and_retrieval_signals() -> None:
    payload = emit_query_metrics(
        tenant_id="tenant_alpha",
        route="mixed_guardrail",
        latency_ms=123.4,
        citation_count=2,
        sql_row_count=1,
        guardrail_passed=True,
        timings={
            "route": 3.2,
            "sql_retrieval": 40.5,
            "rag_retrieval": 17.1,
            "synthesize": 55.6,
        },
        retrieval_summary={
            "chunks_returned": 4.0,
            "chunks_kept": 3.0,
            "chunk_budget_chars": 8000.0,
            "budget_used_chars": 2400.0,
            "top_hit_score": 0.91,
        },
    )

    metrics = json.loads(payload)

    assert metrics["tenant_id"] == "tenant_alpha"
    assert metrics["route"] == "mixed_guardrail"
    assert metrics["RouteLatencyMs"] == 3.2
    assert metrics["SqlRetrievalLatencyMs"] == 40.5
    assert metrics["RagRetrievalLatencyMs"] == 17.1
    assert metrics["SynthesisLatencyMs"] == 55.6
    assert metrics["RetrievedChunks"] == 4.0
    assert metrics["RetrievedChunksKept"] == 3.0
    assert metrics["TopHitScore"] == 0.91
    assert metrics["ContextBudgetUsedPct"] == 0.3

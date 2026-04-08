"""Retrieval quality evaluation (offline / mock mode).

Reports measurable retrieval reliability signals:
- hit rate@k against a labeled golden set
- MRR@k across the same cases
- latency distribution for the search step
- tenant and retention isolation guarantees
"""

from __future__ import annotations

import re
import statistics
import time
from dataclasses import dataclass

from caseware_poc.agents.guardrails import enforce_context_budget


@dataclass(slots=True)
class MockDocument:
    doc_id: str
    tenant_id: str
    retention_state: str
    doc_type: str
    text: str


@dataclass(slots=True)
class RetrievalCase:
    case_id: str
    tenant_id: str
    query: str
    expected_doc_ids: list[str]


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

_MOCK_INDEX = [
    MockDocument(
        doc_id="policy_deferred_revenue",
        tenant_id="tenant_alpha",
        retention_state="active",
        doc_type="policy",
        text="Deferred revenue for onboarding services is recognized over the delivery period.",
    ),
    MockDocument(
        doc_id="policy_multi_year",
        tenant_id="tenant_alpha",
        retention_state="active",
        doc_type="policy",
        text="Multi-year engagements allocate revenue across performance obligations over time.",
    ),
    MockDocument(
        doc_id="note_materiality_threshold",
        tenant_id="tenant_alpha",
        retention_state="active",
        doc_type="engagement_note",
        text="The engagement note explains why the materiality threshold was set at five percent.",
    ),
    MockDocument(
        doc_id="issue_payroll_discrepancy",
        tenant_id="tenant_alpha",
        retention_state="active",
        doc_type="issue_summary",
        text="The issue summary documents payroll discrepancies and the related remediation plan.",
    ),
    MockDocument(
        doc_id="workpaper_late_fees",
        tenant_id="tenant_alpha",
        retention_state="active",
        doc_type="workpaper",
        text="The OCR workpaper mentions late fee handling and delayed approval context.",
    ),
    MockDocument(
        doc_id="policy_lease_classification",
        tenant_id="tenant_beta",
        retention_state="active",
        doc_type="policy",
        text="Tenant beta policy on classifying lease obligations and right-of-use assets.",
    ),
    MockDocument(
        doc_id="archived_old_policy",
        tenant_id="tenant_alpha",
        retention_state="archived",
        doc_type="policy",
        text="Superseded deferred revenue policy from 2020.",
    ),
]

_GOLDEN_CASES = [
    RetrievalCase(
        case_id="retrieval_001",
        tenant_id="tenant_alpha",
        query="What does the deferred revenue policy say about onboarding services?",
        expected_doc_ids=["policy_deferred_revenue"],
    ),
    RetrievalCase(
        case_id="retrieval_002",
        tenant_id="tenant_alpha",
        query="Explain the revenue recognition guidance for multi-year engagements.",
        expected_doc_ids=["policy_multi_year"],
    ),
    RetrievalCase(
        case_id="retrieval_003",
        tenant_id="tenant_alpha",
        query="Why was the materiality threshold set at 5% for this engagement?",
        expected_doc_ids=["note_materiality_threshold"],
    ),
    RetrievalCase(
        case_id="retrieval_004",
        tenant_id="tenant_alpha",
        query="What does the issue summary say about payroll discrepancies?",
        expected_doc_ids=["issue_payroll_discrepancy"],
    ),
    RetrievalCase(
        case_id="retrieval_005",
        tenant_id="tenant_alpha",
        query="What does the workpaper say about late fees?",
        expected_doc_ids=["workpaper_late_fees"],
    ),
]


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_PATTERN.findall(text.lower()))


def _score_document(query: str, document: MockDocument) -> float:
    query_tokens = _tokenize(query)
    document_tokens = _tokenize(document.text)
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & document_tokens) / len(query_tokens)
    doc_type_boost = 0.0
    if "policy" in query_tokens and document.doc_type == "policy":
        doc_type_boost += 0.2
    if "workpaper" in query_tokens and document.doc_type == "workpaper":
        doc_type_boost += 0.2
    if "note" in query_tokens and document.doc_type == "engagement_note":
        doc_type_boost += 0.2
    if "issue" in query_tokens and document.doc_type == "issue_summary":
        doc_type_boost += 0.2
    return overlap + doc_type_boost


def _tenant_scoped_search(
    case: RetrievalCase, top_k: int = 4
) -> tuple[list[dict], float]:
    start = time.perf_counter()
    ranked = sorted(
        (
            document
            for document in _MOCK_INDEX
            if document.tenant_id == case.tenant_id
            and document.retention_state == "active"
        ),
        key=lambda document: _score_document(case.query, document),
        reverse=True,
    )[:top_k]
    latency_ms = (time.perf_counter() - start) * 1000
    return [
        {
            "id": document.doc_id,
            "tenant_id": document.tenant_id,
            "retention_state": document.retention_state,
            "score": round(_score_document(case.query, document), 4),
            "text": document.text,
            "source_uri": f"s3://{document.tenant_id}/{document.doc_id}",
        }
        for document in ranked
    ], latency_ms


def _reciprocal_rank(result_ids: list[str], expected_doc_ids: list[str]) -> float:
    for index, result_id in enumerate(result_ids, start=1):
        if result_id in expected_doc_ids:
            return 1.0 / index
    return 0.0


def evaluate_retrieval() -> dict:
    case_results: list[dict] = []
    latencies_ms: list[float] = []
    hit_count = 0
    reciprocal_rank_total = 0.0
    tenant_isolation_passes = 0
    retention_passes = 0

    for case in _GOLDEN_CASES:
        hits, latency_ms = _tenant_scoped_search(case)
        result_ids = [hit["id"] for hit in hits]
        hit = any(result_id in case.expected_doc_ids for result_id in result_ids)
        reciprocal_rank = _reciprocal_rank(result_ids, case.expected_doc_ids)
        tenant_isolated = all(hit["tenant_id"] == case.tenant_id for hit in hits)
        retention_safe = all(hit["retention_state"] == "active" for hit in hits)

        hit_count += int(hit)
        reciprocal_rank_total += reciprocal_rank
        tenant_isolation_passes += int(tenant_isolated)
        retention_passes += int(retention_safe)
        latencies_ms.append(latency_ms)
        case_results.append(
            {
                "case_id": case.case_id,
                "expected_doc_ids": case.expected_doc_ids,
                "returned_doc_ids": result_ids,
                "hit": hit,
                "reciprocal_rank": round(reciprocal_rank, 4),
                "latency_ms": round(latency_ms, 4),
                "tenant_isolated": tenant_isolated,
                "retention_safe": retention_safe,
            }
        )

    big_chunks = [{"text": "x" * 3000, "id": f"big_{index}"} for index in range(5)]
    trimmed = enforce_context_budget(big_chunks, max_chars=8000)

    total_cases = len(_GOLDEN_CASES)
    sorted_latencies = sorted(latencies_ms)
    p95_index = (
        int(round((len(sorted_latencies) - 1) * 0.95)) if sorted_latencies else 0
    )

    return {
        "hit_rate_at_4": round(hit_count / total_cases, 2) if total_cases else 0.0,
        "mrr_at_4": round(reciprocal_rank_total / total_cases, 2)
        if total_cases
        else 0.0,
        "mean_latency_ms": round(statistics.mean(latencies_ms), 4)
        if latencies_ms
        else 0.0,
        "p95_latency_ms": round(sorted_latencies[p95_index], 4)
        if sorted_latencies
        else 0.0,
        "tenant_isolation_pass_rate": round(tenant_isolation_passes / total_cases, 2)
        if total_cases
        else 0.0,
        "retention_filter_pass_rate": round(retention_passes / total_cases, 2)
        if total_cases
        else 0.0,
        "context_budget": {
            "input_chunks": len(big_chunks),
            "output_chunks": len(trimmed),
            "budget_respected": sum(len(chunk["text"]) for chunk in trimmed) <= 8000,
        },
        "per_case": case_results,
    }


if __name__ == "__main__":
    report = evaluate_retrieval()
    print(
        "Retrieval eval: "
        f"hit_rate@4={report['hit_rate_at_4']:.0%} "
        f"mrr@4={report['mrr_at_4']:.2f} "
        f"p95_latency_ms={report['p95_latency_ms']}"
    )
    print(
        "Isolation: "
        f"tenant={report['tenant_isolation_pass_rate']:.0%} "
        f"retention={report['retention_filter_pass_rate']:.0%}"
    )
    print(f"Context budget respected: {report['context_budget']['budget_respected']}")

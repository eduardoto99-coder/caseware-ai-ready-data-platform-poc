"""Chunking quality evaluation.

Measures the core reliability properties of the chunker:
- mean narrative chunk size
- overlap coverage between adjacent narrative chunks
- table-detection precision/recall on labeled examples
"""

from __future__ import annotations

import statistics
from datetime import datetime, timezone

from caseware_poc.common.models import DocumentRecord
from caseware_poc.rag.chunking import DocumentChunk, chunk_document


_NARRATIVE_ONLY = DocumentRecord(
    tenant_id="eval_tenant",
    document_id="eval_narrative",
    title="Revenue Recognition Policy",
    doc_type="policy",
    classification="confidential",
    retention_state="active",
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    source_uri="s3://eval/policy.txt",
    contains_table_like_text=False,
    text=(
        "Revenue from onboarding services is recognized over the service delivery period. "
        "The allocation of transaction price follows the standalone selling price method. "
        "When a contract includes multiple performance obligations, each obligation is "
        "identified and measured separately. Variable consideration is estimated using the "
        "expected value approach and constrained to the extent that a significant reversal "
        "is not probable. Contract modifications are treated as separate contracts when "
        "the additional goods or services are distinct and the price reflects standalone "
        "selling prices.\n\n"
        "Deferred revenue arises when payment is received before the performance obligation "
        "is satisfied. The liability is released to revenue as services are delivered. "
        "The company reviews deferred revenue balances quarterly to ensure proper classification."
    ),
)

_TABLE_DOCUMENT = DocumentRecord(
    tenant_id="eval_tenant",
    document_id="eval_table",
    title="OCR Workpaper Extract",
    doc_type="workpaper",
    classification="confidential",
    retention_state="active",
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    source_uri="s3://eval/workpaper.txt",
    contains_table_like_text=True,
    text=(
        "Audit observations for Q4 2025.\n\n"
        "Line Item          Treatment\n"
        "Onboarding         Recognize over service period\n"
        "License fees       Recognize at point in time\n"
        "Support            Recognize ratably over term\n\n"
        "The auditor concluded that the treatments above are consistent with ASC 606."
    ),
)

_EMPTY_DOCUMENT = DocumentRecord(
    tenant_id="eval_tenant",
    document_id="eval_empty",
    title="Empty Note",
    doc_type="engagement_note",
    classification="internal",
    retention_state="active",
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    source_uri="s3://eval/empty.txt",
    contains_table_like_text=False,
    text="",
)

_SHORT_DOCUMENT = DocumentRecord(
    tenant_id="eval_tenant",
    document_id="eval_short",
    title="Brief Note",
    doc_type="engagement_note",
    classification="internal",
    retention_state="active",
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    source_uri="s3://eval/short.txt",
    contains_table_like_text=False,
    text="Single paragraph under the window threshold.",
)

_TABLE_ONLY_DOCUMENT = DocumentRecord(
    tenant_id="eval_tenant",
    document_id="eval_table_only",
    title="Tables Only",
    doc_type="workpaper",
    classification="confidential",
    retention_state="active",
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    source_uri="s3://eval/table_only.txt",
    contains_table_like_text=True,
    text=(
        "Column A           Column B\n"
        "Revenue            120000\n"
        "Deferred Revenue   45000\n"
    ),
)

_FALSE_POSITIVE_GUARD = DocumentRecord(
    tenant_id="eval_tenant",
    document_id="eval_false_positive_guard",
    title="Indented Narrative",
    doc_type="engagement_note",
    classification="internal",
    retention_state="active",
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    source_uri="s3://eval/indented_note.txt",
    contains_table_like_text=False,
    text=(
        "The team discussed recognition timing.\n\n"
        "The note is indented for readability only.\n"
        "It is not a table and should remain narrative."
    ),
)

_BOUNDARY_DOCUMENT = DocumentRecord(
    tenant_id="eval_tenant",
    document_id="eval_boundary",
    title="Boundary Case",
    doc_type="policy",
    classification="confidential",
    retention_state="active",
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    source_uri="s3://eval/boundary.txt",
    contains_table_like_text=False,
    text="A" * 320,
)


def _chunk_stats(chunks: list[DocumentChunk]) -> dict:
    if not chunks:
        return {"count": 0}
    lengths = [len(c.text) for c in chunks]
    return {
        "count": len(chunks),
        "min_chars": min(lengths),
        "max_chars": max(lengths),
        "mean_chars": round(statistics.mean(lengths), 1),
        "median_chars": round(statistics.median(lengths), 1),
        "kinds": {
            kind: sum(1 for c in chunks if c.chunk_kind == kind)
            for kind in set(c.chunk_kind for c in chunks)
        },
    }


def _has_overlap(previous: DocumentChunk, current: DocumentChunk) -> bool:
    tail = previous.text.rsplit(". ", 1)[-1] if ". " in previous.text else previous.text
    return bool(tail and tail[:40] in current.text)


def evaluate_chunking() -> dict:
    results: dict[str, dict] = {}

    narrative_chunks = chunk_document(_NARRATIVE_ONLY)
    narrative_pairs = max(len(narrative_chunks) - 1, 0)
    overlapping_pairs = sum(
        1
        for index in range(1, len(narrative_chunks))
        if _has_overlap(narrative_chunks[index - 1], narrative_chunks[index])
    )
    results["narrative_windowing"] = _chunk_stats(narrative_chunks)
    results["narrative_windowing"]["all_narrative"] = all(
        chunk.chunk_kind == "narrative" for chunk in narrative_chunks
    )
    results["narrative_windowing"]["overlap_pair_rate"] = (
        round(overlapping_pairs / narrative_pairs, 2) if narrative_pairs else 0.0
    )
    results["narrative_windowing"]["mean_size_in_target_range"] = (
        200 <= results["narrative_windowing"]["mean_chars"] <= 400
    )

    short_chunks = chunk_document(_SHORT_DOCUMENT)
    boundary_chunks = chunk_document(_BOUNDARY_DOCUMENT)
    empty_chunks = chunk_document(_EMPTY_DOCUMENT)
    results["boundary_cases"] = {
        "short_doc_single_chunk": len(short_chunks) == 1,
        "boundary_doc_single_chunk": len(boundary_chunks) == 1,
        "empty_doc_count": len(empty_chunks),
    }

    table_cases = [
        ("table_document", _TABLE_DOCUMENT, True),
        ("table_only_document", _TABLE_ONLY_DOCUMENT, True),
        ("narrative_only_document", _NARRATIVE_ONLY, False),
        ("false_positive_guard", _FALSE_POSITIVE_GUARD, False),
    ]
    case_results: dict[str, dict[str, bool | int]] = {}
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    for name, document, expect_table in table_cases:
        chunks = chunk_document(document)
        predicted_table = any(chunk.chunk_kind == "table_fragment" for chunk in chunks)
        case_results[name] = {
            "expected_table_fragment": expect_table,
            "predicted_table_fragment": predicted_table,
            "chunk_count": len(chunks),
        }
        if predicted_table and expect_table:
            true_positives += 1
        elif predicted_table and not expect_table:
            false_positives += 1
        elif expect_table and not predicted_table:
            false_negatives += 1
    precision_denominator = true_positives + false_positives
    recall_denominator = true_positives + false_negatives
    results["table_detection"] = {
        "precision": round(true_positives / precision_denominator, 2)
        if precision_denominator
        else 0.0,
        "recall": round(true_positives / recall_denominator, 2)
        if recall_denominator
        else 0.0,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "cases": case_results,
    }

    return results


if __name__ == "__main__":
    report = evaluate_chunking()
    for doc_type, stats in report.items():
        print(f"\n{doc_type}:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

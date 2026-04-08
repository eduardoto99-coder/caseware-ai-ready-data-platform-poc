from datetime import datetime, timezone

from caseware_poc.common.models import DocumentRecord
from caseware_poc.rag.chunking import chunk_document


def _document(
    *, text: str, document_id: str = "doc_1", contains_table_like_text: bool = False
) -> DocumentRecord:
    return DocumentRecord(
        tenant_id="tenant_alpha",
        document_id=document_id,
        title="Test Document",
        doc_type="workpaper" if contains_table_like_text else "policy",
        classification="confidential",
        retention_state="active",
        created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        source_uri=f"s3://tenant-alpha/{document_id}.txt",
        contains_table_like_text=contains_table_like_text,
        text=text,
    )


def test_table_like_document_keeps_table_fragment() -> None:
    document = _document(
        document_id="ocr_workpaper",
        contains_table_like_text=True,
        text=(
            "Header\n\n"
            "Observed table\n"
            "Line Item    Treatment\n"
            "Onboarding    Recognize over service period\n"
        ),
    )

    chunks = chunk_document(document)

    assert any(chunk.chunk_kind == "table_fragment" for chunk in chunks)


def test_empty_document_returns_no_chunks() -> None:
    assert chunk_document(_document(text="", document_id="empty")) == []


def test_single_sentence_document_stays_in_one_narrative_chunk() -> None:
    chunks = chunk_document(
        _document(text="Single sentence under the threshold.", document_id="short")
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_kind == "narrative"


def test_boundary_length_document_does_not_split_at_320_chars() -> None:
    chunks = chunk_document(_document(text="A" * 320, document_id="boundary"))

    assert len(chunks) == 1
    assert chunks[0].text == "A" * 320


def test_long_narrative_creates_multiple_chunks_with_carryover() -> None:
    document = _document(
        document_id="long_narrative",
        text=(
            "Revenue is recognized over time when control transfers continuously. "
            "This policy applies to onboarding services delivered over multiple weeks. "
            "The finance team reviews exceptions monthly and escalates unusual balances. "
            "Supporting documentation is retained with the engagement workpapers for audit review. "
            "Deferred revenue is released as obligations are satisfied."
        ),
    )

    chunks = chunk_document(document)

    assert len(chunks) >= 2
    assert chunks[0].chunk_kind == "narrative"
    assert chunks[0].text.rsplit(". ", 1)[-1][:30] in chunks[1].text


def test_table_only_document_remains_a_single_table_fragment() -> None:
    chunks = chunk_document(
        _document(
            document_id="table_only",
            contains_table_like_text=True,
            text=(
                "Column A          Column B\n"
                "Revenue           120000\n"
                "Deferred Revenue  45000\n"
            ),
        )
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_kind == "table_fragment"

from datetime import datetime, timezone

from caseware_poc.common.models import DocumentRecord
from caseware_poc.rag.chunking import chunk_document


def test_table_like_document_keeps_table_fragment() -> None:
    document = DocumentRecord(
        tenant_id="tenant_alpha",
        document_id="doc_1",
        title="OCR workpaper",
        doc_type="workpaper",
        classification="confidential",
        retention_state="active",
        created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        source_uri="s3://tenant-alpha/workpapers/doc.txt",
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

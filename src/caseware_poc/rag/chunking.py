from __future__ import annotations

import re
from dataclasses import dataclass

from caseware_poc.common.models import DocumentRecord


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    tenant_id: str
    document_id: str
    title: str
    doc_type: str
    classification: str
    retention_state: str
    source_uri: str
    chunk_index: int
    chunk_kind: str
    text: str


def normalize_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n")
    cleaned = cleaned.replace("\t", " ")
    cleaned = re.sub(r"[ ]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _is_table_like(paragraph: str) -> bool:
    lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    return any(re.search(r"\w+\s{2,}\w+", line) for line in lines)


def chunk_document(document: DocumentRecord) -> list[DocumentChunk]:
    normalized = normalize_text(document.text)
    paragraphs = [block.strip() for block in normalized.split("\n\n") if block.strip()]
    chunks: list[DocumentChunk] = []
    carryover = ""
    for paragraph in paragraphs:
        kind = (
            "table_fragment"
            if document.contains_table_like_text and _is_table_like(paragraph)
            else "narrative"
        )
        text = paragraph
        if kind == "narrative" and len(paragraph) > 320:
            # Narrative chunks use overlapping sentence windows so downstream retrieval keeps
            # enough local context without breaking table-like fragments apart.
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            windows: list[str] = []
            buffer: list[str] = []
            buffer_length = 0
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if buffer and buffer_length + len(sentence) > 320:
                    windows.append(" ".join(buffer))
                    buffer = buffer[-1:]
                    buffer_length = len(buffer[0]) if buffer else 0
                buffer.append(sentence)
                buffer_length += len(sentence)
            if buffer:
                windows.append(" ".join(buffer))
            fragments = windows
        else:
            fragments = [text]

        for fragment in fragments:
            # Carry the prior tail sentence forward to avoid losing references at chunk edges.
            chunk_text = fragment if not carryover else f"{carryover}\n{fragment}"
            chunk = DocumentChunk(
                chunk_id=f"{document.document_id}::chunk::{len(chunks)}",
                tenant_id=document.tenant_id,
                document_id=document.document_id,
                title=document.title,
                doc_type=document.doc_type,
                classification=document.classification,
                retention_state=document.retention_state,
                source_uri=document.source_uri,
                chunk_index=len(chunks),
                chunk_kind=kind,
                text=chunk_text,
            )
            chunks.append(chunk)
            carryover = fragment.split(". ")[-1] if kind == "narrative" else ""
            if len(carryover) > 160:
                carryover = carryover[:160]
    return chunks

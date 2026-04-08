"""AWS Textract integration for layout-aware document processing.

Extracts text blocks, tables, and key-value pairs from scanned documents
and feeds structured output into the chunking pipeline.  Table blocks are
preserved with column alignment so downstream table-detection heuristics
in chunking.py can keep them intact.
"""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any

import boto3

from caseware_poc.common.models import DocumentRecord, DocumentType, RetentionState


@dataclass(slots=True)
class TextractConfig:
    region_name: str
    feature_types: list[str] = field(default_factory=lambda: ["TABLES", "FORMS"])


@dataclass(slots=True)
class ExtractedDocument:
    raw_text: str
    tables: list[list[list[str]]]
    key_value_pairs: list[dict[str, str]]
    contains_table_like_text: bool
    page_count: int

    def to_document_record(
        self,
        *,
        tenant_id: str,
        document_id: str,
        title: str,
        doc_type: DocumentType,
        classification: str,
        retention_state: RetentionState,
        source_uri: str,
        observed_at: datetime | None = None,
    ) -> DocumentRecord:
        timestamp = observed_at or datetime.now(timezone.utc)
        return DocumentRecord(
            tenant_id=tenant_id,
            document_id=document_id,
            title=title,
            doc_type=doc_type,
            classification=classification,
            retention_state=retention_state,
            created_at=timestamp,
            updated_at=timestamp,
            text=self.raw_text,
            source_uri=source_uri,
            contains_table_like_text=self.contains_table_like_text,
        )


class TextractDocumentProcessor:
    """Process scanned documents through Textract and prepare for chunking."""

    def __init__(self, config: TextractConfig) -> None:
        self.config = config
        self.client = boto3.client("textract", region_name=config.region_name)

    def analyze_document(self, s3_bucket: str, s3_key: str) -> ExtractedDocument:
        """Run Textract AnalyzeDocument and return structured output."""
        response = self.client.analyze_document(
            Document={"S3Object": {"Bucket": s3_bucket, "Name": s3_key}},
            FeatureTypes=self.config.feature_types,
        )
        return self._parse_response(response)

    def analyze_document_bytes(self, document_bytes: bytes) -> ExtractedDocument:
        """Run Textract AnalyzeDocument on raw bytes (single page)."""
        response = self.client.analyze_document(
            Document={"Bytes": document_bytes},
            FeatureTypes=self.config.feature_types,
        )
        return self._parse_response(response)

    def _parse_response(self, response: dict[str, Any]) -> ExtractedDocument:
        blocks = response.get("Blocks", [])
        block_map = {b["Id"]: b for b in blocks}

        lines = self._extract_lines(blocks)
        tables = self._extract_tables(blocks, block_map)
        kv_pairs = self._extract_key_value_pairs(blocks, block_map)
        page_count = sum(1 for b in blocks if b["BlockType"] == "PAGE")

        # Build the full text with tables rendered using column-aligned spacing
        # so the chunker's _is_table_like heuristic detects them correctly.
        text_parts: list[str] = []
        for line in lines:
            text_parts.append(line)
        for table in tables:
            text_parts.append("")
            for row in table:
                text_parts.append("    ".join(cell.ljust(20) for cell in row))
            text_parts.append("")

        return ExtractedDocument(
            raw_text="\n".join(text_parts),
            tables=tables,
            key_value_pairs=kv_pairs,
            contains_table_like_text=len(tables) > 0,
            page_count=page_count,
        )

    @staticmethod
    def _extract_lines(blocks: list[dict[str, Any]]) -> list[str]:
        return [b["Text"] for b in blocks if b["BlockType"] == "LINE" and "Text" in b]

    @staticmethod
    def _extract_tables(
        blocks: list[dict[str, Any]], block_map: dict[str, Any]
    ) -> list[list[list[str]]]:
        tables: list[list[list[str]]] = []
        for block in blocks:
            if block["BlockType"] != "TABLE":
                continue
            rows: dict[int, dict[int, str]] = {}
            for rel in block.get("Relationships", []):
                if rel["Type"] != "CHILD":
                    continue
                for cell_id in rel["Ids"]:
                    cell = block_map.get(cell_id, {})
                    if cell.get("BlockType") != "CELL":
                        continue
                    row_idx = cell.get("RowIndex", 0)
                    col_idx = cell.get("ColumnIndex", 0)
                    cell_text = TextractDocumentProcessor._get_cell_text(
                        cell, block_map
                    )
                    rows.setdefault(row_idx, {})[col_idx] = cell_text
            table = []
            for row_idx in sorted(rows):
                row = rows[row_idx]
                table.append([row.get(col, "") for col in sorted(row)])
            tables.append(table)
        return tables

    @staticmethod
    def _extract_key_value_pairs(
        blocks: list[dict[str, Any]], block_map: dict[str, Any]
    ) -> list[dict[str, str]]:
        pairs: list[dict[str, str]] = []
        for block in blocks:
            if block["BlockType"] != "KEY_VALUE_SET" or "KEY" not in block.get(
                "EntityTypes", []
            ):
                continue
            key_text = TextractDocumentProcessor._get_child_text(block, block_map)
            value_text = ""
            for rel in block.get("Relationships", []):
                if rel["Type"] == "VALUE":
                    for val_id in rel["Ids"]:
                        val_block = block_map.get(val_id, {})
                        value_text = TextractDocumentProcessor._get_child_text(
                            val_block, block_map
                        )
            if key_text:
                pairs.append({"key": key_text, "value": value_text})
        return pairs

    @staticmethod
    def _get_cell_text(cell: dict[str, Any], block_map: dict[str, Any]) -> str:
        return TextractDocumentProcessor._get_child_text(cell, block_map)

    @staticmethod
    def _get_child_text(block: dict[str, Any], block_map: dict[str, Any]) -> str:
        words: list[str] = []
        for rel in block.get("Relationships", []):
            if rel["Type"] != "CHILD":
                continue
            for child_id in rel["Ids"]:
                child = block_map.get(child_id, {})
                if child.get("BlockType") == "WORD" and "Text" in child:
                    words.append(child["Text"])
        return " ".join(words)

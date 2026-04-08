from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


EventOp = Literal["insert", "update", "delete"]
EntityName = Literal["customer", "engagement", "invoice", "journal_entry", "control"]
DocumentType = Literal["policy", "workpaper", "engagement_note", "issue_summary"]
RetentionState = Literal["active", "archived", "legal_hold"]


class StructuredChangeEvent(BaseModel):
    event_id: str
    entity_name: EntityName
    op: EventOp
    tenant_id: str
    entity_id: str
    updated_at: datetime
    emitted_at: datetime
    source_sequence: int
    payload: dict[str, Any] = Field(default_factory=dict)
    source_system: str = "oltp-simulator"


class DocumentRecord(BaseModel):
    tenant_id: str
    document_id: str
    title: str
    doc_type: DocumentType
    classification: str
    retention_state: RetentionState
    created_at: datetime
    updated_at: datetime
    text: str
    source_uri: str
    contains_table_like_text: bool = False


class RetrievedChunk(BaseModel):
    chunk_id: str
    tenant_id: str
    document_id: str
    doc_type: str
    title: str
    source_uri: str
    chunk_index: int
    score: float
    text: str


class RouteDecision(BaseModel):
    route: Literal["sql", "rag", "mixed_guardrail"]
    skill: str
    reason: str
    rules_fired: list[str]


class QueryResponse(BaseModel):
    tenant_id: str
    question: str
    route: RouteDecision
    answer: str
    sql: str | None = None
    records: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[RetrievedChunk] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

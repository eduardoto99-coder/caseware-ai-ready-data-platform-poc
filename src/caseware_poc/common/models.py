from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DocumentType = Literal["policy", "workpaper", "engagement_note", "issue_summary"]
RetentionState = Literal["active", "archived", "legal_hold"]


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


class RouteDecision(BaseModel):
    route: Literal["sql", "rag", "mixed_guardrail"]
    skill: str
    reason: str
    rules_fired: list[str]


class GuardrailContext(BaseModel):
    skill_id: str
    skill_file: str
    rule_ids: list[str] = Field(default_factory=list)
    rule_files: list[str] = Field(default_factory=list)
    enforcement_points: list[str] = Field(default_factory=list)

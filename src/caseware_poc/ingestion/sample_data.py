from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from caseware_poc.common.io_utils import write_json, write_jsonl
from caseware_poc.common.models import DocumentRecord, StructuredChangeEvent


def _ts(day: int, hour: int, minute: int) -> datetime:
    return datetime(2026, 4, day, hour, minute, tzinfo=timezone.utc)


def _event(
    *,
    event_id: str,
    entity_name: str,
    op: str,
    tenant_id: str,
    entity_id: str,
    updated_at: datetime,
    emitted_at: datetime,
    source_sequence: int,
    payload: dict,
) -> StructuredChangeEvent:
    return StructuredChangeEvent(
        event_id=event_id,
        entity_name=entity_name,  # type: ignore[arg-type]
        op=op,  # type: ignore[arg-type]
        tenant_id=tenant_id,
        entity_id=entity_id,
        updated_at=updated_at,
        emitted_at=emitted_at,
        source_sequence=source_sequence,
        payload=payload,
    )


def _doc(
    *,
    tenant_id: str,
    document_id: str,
    title: str,
    doc_type: str,
    classification: str,
    retention_state: str,
    created_at: datetime,
    updated_at: datetime,
    text: str,
    source_uri: str,
    contains_table_like_text: bool = False,
) -> DocumentRecord:
    return DocumentRecord(
        tenant_id=tenant_id,
        document_id=document_id,
        title=title,
        doc_type=doc_type,  # type: ignore[arg-type]
        classification=classification,
        retention_state=retention_state,  # type: ignore[arg-type]
        created_at=created_at,
        updated_at=updated_at,
        text=text,
        source_uri=source_uri,
        contains_table_like_text=contains_table_like_text,
    )


def structured_event_batches() -> list[list[StructuredChangeEvent]]:
    """Deterministic structured change feed with late and duplicate events."""

    batch_1 = [
        _event(
            event_id="evt-cus-a1",
            entity_name="customer",
            op="insert",
            tenant_id="tenant_alpha",
            entity_id="cust_a1",
            updated_at=_ts(1, 9, 0),
            emitted_at=_ts(1, 9, 1),
            source_sequence=1,
            payload={
                "customer_name": "Northwind Audit LLP",
                "segment": "enterprise",
                "billing_country": "CA",
            },
        ),
        _event(
            event_id="evt-eng-a1",
            entity_name="engagement",
            op="insert",
            tenant_id="tenant_alpha",
            entity_id="eng_a1",
            updated_at=_ts(1, 9, 5),
            emitted_at=_ts(1, 9, 6),
            source_sequence=2,
            payload={
                "engagement_name": "FY26 Northwind Audit",
                "status": "active",
                "owner": "A. Patel",
                "issue_count": 2,
            },
        ),
        _event(
            event_id="evt-inv-a1",
            entity_name="invoice",
            op="insert",
            tenant_id="tenant_alpha",
            entity_id="inv_a1",
            updated_at=_ts(1, 9, 10),
            emitted_at=_ts(1, 9, 11),
            source_sequence=3,
            payload={
                "customer_id": "cust_a1",
                "engagement_id": "eng_a1",
                "invoice_number": "A-1001",
                "invoice_amount": 12500.0,
                "currency": "USD",
                "status": "sent",
                "due_date": "2026-04-05",
                "invoice_date": "2026-04-01",
            },
        ),
        _event(
            event_id="evt-ctl-a1",
            entity_name="control",
            op="insert",
            tenant_id="tenant_alpha",
            entity_id="ctl_a1",
            updated_at=_ts(1, 9, 20),
            emitted_at=_ts(1, 9, 21),
            source_sequence=4,
            payload={
                "engagement_id": "eng_a1",
                "control_name": "Revenue cutoff review",
                "severity": "high",
                "status": "exception_open",
                "exception_count": 2,
                "owner": "L. Gomez",
            },
        ),
        _event(
            event_id="evt-cus-b1",
            entity_name="customer",
            op="insert",
            tenant_id="tenant_beta",
            entity_id="cust_b1",
            updated_at=_ts(1, 9, 0),
            emitted_at=_ts(1, 9, 2),
            source_sequence=1,
            payload={
                "customer_name": "Cypress Controls Inc",
                "segment": "mid_market",
                "billing_country": "US",
            },
        ),
        _event(
            event_id="evt-eng-b1",
            entity_name="engagement",
            op="insert",
            tenant_id="tenant_beta",
            entity_id="eng_b1",
            updated_at=_ts(1, 9, 3),
            emitted_at=_ts(1, 9, 4),
            source_sequence=2,
            payload={
                "engagement_name": "SOX Readiness FY26",
                "status": "planning",
                "owner": "J. Harris",
                "issue_count": 1,
            },
        ),
    ]
    batch_2 = [
        _event(
            event_id="evt-inv-a1-upd",
            entity_name="invoice",
            op="update",
            tenant_id="tenant_alpha",
            entity_id="inv_a1",
            updated_at=_ts(3, 10, 15),
            emitted_at=_ts(3, 10, 16),
            source_sequence=5,
            payload={
                "customer_id": "cust_a1",
                "engagement_id": "eng_a1",
                "invoice_number": "A-1001",
                "invoice_amount": 12500.0,
                "currency": "USD",
                "status": "overdue",
                "due_date": "2026-04-05",
                "invoice_date": "2026-04-01",
            },
        ),
        _event(
            event_id="evt-inv-a1-upd",
            entity_name="invoice",
            op="update",
            tenant_id="tenant_alpha",
            entity_id="inv_a1",
            updated_at=_ts(3, 10, 15),
            emitted_at=_ts(3, 10, 17),
            source_sequence=5,
            payload={
                "customer_id": "cust_a1",
                "engagement_id": "eng_a1",
                "invoice_number": "A-1001",
                "invoice_amount": 12500.0,
                "currency": "USD",
                "status": "overdue",
                "due_date": "2026-04-05",
                "invoice_date": "2026-04-01",
            },
        ),
        _event(
            event_id="evt-inv-a2",
            entity_name="invoice",
            op="insert",
            tenant_id="tenant_alpha",
            entity_id="inv_a2",
            updated_at=_ts(3, 11, 0),
            emitted_at=_ts(3, 11, 2),
            source_sequence=6,
            payload={
                "customer_id": "cust_a1",
                "engagement_id": "eng_a1",
                "invoice_number": "A-1002",
                "invoice_amount": 4800.0,
                "currency": "USD",
                "status": "paid",
                "due_date": "2026-04-15",
                "invoice_date": "2026-04-03",
            },
        ),
        _event(
            event_id="evt-je-a1",
            entity_name="journal_entry",
            op="insert",
            tenant_id="tenant_alpha",
            entity_id="je_a1",
            updated_at=_ts(3, 11, 5),
            emitted_at=_ts(3, 11, 6),
            source_sequence=7,
            payload={
                "engagement_id": "eng_a1",
                "entry_type": "adjustment",
                "amount": 12500.0,
                "debit_account": "Accounts Receivable",
                "credit_account": "Revenue",
            },
        ),
        _event(
            event_id="evt-ctl-a1-upd",
            entity_name="control",
            op="update",
            tenant_id="tenant_alpha",
            entity_id="ctl_a1",
            updated_at=_ts(3, 11, 8),
            emitted_at=_ts(3, 11, 9),
            source_sequence=8,
            payload={
                "engagement_id": "eng_a1",
                "control_name": "Revenue cutoff review",
                "severity": "high",
                "status": "exception_open",
                "exception_count": 3,
                "owner": "L. Gomez",
            },
        ),
        _event(
            event_id="evt-inv-b1",
            entity_name="invoice",
            op="insert",
            tenant_id="tenant_beta",
            entity_id="inv_b1",
            updated_at=_ts(3, 11, 12),
            emitted_at=_ts(3, 11, 13),
            source_sequence=3,
            payload={
                "customer_id": "cust_b1",
                "engagement_id": "eng_b1",
                "invoice_number": "B-2001",
                "invoice_amount": 9300.0,
                "currency": "USD",
                "status": "sent",
                "due_date": "2026-04-28",
                "invoice_date": "2026-04-03",
            },
        ),
    ]
    batch_3 = [
        _event(
            event_id="evt-eng-a1-late",
            entity_name="engagement",
            op="update",
            tenant_id="tenant_alpha",
            entity_id="eng_a1",
            updated_at=_ts(2, 16, 0),
            emitted_at=_ts(5, 9, 0),
            source_sequence=4,
            payload={
                "engagement_name": "FY26 Northwind Audit",
                "status": "fieldwork",
                "owner": "A. Patel",
                "issue_count": 3,
            },
        ),
        _event(
            event_id="evt-eng-a1-new",
            entity_name="engagement",
            op="update",
            tenant_id="tenant_alpha",
            entity_id="eng_a1",
            updated_at=_ts(5, 8, 30),
            emitted_at=_ts(5, 9, 1),
            source_sequence=9,
            payload={
                "engagement_name": "FY26 Northwind Audit",
                "status": "active",
                "owner": "A. Patel",
                "issue_count": 4,
            },
        ),
        _event(
            event_id="evt-inv-b1-del",
            entity_name="invoice",
            op="delete",
            tenant_id="tenant_beta",
            entity_id="inv_b1",
            updated_at=_ts(6, 14, 0),
            emitted_at=_ts(6, 14, 2),
            source_sequence=4,
            payload={
                "customer_id": "cust_b1",
                "engagement_id": "eng_b1",
                "invoice_number": "B-2001",
                "invoice_amount": 9300.0,
                "currency": "USD",
                "status": "voided",
                "due_date": "2026-04-28",
                "invoice_date": "2026-04-03",
                "is_deleted": True,
            },
        ),
        _event(
            event_id="evt-doc-anchor",
            entity_name="control",
            op="insert",
            tenant_id="tenant_beta",
            entity_id="ctl_b1",
            updated_at=_ts(6, 14, 10),
            emitted_at=_ts(6, 14, 11),
            source_sequence=5,
            payload={
                "engagement_id": "eng_b1",
                "control_name": "Deferred revenue review",
                "severity": "medium",
                "status": "monitoring",
                "exception_count": 0,
                "owner": "N. Brooks",
            },
        ),
        _event(
            event_id="evt-cus-a1-upd",
            entity_name="customer",
            op="update",
            tenant_id="tenant_alpha",
            entity_id="cust_a1",
            updated_at=_ts(6, 15, 0),
            emitted_at=_ts(6, 15, 1),
            source_sequence=10,
            payload={
                "customer_name": "Northwind Audit LLP",
                "segment": "enterprise",
                "billing_country": "US",
            },
        ),
    ]
    return [batch_1, batch_2, batch_3]


def documents() -> list[DocumentRecord]:
    return [
        _doc(
            tenant_id="tenant_alpha",
            document_id="doc_alpha_policy_revrec",
            title="Revenue Recognition Policy",
            doc_type="policy",
            classification="confidential",
            retention_state="active",
            created_at=_ts(1, 8, 0),
            updated_at=_ts(4, 12, 0),
            source_uri="s3://tenant-alpha/policies/revenue-recognition-policy-v3.pdf",
            text=(
                "Purpose\n"
                "This policy defines when tenant_alpha recognizes software and audit platform revenue.\n\n"
                "Core rule\n"
                "Deferred revenue is recognized when contractual performance obligations are satisfied. "
                "Standalone onboarding work is recognized ratably over the service period unless the statement of work explicitly states otherwise.\n\n"
                "Evidence and review\n"
                "Controllers must retain signed contracts, approved billing schedules, and engagement completion evidence. "
                "Any exception above USD 10,000 requires director approval and linkage to the engagement record."
            ),
        ),
        _doc(
            tenant_id="tenant_alpha",
            document_id="doc_alpha_note_eng",
            title="Northwind Audit Engagement Notes",
            doc_type="engagement_note",
            classification="restricted",
            retention_state="active",
            created_at=_ts(4, 14, 0),
            updated_at=_ts(5, 16, 0),
            source_uri="s3://tenant-alpha/engagements/eng-a1/notes/april-fieldwork.txt",
            text=(
                "Fieldwork update\n"
                "The revenue cutoff walkthrough identified three open questions tied to shipment timing.\n\n"
                "Team assessment\n"
                "Two invoices remain unpaid and one requires follow-up with the controller. "
                "The client requested clarification on deferred revenue handling for onboarding services.\n\n"
                "Next action\n"
                "Escalate policy interpretation questions to technical accounting if the signed SOW includes milestones."
            ),
        ),
        _doc(
            tenant_id="tenant_alpha",
            document_id="doc_alpha_workpaper_ocr",
            title="Revenue Workpaper OCR Export",
            doc_type="workpaper",
            classification="confidential",
            retention_state="active",
            created_at=_ts(4, 8, 0),
            updated_at=_ts(5, 10, 30),
            source_uri="s3://tenant-alpha/workpapers/revenue/workpaper-ocr-export.txt",
            contains_table_like_text=True,
            text=(
                "Revenue walkthrough    OCR capture\n\n"
                "Observed table\n"
                "Line Item    Contract Ref    Proposed Treatment\n"
                "Onboarding services    SOW-77    Recognize over service period\n"
                "Platform subscription    MSA-22    Recognize monthly as services are delivered\n\n"
                "Reviewer note\n"
                "Numeric values in this OCR extract are not authoritative; trace exact balances back to the gold invoice tables."
            ),
        ),
        _doc(
            tenant_id="tenant_beta",
            document_id="doc_beta_policy_defrev",
            title="Deferred Revenue Accounting Policy",
            doc_type="policy",
            classification="confidential",
            retention_state="active",
            created_at=_ts(2, 7, 30),
            updated_at=_ts(6, 10, 0),
            source_uri="s3://tenant-beta/policies/deferred-revenue-accounting.md",
            text=(
                "Policy statement\n"
                "Deferred revenue remains on the balance sheet until the associated readiness and monitoring services are delivered.\n\n"
                "Interpretation\n"
                "Implementation fees are not recognized upfront when they are not distinct from the recurring monitoring service. "
                "The accounting team reviews bundled obligations quarterly.\n\n"
                "Controls\n"
                "The deferred revenue review control owner documents evidence in the engagement workpaper each month."
            ),
        ),
        _doc(
            tenant_id="tenant_beta",
            document_id="doc_beta_issue_summary",
            title="SOX Readiness Issue Summary",
            doc_type="issue_summary",
            classification="restricted",
            retention_state="active",
            created_at=_ts(6, 11, 0),
            updated_at=_ts(6, 11, 15),
            source_uri="s3://tenant-beta/issues/sox-readiness-summary.txt",
            text=(
                "Current issue summary\n"
                "No control exceptions are currently open. Monitoring continues for deferred revenue evidence completeness.\n\n"
                "Reminder\n"
                "If an auditor requests exact balances, route the request to the structured invoice and journal entry data products."
            ),
        ),
    ]


def write_sample_data(base_dir: Path) -> None:
    events_dir = base_dir / "events"
    docs_dir = base_dir / "documents"
    events_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for index, batch in enumerate(structured_event_batches(), start=1):
        batch_id = f"batch_{index:02d}"
        path = events_dir / f"{batch_id}.jsonl"
        write_jsonl(
            path,
            [
                event.model_dump(mode="json")
                | {
                    "batch_id": batch_id,
                    "payload_json": json.dumps(event.payload, sort_keys=True),
                }
                for event in batch
            ],
        )
        manifest.append(
            {
                "batch_id": batch_id,
                "path": str(path.relative_to(base_dir)),
                "record_count": len(batch),
                "min_emitted_at": min(event.emitted_at for event in batch).isoformat(),
                "max_emitted_at": max(event.emitted_at for event in batch).isoformat(),
            }
        )

    write_json(
        docs_dir / "documents.json",
        [document.model_dump(mode="json") for document in documents()],
    )
    write_json(base_dir / "manifest.json", {"structured_batches": manifest, "document_count": len(documents())})

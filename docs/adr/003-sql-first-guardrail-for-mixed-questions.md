# ADR-003: SQL-first guardrail for mixed questions

## Status

Accepted

## Context

When a question mixes exact-value intent ("what is the total overdue amount") with document context ("and what does the workpaper say about it"), the system must decide which source of truth owns the numerical answer.

In accounting and audit, presenting a number from an OCR-extracted workpaper as an authoritative balance is a compliance risk. Documents may contain draft figures, rounded estimates, or values from prior periods.

## Decision

Mixed questions are routed to the `mixed_guardrail` path, which executes SQL retrieval first. The SQL result anchors the exact answer. Document retrieval runs second and is used only for context, never as the source of a number.

## Rationale

- **Auditability**: Gold table values trace back through silver snapshots to bronze CDC events, each carrying a `lineage_ref`. Document chunks do not have this provenance chain for numerical values.
- **Correctness**: The gold invoice summary is computed from OLTP source-of-record data via a governed medallion pipeline. OCR-extracted tables may contain recognition errors, rounding, or stale values.
- **Guardrail enforcement**: `enforce_exact_finance_from_sql()` rejects any mixed-guardrail response that does not include an SQL-backed answer path. This makes the contract programmatically enforceable, not just a prompt instruction.
- **User trust**: The response contract injects a visible warning when the mixed path is used, making the provenance of numbers transparent.

## Trade-offs

- Questions where the document genuinely contains the most current number (e.g., a manually updated workpaper not yet reflected in OLTP) will show stale SQL data. This is the correct behavior for a compliance-first platform; the document context will still surface alongside it.
- The mixed path adds one extra node (SQL retrieval) compared to pure RAG, increasing latency by the Trino query time (~100-300ms).

## When to revisit

- If the platform adds a "document as source of truth" flag for specific workpaper types, the guardrail could selectively allow document-sourced numbers for those types.
- If Caseware moves to real-time OLTP-to-gold streaming (sub-second freshness), the staleness concern for SQL diminishes further.

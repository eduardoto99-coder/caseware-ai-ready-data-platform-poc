from __future__ import annotations

from typing import Any


def enforce_tenant_boundary(
    *, authenticated_tenant_id: str, request_tenant_id: str
) -> None:
    if authenticated_tenant_id != request_tenant_id:
        raise PermissionError(
            "Tenant mismatch: the request tenant scope does not match the authenticated tenant."
        )


def enforce_citation_minimum(
    response: dict[str, Any], minimum_citations: int = 1
) -> None:
    citations = response.get("citations", [])
    if len(citations) < minimum_citations:
        raise ValueError("The answer does not meet the minimum citation threshold.")


def enforce_exact_finance_from_sql(
    *, question_route: str, answer_payload: dict[str, Any]
) -> None:
    if question_route == "mixed_guardrail" and not answer_payload.get("sql"):
        raise ValueError(
            "Mixed-guardrail finance questions must include an SQL-backed answer path."
        )


def enforce_context_budget(
    chunks: list[dict[str, Any]], max_chars: int = 8000
) -> list[dict[str, Any]]:
    # Keep the highest-ranked chunks in order until the prompt budget is exhausted.
    budget = 0
    kept: list[dict[str, Any]] = []
    for chunk in chunks:
        text = str(chunk.get("text", ""))
        if budget + len(text) > max_chars:
            break
        kept.append(chunk)
        budget += len(text)
    return kept

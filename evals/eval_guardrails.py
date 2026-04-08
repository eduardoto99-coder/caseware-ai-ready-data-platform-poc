"""Guardrail contract compliance evaluation.

Validates that enforcement functions correctly accept or reject
payloads across route types, testing the boundary conditions that
matter in production: tenant mismatch, missing citations, mixed
routes without SQL, and context budget overflow.
"""

from __future__ import annotations

from typing import Any

from caseware_poc.agents.guardrails import (
    enforce_citation_minimum,
    enforce_context_budget,
    enforce_exact_finance_from_sql,
    enforce_tenant_boundary,
)
from caseware_poc.guardrails.registry import GuardrailRegistry


def _run_case(name: str, fn: Any, expect_pass: bool) -> dict[str, Any]:
    try:
        fn()
        passed = True
    except (PermissionError, ValueError):
        passed = False

    correct = passed == expect_pass
    return {
        "name": name,
        "expected_pass": expect_pass,
        "actual_pass": passed,
        "correct": correct,
    }


def _required_fields_present(
    required_fields: list[str], payload: dict[str, object]
) -> bool:
    return all(
        field in payload and payload[field] not in (None, [])
        for field in required_fields
    )


def evaluate_guardrails() -> dict[str, Any]:
    registry = GuardrailRegistry()
    contracts = registry.answer_contracts
    cases = [
        # Tenant boundary
        _run_case(
            "tenant_match",
            lambda: enforce_tenant_boundary(
                authenticated_tenant_id="t1", request_tenant_id="t1"
            ),
            expect_pass=True,
        ),
        _run_case(
            "tenant_mismatch",
            lambda: enforce_tenant_boundary(
                authenticated_tenant_id="t1", request_tenant_id="t2"
            ),
            expect_pass=False,
        ),
        # Citation minimum
        _run_case(
            "citations_present",
            lambda: enforce_citation_minimum(
                {"citations": [{"id": "c1"}]}, minimum_citations=1
            ),
            expect_pass=True,
        ),
        _run_case(
            "citations_missing",
            lambda: enforce_citation_minimum({"citations": []}, minimum_citations=1),
            expect_pass=False,
        ),
        _run_case(
            "citations_not_required_for_sql",
            lambda: enforce_citation_minimum({"citations": []}, minimum_citations=0),
            expect_pass=True,
        ),
        # SQL-first exactness
        _run_case(
            "mixed_with_sql",
            lambda: enforce_exact_finance_from_sql(
                question_route="mixed_guardrail",
                answer_payload={"sql": [{"total": 100}], "citations": []},
            ),
            expect_pass=True,
        ),
        _run_case(
            "mixed_without_sql",
            lambda: enforce_exact_finance_from_sql(
                question_route="mixed_guardrail",
                answer_payload={"sql": [], "citations": [{"id": "c1"}]},
            ),
            expect_pass=False,
        ),
        _run_case(
            "rag_route_no_sql_ok",
            lambda: enforce_exact_finance_from_sql(
                question_route="rag",
                answer_payload={"sql": [], "citations": [{"id": "c1"}]},
            ),
            expect_pass=True,
        ),
        # Context budget
        _run_case(
            "under_budget",
            lambda: enforce_context_budget(
                [{"text": "a" * 100}, {"text": "b" * 100}], max_chars=8000
            ),
            expect_pass=True,
        ),
    ]

    contract_cases: list[tuple[str, list[str], dict[str, object], bool]] = [
        (
            "sql_contract_valid",
            contracts["exact_accounting_sql"]["required_fields"],
            {
                "answer": "42 invoices are overdue.",
                "sql": "SELECT ...",
                "records": [{"invoice_id": "i1"}],
                "route": "sql",
                "guardrail_context": {"rule_ids": ["tool_routing"]},
            },
            True,
        ),
        (
            "sql_contract_missing_sql",
            contracts["exact_accounting_sql"]["required_fields"],
            {
                "answer": "42 invoices are overdue.",
                "records": [{"invoice_id": "i1"}],
                "route": "sql",
                "guardrail_context": {"rule_ids": ["tool_routing"]},
            },
            False,
        ),
        (
            "rag_contract_valid",
            contracts["tenant_safe_policy_rag"]["required_fields"],
            {
                "answer": "The policy recognizes onboarding revenue over time.",
                "citations": [{"id": "doc1"}],
                "route": "rag",
                "guardrail_context": {"rule_ids": ["retrieval_grounding"]},
            },
            True,
        ),
        (
            "rag_contract_missing_citations",
            contracts["tenant_safe_policy_rag"]["required_fields"],
            {
                "answer": "The policy recognizes onboarding revenue over time.",
                "route": "rag",
                "guardrail_context": {"rule_ids": ["retrieval_grounding"]},
            },
            False,
        ),
        (
            "mixed_contract_valid",
            contracts["precision_guardrail"]["required_fields"],
            {
                "answer": "The overdue amount is 100. The workpaper notes delayed approvals.",
                "warnings": ["SQL is the source of truth for the amount."],
                "citations": [{"id": "doc1"}],
                "route": "mixed_guardrail",
                "guardrail_context": {"rule_ids": ["response_guardrail"]},
            },
            True,
        ),
        (
            "mixed_contract_missing_warning",
            contracts["precision_guardrail"]["required_fields"],
            {
                "answer": "The overdue amount is 100.",
                "citations": [{"id": "doc1"}],
                "route": "mixed_guardrail",
                "guardrail_context": {"rule_ids": ["response_guardrail"]},
            },
            False,
        ),
    ]
    cases.extend(
        {
            "name": name,
            "expected_pass": expect_pass,
            "actual_pass": _required_fields_present(required_fields, payload),
            "correct": _required_fields_present(required_fields, payload)
            == expect_pass,
        }
        for name, required_fields, payload, expect_pass in contract_cases
    )

    # Context budget returns a list, so test its trimming behavior separately
    over_budget_chunks = [{"text": "x" * 5000}, {"text": "y" * 5000}]
    trimmed = enforce_context_budget(over_budget_chunks, max_chars=8000)
    cases.append(
        {
            "name": "budget_trims_excess",
            "expected_pass": True,
            "actual_pass": len(trimmed) == 1,
            "correct": len(trimmed) == 1,
        }
    )

    total = len(cases)
    correct = sum(1 for c in cases if c["correct"])
    failures = [c for c in cases if not c["correct"]]

    return {
        "compliance_rate": correct / total if total else 0.0,
        "total": total,
        "correct": correct,
        "failures": failures,
    }


if __name__ == "__main__":
    report = evaluate_guardrails()
    print(
        f"Guardrail compliance: {report['compliance_rate']:.1%} ({report['correct']}/{report['total']})"
    )
    if report["failures"]:
        print("\nFailed cases:")
        for f in report["failures"]:
            print(
                f"  {f['name']}: expected_pass={f['expected_pass']} actual_pass={f['actual_pass']}"
            )
    else:
        print("All guardrail contracts passed.")

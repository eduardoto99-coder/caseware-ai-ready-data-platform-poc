import pytest

from caseware_poc.agents.guardrails import (
    enforce_context_budget,
    enforce_exact_finance_from_sql,
    enforce_tenant_boundary,
)
from caseware_poc.agents.prompt_loader import PromptAssetLoader
from caseware_poc.common.paths import project_root
from caseware_poc.guardrails.registry import GuardrailRegistry


def test_guardrail_registry_loads_skills_and_rules() -> None:
    registry = GuardrailRegistry()
    payload = registry.as_payload()

    assert "exact_accounting_sql" in payload["skills"]
    assert "tenant_safe_policy_rag" in payload["skills"]
    assert "mixed_guardrail" in payload["routing"]["skill_bindings"]
    assert payload["response"]["require_warning_for_guardrail"] is True


def test_guardrail_registry_builds_context_for_mixed_route() -> None:
    registry = GuardrailRegistry()
    context = registry.context_for(
        route="mixed_guardrail", skill_id="precision_guardrail"
    )

    assert context.skill_id == "precision_guardrail"
    assert "guardrails/rules/routing.md" in context.rule_files
    assert "guardrails/rules/retrieval.md" in context.rule_files
    assert "guardrails/rules/response.md" in context.rule_files


def test_prompt_asset_loader_reads_guardrail_assets() -> None:
    loader = PromptAssetLoader(project_root())

    skill = loader.load_skill("exact_accounting_sql")
    rules = loader.load_rules("llm_guardrails")
    template = loader.load_template("trino_overdue_query")

    assert "gold_invoice_summary" in skill
    assert "routing" in rules
    assert "retrieval" in rules
    assert "tenant_id = ?" in template


def test_enforce_tenant_boundary_raises_on_mismatch() -> None:
    with pytest.raises(PermissionError):
        enforce_tenant_boundary(
            authenticated_tenant_id="tenant_alpha", request_tenant_id="tenant_beta"
        )


def test_enforce_exact_finance_from_sql_rejects_mixed_route_without_sql() -> None:
    with pytest.raises(ValueError):
        enforce_exact_finance_from_sql(
            question_route="mixed_guardrail",
            answer_payload={"sql": [], "citations": [{"id": "doc_1"}]},
        )


def test_enforce_context_budget_keeps_ranked_order_until_limit() -> None:
    chunks = [
        {"id": "first", "text": "a" * 3000},
        {"id": "second", "text": "b" * 3000},
        {"id": "third", "text": "c" * 3000},
    ]

    kept = enforce_context_budget(chunks, max_chars=6500)

    assert [chunk["id"] for chunk in kept] == ["first", "second"]

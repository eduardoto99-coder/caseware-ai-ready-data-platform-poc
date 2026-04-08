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
    context = registry.context_for(route="mixed_guardrail", skill_id="precision_guardrail")

    assert context.skill_id == "precision_guardrail"
    assert "guardrails/rules/routing.yaml" in context.rule_files
    assert "guardrails/rules/retrieval.yaml" in context.rule_files
    assert "guardrails/rules/response.yaml" in context.rule_files


def test_prompt_asset_loader_reads_guardrail_assets() -> None:
    loader = PromptAssetLoader(project_root())

    skill = loader.load_skill("exact_accounting_sql")
    rules = loader.load_rules("llm_guardrails")
    template = loader.load_template("trino_overdue_query")

    assert "gold_invoice_summary" in skill
    assert "routing" in rules
    assert "retrieval" in rules
    assert "tenant_id = ?" in template

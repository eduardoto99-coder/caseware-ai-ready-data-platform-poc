from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from caseware_poc.common.models import GuardrailContext
from caseware_poc.common.paths import project_root


@dataclass(frozen=True, slots=True)
class GuardrailRule:
    rule_id: str
    title: str
    description: str
    applies_to_routes: list[str]
    applies_to_skills: list[str]
    enforcement_points: list[str]
    source_file: str


@dataclass(frozen=True, slots=True)
class GuardrailSkill:
    skill_id: str
    title: str
    purpose: str
    owned_route: str
    use_for: list[str]
    required_outputs: list[str]
    prohibited_behaviors: list[str]
    source_file: str
    body: str


class GuardrailRegistry:
    def __init__(self, root_dir: Path | None = None) -> None:
        candidate_root = root_dir or project_root()
        if not (candidate_root / "guardrails" / "skills").exists():
            candidate_root = project_root()
        self.root_dir = candidate_root
        self.skills_dir = self.root_dir / "guardrails" / "skills"
        self.rules_dir = self.root_dir / "guardrails" / "rules"
        self.contracts_dir = self.root_dir / "guardrails" / "contracts"
        self.context_file = self.root_dir / "guardrails" / "context" / "system_context.txt"
        self._skills = self._load_skills()
        self._rules = self._load_rules()
        self.system_context = self.context_file.read_text(encoding="utf-8").strip()

    def context_for(self, *, route: str, skill_id: str) -> GuardrailContext:
        skill = self._skills[skill_id]
        # Return the concrete skill and rule files that governed the answer so callers can
        # expose policy provenance during reviews or interviews.
        matching_rules = [
            rule
            for rule in self._rules.values()
            if route in rule.applies_to_routes
            and (not rule.applies_to_skills or skill_id in rule.applies_to_skills)
        ]
        return GuardrailContext(
            skill_id=skill.skill_id,
            skill_file=skill.source_file,
            rule_ids=[rule.rule_id for rule in matching_rules],
            rule_files=[rule.source_file for rule in matching_rules],
            enforcement_points=[
                enforcement
                for rule in matching_rules
                for enforcement in rule.enforcement_points
            ],
        )

    def _load_skills(self) -> dict[str, GuardrailSkill]:
        skills: dict[str, GuardrailSkill] = {}
        for skill_file in sorted(self.skills_dir.glob("*.yaml")):
            payload = yaml.safe_load(skill_file.read_text(encoding="utf-8")) or {}
            skills[skill_file.stem] = GuardrailSkill(
                skill_id=payload["skill_id"],
                title=payload["title"],
                purpose=payload["purpose"],
                owned_route=payload["owned_route"],
                use_for=list(payload.get("use_for", [])),
                required_outputs=list(payload.get("required_outputs", [])),
                prohibited_behaviors=list(payload.get("prohibited_behaviors", [])),
                source_file=str(skill_file.relative_to(self.root_dir)),
                body=str(payload.get("body", "")).strip(),
            )
        return skills

    def _load_rules(self) -> dict[str, GuardrailRule]:
        routing_file = self.rules_dir / "routing.yaml"
        retrieval_file = self.rules_dir / "retrieval.yaml"
        response_file = self.rules_dir / "response.yaml"
        routing = yaml.safe_load(routing_file.read_text(encoding="utf-8"))["routing"]
        retrieval = yaml.safe_load(retrieval_file.read_text(encoding="utf-8"))["retrieval"]
        response = yaml.safe_load(response_file.read_text(encoding="utf-8"))["response"]
        return {
            "tool_routing": GuardrailRule(
                rule_id="tool_routing",
                title="Tool Routing Discipline",
                description="Use SQL for governed exact facts and RAG for narrative context.",
                applies_to_routes=["sql", "rag", "mixed_guardrail"],
                applies_to_skills=[],
                enforcement_points=["route_selection", "skill_binding", "structured_truth_priority"],
                source_file=str(routing_file.relative_to(self.root_dir)),
            ),
            "retrieval_grounding": GuardrailRule(
                rule_id="retrieval_grounding",
                title="Retrieval Grounding",
                description=f"Require filters {retrieval['required_metadata_filters']} and citations for document answers.",
                applies_to_routes=["rag", "mixed_guardrail"],
                applies_to_skills=["tenant_safe_policy_rag", "precision_guardrail"],
                enforcement_points=["tenant_filtering", "retention_filtering", "citation_requirement"],
                source_file=str(retrieval_file.relative_to(self.root_dir)),
            ),
            "response_guardrail": GuardrailRule(
                rule_id="response_guardrail",
                title="Response Guardrail",
                description=response["guardrail_warning_message"],
                applies_to_routes=["rag", "mixed_guardrail"],
                applies_to_skills=["tenant_safe_policy_rag", "precision_guardrail"],
                enforcement_points=["warning_injection", "exactness_protection", "insufficient_grounding_handling"],
                source_file=str(response_file.relative_to(self.root_dir)),
            ),
        }

    @property
    def routing_terms(self) -> dict[str, Any]:
        return self._load_rule_payload("routing")

    @property
    def retrieval_policy(self) -> dict[str, Any]:
        return self._load_rule_payload("retrieval")

    @property
    def response_policy(self) -> dict[str, Any]:
        return self._load_rule_payload("response")

    @property
    def tenant_isolation_policy(self) -> dict[str, Any]:
        return self._load_rule_payload("tenant_isolation")

    @property
    def tooling_policy(self) -> dict[str, Any]:
        return self._load_rule_payload("tooling")

    @property
    def context_budget_policy(self) -> dict[str, Any]:
        return self._load_rule_payload("context_budget")

    @property
    def answer_contracts(self) -> dict[str, Any]:
        contract_file = self.contracts_dir / "answer_contracts.yaml"
        if not contract_file.exists():
            return {}
        return yaml.safe_load(contract_file.read_text(encoding="utf-8"))["answer_contracts"]

    def skills_payload(self) -> dict[str, Any]:
        return {
            skill_id: {
                "title": skill.title,
                "purpose": skill.purpose,
                "owned_route": skill.owned_route,
                "use_for": skill.use_for,
                "required_outputs": skill.required_outputs,
                "prohibited_behaviors": skill.prohibited_behaviors,
                "source_file": skill.source_file,
            }
            for skill_id, skill in self._skills.items()
        }

    def as_payload(self) -> dict[str, Any]:
        return {
            "system_context": self.system_context,
            "skills": self.skills_payload(),
            "routing": self.routing_terms,
            "retrieval": self.retrieval_policy,
            "response": self.response_policy,
            "tenant_isolation": self.tenant_isolation_policy,
            "tooling": self.tooling_policy,
            "context_budget": self.context_budget_policy,
            "answer_contracts": self.answer_contracts,
        }

    def _load_rule_payload(self, rule_name: str) -> dict[str, Any]:
        rule_file = self.rules_dir / f"{rule_name}.yaml"
        if not rule_file.exists():
            return {}
        return yaml.safe_load(rule_file.read_text(encoding="utf-8"))[rule_name]

from __future__ import annotations

from caseware_poc.guardrails.registry import GuardrailRegistry

_registry = GuardrailRegistry()

SKILLS = {
    skill_id: {
        "description": skill.purpose,
        "use_for": skill.use_for,
        "output_contract": skill.required_outputs,
        "prohibited_behaviors": skill.prohibited_behaviors,
        "source_file": skill.source_file,
    }
    for skill_id, skill in _registry._skills.items()
}

ROUTING_RULES = {
    "sql": "Use when the prompt asks for exact values, filters, aggregations, invoice state, engagement state, or control metrics.",
    "rag": "Use when the prompt asks what a policy, note, workpaper, or issue summary says.",
    "mixed_guardrail": _registry.routing_terms["mixed_route_warning"],
}

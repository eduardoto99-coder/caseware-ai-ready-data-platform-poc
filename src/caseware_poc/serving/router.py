from __future__ import annotations

from caseware_poc.common.models import RouteDecision
from caseware_poc.guardrails.registry import GuardrailRegistry

_registry = GuardrailRegistry()


def route_question(question: str) -> RouteDecision:
    routing = _registry.routing_terms
    normalized = question.lower()
    sql_hits = [term for term in routing["sql_terms"] if term in normalized]
    rag_hits = [term for term in routing["rag_terms"] if term in normalized]
    precision_doc_hits = [term for term in routing["precision_doc_terms"] if term in normalized]

    # When exact-value intent and document cues coexist, route to the guarded mixed path
    # so SQL remains the source of truth and documents stay contextual.
    if sql_hits and precision_doc_hits:
        return RouteDecision(
            route="mixed_guardrail",
            skill=routing["skill_bindings"]["mixed_guardrail"],
            reason="The question mixes exact-value intent with document-oriented cues; SQL must own precise answers.",
            rules_fired=[
                "exact_value_terms_detected",
                "document_context_terms_detected",
                "precision_guardrail_required",
            ],
        )
    if rag_hits and not sql_hits:
        return RouteDecision(
            route="rag",
            skill=routing["skill_bindings"]["rag"],
            reason="The question asks for narrative or policy context better served by tenant-scoped retrieval.",
            rules_fired=["narrative_terms_detected", "rag_skill_selected"],
        )
    return RouteDecision(
        route="sql",
        skill=routing["skill_bindings"]["sql"],
        reason="The question requests exact operational or financial data available in gold tables.",
        rules_fired=["structured_terms_detected", "sql_skill_selected"],
    )

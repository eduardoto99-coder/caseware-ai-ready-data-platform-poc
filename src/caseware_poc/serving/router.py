from __future__ import annotations

import re
from functools import lru_cache

from caseware_poc.common.models import RouteDecision
from caseware_poc.guardrails.registry import GuardrailRegistry


class RouteService:
    def __init__(self, registry: GuardrailRegistry | None = None) -> None:
        self.registry = registry or GuardrailRegistry()

    def route_question(self, question: str) -> RouteDecision:
        routing = self.registry.routing_terms
        normalized = question.lower()
        sql_hits = self._matching_terms(normalized, routing["sql_terms"])
        rag_hits = self._matching_terms(normalized, routing["rag_terms"])
        precision_doc_hits = self._matching_terms(
            normalized, routing["precision_doc_terms"]
        )

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

    @staticmethod
    def _matching_terms(normalized_question: str, terms: list[str]) -> list[str]:
        return [
            term
            for term in terms
            if re.search(RouteService._term_pattern(term), normalized_question)
        ]

    @staticmethod
    def _term_pattern(term: str) -> str:
        escaped = re.escape(term.strip())
        normalized = escaped.replace(r"\ ", r"\s+")
        return r"\b" + normalized + r"\b"


@lru_cache(maxsize=1)
def _default_route_service() -> RouteService:
    return RouteService()


def route_question(
    question: str, *, registry: GuardrailRegistry | None = None
) -> RouteDecision:
    service = (
        RouteService(registry) if registry is not None else _default_route_service()
    )
    return service.route_question(question)

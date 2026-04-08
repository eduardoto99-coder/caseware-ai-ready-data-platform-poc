from __future__ import annotations

from time import perf_counter

from caseware_poc.common.models import QueryResponse, RouteDecision
from caseware_poc.common.runtime import PlatformRuntime
from caseware_poc.guardrails.registry import GuardrailRegistry
from caseware_poc.rag.index import SharedVectorIndex


class RagAnswerService:
    def __init__(
        self,
        runtime: PlatformRuntime,
        vector_index: SharedVectorIndex,
        guardrail_registry: GuardrailRegistry,
    ) -> None:
        self.runtime = runtime
        self.vector_index = vector_index
        self.guardrail_registry = guardrail_registry

    def answer(self, *, tenant_id: str, question: str, route: RouteDecision) -> QueryResponse:
        started = perf_counter()
        retrieval_policy = self.guardrail_registry.retrieval_policy
        metadata_filters = dict(retrieval_policy.get("fixed_filters", {}))
        lowered = question.lower()
        for doc_type, hints in retrieval_policy.get("doc_type_hints", {}).items():
            if any(hint in lowered for hint in hints):
                metadata_filters["doc_type"] = doc_type
                break
        citations = self.vector_index.search(
            question=question,
            tenant_id=tenant_id,
            top_k=int(retrieval_policy.get("max_results", self.runtime.config.max_retrieval_results)),
            metadata_filters=metadata_filters,
            ranking_policy=retrieval_policy.get("ranking", {}),
        )
        answer = self._compose_answer(question, citations)
        latency_ms = round((perf_counter() - started) * 1000, 2)
        self.runtime.logger.emit(
            "rag_answer_completed",
            tenant_id=tenant_id,
            question=question,
            route=route.route,
            retrieval_latency_ms=latency_ms,
            metadata_filters=metadata_filters,
            retrieved_chunk_ids=[citation.chunk_id for citation in citations],
            attribution_uris=[citation.source_uri for citation in citations],
        )
        warnings = []
        if not citations:
            warnings.append(self.guardrail_registry.response_policy["insufficient_grounding_message"])
        return QueryResponse(
            tenant_id=tenant_id,
            question=question,
            route=route,
            answer=answer,
            citations=citations,
            warnings=warnings,
        )

    @staticmethod
    def _compose_answer(question: str, citations: list) -> str:
        if not citations:
            return "No grounded document evidence was found for the tenant-scoped query."
        summary_lines = []
        for citation in citations[:2]:
            first_sentence = citation.text.split(". ")[0].strip()
            summary_lines.append(f"{citation.title}: {first_sentence}.")
        return " ".join(summary_lines)

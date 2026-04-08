from __future__ import annotations

from time import perf_counter

from caseware_poc.common.models import QueryResponse, RouteDecision
from caseware_poc.common.runtime import PlatformRuntime
from caseware_poc.rag.index import SharedVectorIndex


class RagAnswerService:
    def __init__(self, runtime: PlatformRuntime, vector_index: SharedVectorIndex) -> None:
        self.runtime = runtime
        self.vector_index = vector_index

    def answer(self, *, tenant_id: str, question: str, route: RouteDecision) -> QueryResponse:
        started = perf_counter()
        metadata_filters = {"retention_state": "active"}
        lowered = question.lower()
        if "policy" in lowered:
            metadata_filters["doc_type"] = "policy"
        elif any(term in lowered for term in ["workpaper", "ocr", "table"]):
            metadata_filters["doc_type"] = "workpaper"
        elif "note" in lowered:
            metadata_filters["doc_type"] = "engagement_note"
        citations = self.vector_index.search(
            question=question,
            tenant_id=tenant_id,
            top_k=self.runtime.config.max_retrieval_results,
            metadata_filters=metadata_filters,
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
            warnings.append("No active tenant-scoped documents matched the query.")
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

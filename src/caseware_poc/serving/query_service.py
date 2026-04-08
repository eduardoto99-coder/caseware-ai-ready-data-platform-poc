from __future__ import annotations

from caseware_poc.common.models import QueryResponse
from caseware_poc.common.runtime import PlatformRuntime
from caseware_poc.rag.service import RagAnswerService
from caseware_poc.serving.router import route_question
from caseware_poc.serving.sql_service import StructuredQueryService


class QueryOrchestrator:
    def __init__(
        self,
        runtime: PlatformRuntime,
        sql_service: StructuredQueryService,
        rag_service: RagAnswerService,
    ) -> None:
        self.runtime = runtime
        self.sql_service = sql_service
        self.rag_service = rag_service

    def answer(self, *, tenant_id: str, question: str) -> QueryResponse:
        route = route_question(question)
        if route.route == "sql":
            return self.sql_service.answer(tenant_id=tenant_id, question=question, route=route)
        if route.route == "rag":
            return self.rag_service.answer(tenant_id=tenant_id, question=question, route=route)

        guarded = self.sql_service.answer(tenant_id=tenant_id, question=question, route=route)
        doc_context = self.rag_service.answer(tenant_id=tenant_id, question=question, route=route)
        guarded.warnings.append(
            "Guardrail applied: exact values are sourced from gold tables; document chunks are returned only as context."
        )
        guarded.citations = doc_context.citations
        guarded.answer = f"{guarded.answer} Document context: {doc_context.answer}"
        return guarded

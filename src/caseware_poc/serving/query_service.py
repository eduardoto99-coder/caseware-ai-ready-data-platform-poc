from __future__ import annotations

from caseware_poc.common.models import QueryResponse
from caseware_poc.common.runtime import PlatformRuntime
from caseware_poc.guardrails.registry import GuardrailRegistry
from caseware_poc.rag.service import RagAnswerService
from caseware_poc.serving.router import route_question
from caseware_poc.serving.sql_service import StructuredQueryService


class QueryOrchestrator:
    def __init__(
        self,
        runtime: PlatformRuntime,
        sql_service: StructuredQueryService,
        rag_service: RagAnswerService,
        guardrail_registry: GuardrailRegistry,
    ) -> None:
        self.runtime = runtime
        self.sql_service = sql_service
        self.rag_service = rag_service
        self.guardrail_registry = guardrail_registry

    def answer(self, *, tenant_id: str, question: str) -> QueryResponse:
        route = route_question(question)
        context = self.guardrail_registry.context_for(route=route.route, skill_id=route.skill)
        if route.route == "sql":
            response = self.sql_service.answer(tenant_id=tenant_id, question=question, route=route)
            response.guardrail_context = context
            return response
        if route.route == "rag":
            response = self.rag_service.answer(tenant_id=tenant_id, question=question, route=route)
            response.guardrail_context = context
            return response

        guarded = self.sql_service.answer(tenant_id=tenant_id, question=question, route=route)
        doc_context = self.rag_service.answer(tenant_id=tenant_id, question=question, route=route)
        guarded.warnings.append(self.guardrail_registry.response_policy["guardrail_warning_message"])
        guarded.citations = doc_context.citations
        guarded.answer = f"{guarded.answer} Document context: {doc_context.answer}"
        guarded.guardrail_context = context
        return guarded

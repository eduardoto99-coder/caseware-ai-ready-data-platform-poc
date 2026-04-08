from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from caseware_poc.agents.guardrails import (
    enforce_citation_minimum,
    enforce_context_budget,
    enforce_exact_finance_from_sql,
    enforce_tenant_boundary,
)
from caseware_poc.agents.prompt_loader import PromptAssetLoader
from caseware_poc.integrations.bedrock_runtime import BedrockAnswerSynthesizer
from caseware_poc.integrations.opensearch_vector_store import OpenSearchDocumentIndex
from caseware_poc.integrations.trino_client import TrinoServingClient
from caseware_poc.observability.cloudwatch_metrics import emit_query_metrics
from caseware_poc.observability.langfuse_tracer import LangfuseTracer
from caseware_poc.serving.router import RouteService


class AgentState(TypedDict, total=False):
    tenant_id: str
    authenticated_tenant_id: str
    question: str
    route: Literal["sql", "rag", "mixed_guardrail"]
    route_skill: str
    route_reason: str
    route_rules_fired: list[str]
    retrieved_chunks: list[dict[str, Any]]
    retrieval_metrics: dict[str, float]
    sql_rows: list[dict[str, Any]]
    answer: dict[str, Any]
    node_timings: dict[str, float]
    token_usage: dict[str, int]


class ReferenceLangGraphAgent:
    """LangGraph workflow used in this repo."""

    def __init__(
        self,
        *,
        repo_root: Path,
        trino_client: TrinoServingClient,
        opensearch_index: OpenSearchDocumentIndex,
        bedrock_client: BedrockAnswerSynthesizer,
        tracer: LangfuseTracer,
        router: RouteService | None = None,
    ) -> None:
        self.assets = PromptAssetLoader(repo_root)
        self.trino_client = trino_client
        self.opensearch_index = opensearch_index
        self.bedrock_client = bedrock_client
        self.tracer = tracer
        self.router = router or RouteService()

    def build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("validate_tenant", self.validate_tenant)
        graph.add_node("route", self.route)
        graph.add_node("sql_retrieval", self.sql_retrieval)
        graph.add_node("rag_retrieval", self.rag_retrieval)
        graph.add_node("synthesize", self.synthesize)
        graph.add_node("guardrails", self.guardrails)

        graph.set_entry_point("validate_tenant")
        graph.add_edge("validate_tenant", "route")
        # Mixed questions intentionally go through SQL first so exact values are anchored
        # before document context is added in later nodes.
        graph.add_conditional_edges(
            "route",
            self.route_selector,
            {
                "sql_retrieval": "sql_retrieval",
                "rag_retrieval": "rag_retrieval",
                "mixed_guardrail": "sql_retrieval",
            },
        )
        graph.add_conditional_edges(
            "sql_retrieval",
            self.post_sql_selector,
            {
                "rag_retrieval": "rag_retrieval",
                "synthesize": "synthesize",
            },
        )
        graph.add_edge("rag_retrieval", "synthesize")
        graph.add_edge("synthesize", "guardrails")
        graph.add_edge("guardrails", END)
        return graph.compile()

    def validate_tenant(self, state: AgentState) -> AgentState:
        start = time.perf_counter()
        try:
            enforce_tenant_boundary(
                authenticated_tenant_id=state["authenticated_tenant_id"],
                request_tenant_id=state["tenant_id"],
            )
            return state
        finally:
            self._record_timing(state, "validate_tenant", start)

    def route(self, state: AgentState) -> AgentState:
        start = time.perf_counter()
        try:
            decision = self.router.route_question(state["question"])
            state["route"] = decision.route
            state["route_skill"] = decision.skill
            state["route_reason"] = decision.reason
            state["route_rules_fired"] = decision.rules_fired
            return state
        finally:
            self._record_timing(state, "route", start)

    @staticmethod
    def route_selector(state: AgentState) -> str:
        if state["route"] == "rag":
            return "rag_retrieval"
        if state["route"] == "mixed_guardrail":
            return "mixed_guardrail"
        return "sql_retrieval"

    @staticmethod
    def post_sql_selector(state: AgentState) -> str:
        if state["route"] == "mixed_guardrail":
            return "rag_retrieval"
        return "synthesize"

    def sql_retrieval(self, state: AgentState) -> AgentState:
        start = time.perf_counter()
        try:
            sql_template = self.assets.load_template("trino_overdue_query")
            state["sql_rows"] = self.trino_client.query_gold_product(
                tenant_id=state["tenant_id"],
                sql=sql_template,
            )
            return state
        finally:
            self._record_timing(state, "sql_retrieval", start)

    def rag_retrieval(self, state: AgentState) -> AgentState:
        start = time.perf_counter()
        try:
            top_k = self.assets.load_rules("llm_guardrails")["retrieval"]["max_results"]
            max_chars = self.assets.load_rules("context_budget")["context_budget"][
                "max_total_chars"
            ]
            response = self.opensearch_index.tenant_scoped_search(
                tenant_id=state["tenant_id"],
                query_text=state["question"],
                top_k=top_k,
            )
            hits = response.get("hits", {}).get("hits", [])
            # The index already applied tenant and retention filters; this step only reshapes
            # the ranked hits into the chunk payload used by synthesis.
            chunks = [
                {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "text": hit["_source"]["chunk_text"],
                    "source_uri": hit["_source"]["source_uri"],
                }
                for hit in hits
            ]
            kept_chunks = enforce_context_budget(chunks, max_chars=max_chars)
            state["retrieved_chunks"] = kept_chunks
            state["retrieval_metrics"] = {
                "chunks_returned": float(len(hits)),
                "chunks_kept": float(len(kept_chunks)),
                "chunk_budget_chars": float(max_chars),
                "budget_used_chars": float(
                    sum(len(chunk["text"]) for chunk in kept_chunks)
                ),
                "top_hit_score": float(
                    max((chunk["score"] for chunk in chunks), default=0.0)
                ),
            }
            return state
        finally:
            self._record_timing(state, "rag_retrieval", start)

    def synthesize(self, state: AgentState) -> AgentState:
        start = time.perf_counter()
        try:
            skill_name = {
                "sql": "exact_accounting_sql",
                "rag": "tenant_safe_policy_rag",
                "mixed_guardrail": "precision_guardrail",
            }[state["route"]]
            # Prompt assets stay in repo files so the behavior is easy to review and version.
            system_prompt = "\n\n".join(
                [
                    self.assets.load_system_context(),
                    self.assets.load_skill(skill_name),
                    self.assets.load_template("response_contract"),
                ]
            )
            state["answer"] = self.bedrock_client.generate_grounded_answer(
                system_prompt=system_prompt,
                user_question=state["question"],
                structured_context=state.get("sql_rows", []),
                retrieved_context=state.get("retrieved_chunks", []),
                guardrail_rules=self.assets.load_rules("llm_guardrails"),
            )
            state["token_usage"] = self._extract_token_usage(state["answer"])
            return state
        finally:
            self._record_timing(state, "synthesize", start)

    def guardrails(self, state: AgentState) -> AgentState:
        start = time.perf_counter()
        guardrail_passed = False
        try:
            # Final checks validate that the chosen route respected the platform contract before
            # traces are emitted to Langfuse.
            enforce_exact_finance_from_sql(
                question_route=state["route"],
                answer_payload={
                    "sql": state.get("sql_rows"),
                    "citations": state.get("retrieved_chunks", []),
                },
            )
            enforce_citation_minimum(
                {"citations": state.get("retrieved_chunks", [])},
                minimum_citations=1 if state["route"] != "sql" else 0,
            )
            guardrail_passed = True
            return state
        finally:
            self._record_timing(state, "guardrails", start)
            total_latency_ms = sum(state.get("node_timings", {}).values())
            emit_query_metrics(
                tenant_id=state["tenant_id"],
                route=state["route"],
                latency_ms=total_latency_ms,
                citation_count=len(state.get("retrieved_chunks", [])),
                sql_row_count=len(state.get("sql_rows", [])),
                guardrail_passed=guardrail_passed,
                timings=state.get("node_timings"),
                retrieval_summary=state.get("retrieval_metrics"),
            )
            self.tracer.trace_query(
                tenant_id=state["tenant_id"],
                route=state["route"],
                input_payload={"question": state["question"]},
                output_payload={
                    "citations": state.get("retrieved_chunks", []),
                    "sql_rows": state.get("sql_rows", []),
                },
                timings=state.get("node_timings"),
                token_usage=state.get("token_usage"),
                retrieval_summary=state.get("retrieval_metrics"),
                guardrail_passed=guardrail_passed,
                model_id=self.bedrock_client.config.model_id,
            )

    @staticmethod
    def _record_timing(state: AgentState, node_name: str, start: float) -> None:
        timings = state.setdefault("node_timings", {})
        timings[node_name] = (time.perf_counter() - start) * 1000

    @staticmethod
    def _extract_token_usage(answer: dict[str, Any]) -> dict[str, int]:
        usage = answer.get("usage", {})
        return {
            "input_tokens": int(usage.get("inputTokens", usage.get("input_tokens", 0))),
            "output_tokens": int(
                usage.get("outputTokens", usage.get("output_tokens", 0))
            ),
            "total_tokens": int(usage.get("totalTokens", usage.get("total_tokens", 0))),
        }

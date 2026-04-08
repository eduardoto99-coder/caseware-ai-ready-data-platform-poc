from __future__ import annotations

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
from caseware_poc.observability.langfuse_tracer import LangfuseTracer


class AgentState(TypedDict, total=False):
    tenant_id: str
    authenticated_tenant_id: str
    question: str
    route: Literal["sql", "rag", "mixed_guardrail"]
    retrieved_chunks: list[dict[str, Any]]
    sql_rows: list[dict[str, Any]]
    answer: dict[str, Any]


class ReferenceLangGraphAgent:
    """Production-shaped agent graph showing how repo-native skills and rules fit together."""

    def __init__(
        self,
        *,
        repo_root: Path,
        trino_client: TrinoServingClient,
        opensearch_index: OpenSearchDocumentIndex,
        bedrock_client: BedrockAnswerSynthesizer,
        tracer: LangfuseTracer,
    ) -> None:
        self.assets = PromptAssetLoader(repo_root)
        self.trino_client = trino_client
        self.opensearch_index = opensearch_index
        self.bedrock_client = bedrock_client
        self.tracer = tracer

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
        graph.add_conditional_edges(
            "route",
            self.route_selector,
            {
                "sql_retrieval": "sql_retrieval",
                "rag_retrieval": "rag_retrieval",
                "mixed_guardrail": "sql_retrieval",
            },
        )
        graph.add_edge("sql_retrieval", "rag_retrieval")
        graph.add_edge("rag_retrieval", "synthesize")
        graph.add_edge("synthesize", "guardrails")
        graph.add_edge("guardrails", END)
        return graph.compile()

    def validate_tenant(self, state: AgentState) -> AgentState:
        enforce_tenant_boundary(
            authenticated_tenant_id=state["authenticated_tenant_id"],
            request_tenant_id=state["tenant_id"],
        )
        return state

    def route(self, state: AgentState) -> AgentState:
        rules = self.assets.load_rules("llm_guardrails")["routing"]
        question = state["question"].lower()
        sql_hits = [term for term in rules["sql_terms"] if term in question]
        rag_hits = [term for term in rules["rag_terms"] if term in question]
        precision_doc_hits = [term for term in rules["precision_doc_terms"] if term in question]
        if sql_hits and precision_doc_hits:
            state["route"] = "mixed_guardrail"
        elif rag_hits and not sql_hits:
            state["route"] = "rag"
        else:
            state["route"] = "sql"
        return state

    @staticmethod
    def route_selector(state: AgentState) -> str:
        if state["route"] == "rag":
            return "rag_retrieval"
        if state["route"] == "mixed_guardrail":
            return "mixed_guardrail"
        return "sql_retrieval"

    def sql_retrieval(self, state: AgentState) -> AgentState:
        sql_template = self.assets.load_template("trino_overdue_query")
        state["sql_rows"] = self.trino_client.query_gold_product(
            tenant_id=state["tenant_id"],
            sql=sql_template,
        )
        return state

    def rag_retrieval(self, state: AgentState) -> AgentState:
        response = self.opensearch_index.tenant_scoped_search(
            tenant_id=state["tenant_id"],
            query_text=state["question"],
            query_vector=[0.0] * 1536,
            top_k=4,
        )
        hits = response.get("hits", {}).get("hits", [])
        chunks = [
            {
                "id": hit["_id"],
                "score": hit["_score"],
                "text": hit["_source"]["chunk_text"],
                "source_uri": hit["_source"]["source_uri"],
            }
            for hit in hits
        ]
        state["retrieved_chunks"] = enforce_context_budget(chunks)
        return state

    def synthesize(self, state: AgentState) -> AgentState:
        skill_name = {
            "sql": "exact_accounting_sql",
            "rag": "tenant_safe_policy_rag",
            "mixed_guardrail": "precision_guardrail",
        }[state["route"]]
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
            retrieved_context=state.get("retrieved_chunks", []),
            guardrail_rules=self.assets.load_rules("llm_guardrails"),
        )
        return state

    def guardrails(self, state: AgentState) -> AgentState:
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
        self.tracer.trace_query(
            tenant_id=state["tenant_id"],
            route=state["route"],
            input_payload={"question": state["question"]},
            output_payload={"citations": state.get("retrieved_chunks", []), "sql_rows": state.get("sql_rows", [])},
        )
        return state

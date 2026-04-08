from __future__ import annotations

from caseware_poc.common.models import RouteDecision


SQL_TERMS = {
    "invoice",
    "invoices",
    "overdue",
    "amount",
    "total",
    "sum",
    "count",
    "control",
    "controls",
    "engagement",
    "status",
    "exception",
    "exceptions",
}

RAG_TERMS = {
    "policy",
    "policies",
    "workpaper",
    "notes",
    "note",
    "explain",
    "why",
    "say",
    "guidance",
    "revenue recognition",
    "deferred revenue",
}

PRECISION_DOC_TERMS = {"table", "ocr", "document", "policy", "workpaper"}


def route_question(question: str) -> RouteDecision:
    normalized = question.lower()
    sql_hits = [term for term in SQL_TERMS if term in normalized]
    rag_hits = [term for term in RAG_TERMS if term in normalized]
    precision_doc_hits = [term for term in PRECISION_DOC_TERMS if term in normalized]

    if sql_hits and precision_doc_hits:
        return RouteDecision(
            route="mixed_guardrail",
            skill="precision_guardrail",
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
            skill="tenant_safe_policy_rag",
            reason="The question asks for narrative or policy context better served by tenant-scoped retrieval.",
            rules_fired=["narrative_terms_detected", "rag_skill_selected"],
        )
    return RouteDecision(
        route="sql",
        skill="exact_accounting_sql",
        reason="The question requests exact operational or financial data available in gold tables.",
        rules_fired=["structured_terms_detected", "sql_skill_selected"],
    )

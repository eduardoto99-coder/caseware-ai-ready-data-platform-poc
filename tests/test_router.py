from caseware_poc.serving.router import RouteService, route_question


def test_routes_structured_question_to_sql() -> None:
    decision = route_question("What is the total overdue invoice amount this month?")
    assert decision.route == "sql"
    assert decision.skill == "exact_accounting_sql"


def test_routes_policy_question_to_rag() -> None:
    decision = route_question(
        "What does the deferred revenue policy say about onboarding services?"
    )
    assert decision.route == "rag"
    assert decision.skill == "tenant_safe_policy_rag"


def test_routes_mixed_question_to_guardrail() -> None:
    decision = route_question(
        "What does the OCR workpaper say and what exact amount is overdue?"
    )
    assert decision.route == "mixed_guardrail"
    assert decision.skill == "precision_guardrail"


def test_default_route_falls_back_to_sql_when_no_terms_match() -> None:
    decision = route_question("Hello, how are you?")

    assert decision.route == "sql"
    assert "sql_skill_selected" in decision.rules_fired


def test_sql_terms_win_when_question_contains_narrative_language_but_no_precision_doc_terms() -> (
    None
):
    decision = route_question("Explain the invoice status for engagement E-2026-001.")

    assert decision.route == "sql"
    assert decision.skill == "exact_accounting_sql"


def test_route_service_matches_top_level_helper() -> None:
    service = RouteService()
    question = "What does the issue summary say about payroll discrepancies?"

    assert service.route_question(question) == route_question(question)

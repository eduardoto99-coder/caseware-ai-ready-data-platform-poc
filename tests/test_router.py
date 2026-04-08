from caseware_poc.serving.router import route_question


def test_routes_structured_question_to_sql() -> None:
    decision = route_question("What is the total overdue invoice amount this month?")
    assert decision.route == "sql"


def test_routes_policy_question_to_rag() -> None:
    decision = route_question("What does the deferred revenue policy say about onboarding services?")
    assert decision.route == "rag"


def test_routes_mixed_question_to_guardrail() -> None:
    decision = route_question("What does the OCR workpaper say and what exact amount is overdue?")
    assert decision.route == "mixed_guardrail"

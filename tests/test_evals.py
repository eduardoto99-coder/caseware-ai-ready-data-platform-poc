from evals.eval_chunking import evaluate_chunking
from evals.eval_guardrails import evaluate_guardrails
from evals.eval_retrieval import evaluate_retrieval
from evals.eval_routing import evaluate_routing


def test_routing_eval_matches_golden_routes() -> None:
    report = evaluate_routing()

    assert report["overall_accuracy"] == 1.0
    assert report["misses"] == []


def test_chunking_eval_reports_healthy_overlap_and_table_detection() -> None:
    report = evaluate_chunking()

    assert report["narrative_windowing"]["overlap_pair_rate"] > 0
    assert report["table_detection"]["precision"] >= 0.5
    assert report["table_detection"]["recall"] == 1.0


def test_guardrail_eval_reports_full_contract_compliance() -> None:
    report = evaluate_guardrails()

    assert report["compliance_rate"] == 1.0
    assert report["failures"] == []


def test_retrieval_eval_reports_hit_rate_and_budget_safety() -> None:
    report = evaluate_retrieval()

    assert report["hit_rate_at_4"] >= 0.8
    assert report["mrr_at_4"] >= 0.8
    assert report["tenant_isolation_pass_rate"] == 1.0
    assert report["context_budget"]["budget_respected"] is True

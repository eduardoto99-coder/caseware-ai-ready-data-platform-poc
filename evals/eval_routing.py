"""Routing accuracy evaluation against the golden question set.

Runs every labeled question through the keyword router and reports
precision per route plus an overall accuracy score.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from caseware_poc.serving.router import RouteService


def load_golden_questions(path: Path | None = None) -> list[dict]:
    path = path or Path(__file__).parent / "golden_questions.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data["questions"]


def evaluate_routing() -> dict:
    questions = load_golden_questions()
    router = RouteService()

    results: list[dict] = []
    for q in questions:
        decision = router.route_question(q["text"])
        correct = decision.route == q["expected_route"]
        results.append(
            {
                "id": q["id"],
                "text": q["text"],
                "expected_route": q["expected_route"],
                "actual_route": decision.route,
                "expected_skill": q.get("expected_skill"),
                "actual_skill": decision.skill,
                "correct": correct,
                "rules_fired": decision.rules_fired,
            }
        )

    total = len(results)
    correct_count = sum(1 for r in results if r["correct"])
    accuracy = correct_count / total if total else 0.0

    per_route: dict[str, dict] = {}
    for route in ("sql", "rag", "mixed_guardrail"):
        subset = [r for r in results if r["expected_route"] == route]
        hits = sum(1 for r in subset if r["correct"])
        per_route[route] = {
            "total": len(subset),
            "correct": hits,
            "accuracy": hits / len(subset) if subset else 0.0,
        }

    misses = [r for r in results if not r["correct"]]

    return {
        "overall_accuracy": accuracy,
        "total": total,
        "correct": correct_count,
        "per_route": per_route,
        "misses": misses,
    }


if __name__ == "__main__":
    report = evaluate_routing()
    print(
        f"Routing accuracy: {report['overall_accuracy']:.1%} ({report['correct']}/{report['total']})"
    )
    for route, stats in report["per_route"].items():
        print(
            f"  {route}: {stats['accuracy']:.1%} ({stats['correct']}/{stats['total']})"
        )
    if report["misses"]:
        print("\nMisrouted questions:")
        for miss in report["misses"]:
            print(
                f"  [{miss['id']}] expected={miss['expected_route']} actual={miss['actual_route']}"
            )
            print(f"    {miss['text']}")

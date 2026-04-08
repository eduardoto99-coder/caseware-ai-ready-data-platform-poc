from __future__ import annotations

import json
from pathlib import Path

from caseware_poc.platform import PlatformApp


ROOT_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    app = PlatformApp(ROOT_DIR)
    app.reset()
    bootstrap_summary = app.bootstrap()
    demo_questions = [
        (
            "tenant_alpha",
            "What is the total invoice amount overdue for tenant alpha this month?",
        ),
        (
            "tenant_alpha",
            "What does tenant alpha's revenue recognition policy say about deferred revenue?",
        ),
        (
            "tenant_alpha",
            "What does the OCR workpaper table say about onboarding services and what exact amount is overdue?",
        ),
        (
            "tenant_beta",
            "Which controls have exceptions for tenant beta?",
        ),
        (
            "tenant_beta",
            "What does tenant beta's deferred revenue policy say about implementation fees?",
        ),
    ]
    answers = [
        app.answer(tenant_id=tenant_id, question=question).model_dump(mode="json")
        for tenant_id, question in demo_questions
    ]
    summary = {
        "bootstrap_summary": bootstrap_summary,
        "demo_questions": answers,
    }
    output_path = ROOT_DIR / "data" / "demo_run_summary.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

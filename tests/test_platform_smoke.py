from pathlib import Path

import duckdb

from caseware_poc.platform import PlatformApp


def bootstrap_app(tmp_path: Path) -> PlatformApp:
    app = PlatformApp(tmp_path)
    app.reset()
    app.bootstrap()
    return app


def test_bootstrap_builds_expected_gold_tables(tmp_path: Path) -> None:
    app = bootstrap_app(tmp_path)

    with duckdb.connect(str(app.config.db_path), read_only=True) as con:
        invoice_count = con.execute("select count(*) from gold_invoice_summary").fetchone()[0]
        beta_invoices = con.execute(
            "select count(*) from gold_invoice_summary where tenant_id = 'tenant_beta'"
        ).fetchone()[0]

    assert invoice_count == 2
    assert beta_invoices == 0


def test_sql_query_returns_exact_overdue_total(tmp_path: Path) -> None:
    app = bootstrap_app(tmp_path)

    response = app.answer(
        "tenant_alpha",
        "What is the total invoice amount overdue for tenant alpha this month?",
    )

    assert response.route.route == "sql"
    assert response.records[0]["total_overdue_amount"] == 12500.0


def test_rag_query_returns_tenant_scoped_citations(tmp_path: Path) -> None:
    app = bootstrap_app(tmp_path)

    response = app.answer(
        "tenant_alpha",
        "What does tenant alpha's revenue recognition policy say about deferred revenue?",
    )

    assert response.route.route == "rag"
    assert response.citations
    assert all(citation.tenant_id == "tenant_alpha" for citation in response.citations)
    assert any("Deferred revenue" in citation.text for citation in response.citations)


def test_guardrail_combines_sql_and_document_context(tmp_path: Path) -> None:
    app = bootstrap_app(tmp_path)

    response = app.answer(
        "tenant_alpha",
        "What does the OCR workpaper table say about onboarding services and what exact amount is overdue?",
    )

    assert response.route.route == "mixed_guardrail"
    assert response.records[0]["total_overdue_amount"] == 12500.0
    assert response.citations
    assert response.warnings

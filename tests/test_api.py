from fastapi.testclient import TestClient

from caseware_poc.app import api, platform_app


client = TestClient(api)


def test_bootstrap_and_query_api_flow() -> None:
    platform_app.reset()

    bootstrap_response = client.post("/bootstrap")
    assert bootstrap_response.status_code == 200
    assert bootstrap_response.json()["vector_index"]["chunks"] >= 1

    query_response = client.post(
        "/query",
        json={
            "tenant_id": "tenant_alpha",
            "question": "What is the total invoice amount overdue for tenant alpha this month?",
        },
    )
    assert query_response.status_code == 200
    payload = query_response.json()
    assert payload["route"]["route"] == "sql"
    assert payload["records"][0]["total_overdue_amount"] == 12500.0


def test_guardrails_endpoint_exposes_repo_native_assets() -> None:
    response = client.get("/guardrails")
    assert response.status_code == 200
    payload = response.json()
    assert "skills" in payload
    assert "routing" in payload
    assert "retrieval" in payload
    assert "response" in payload
    assert "tenant_isolation" in payload
    assert "tooling" in payload
    assert "context_budget" in payload
    assert "answer_contracts" in payload

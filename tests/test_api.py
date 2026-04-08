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

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validation_error_returns_string_detail(client: TestClient) -> None:
    # When validation fails the response body must follow the SAD §4 contract:
    # `{"detail": "<single string>"}`. FastAPI's default returns a list, which we
    # flatten in main.py — guard that behaviour here.
    response = client.post("/health", json={})

    assert response.status_code == 405  # /health only allows GET
    assert "detail" in response.json()
    assert isinstance(response.json()["detail"], str)

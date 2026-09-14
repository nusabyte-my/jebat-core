from fastapi.testclient import TestClient

from main import app


def test_api_v1_health_compatibility_route_returns_healthy_status():
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200, response.text
    assert response.json()["healthy"] is True

"""Tests for the /health route."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_reports_ok() -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["service"] == "later-backend"


def test_unknown_route_returns_404() -> None:
    assert client.get("/nope").status_code == 404

"""Smoke tests for the API surface. Deliberately no database dependency."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_identifies_the_service() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "causallens-api"


def test_health_is_live_without_touching_the_database() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_db_health_reports_rather_than_raises() -> None:
    """A suspended Neon compute must not read as a 500 — it reports status."""
    response = client.get("/health/db")
    assert response.status_code == 200
    assert "connected" in response.json()

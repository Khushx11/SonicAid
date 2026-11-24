import pytest
from fastapi.testclient import TestClient

from backend.app.main import allowed_cors_origins, create_app


def test_local_frontend_origin_receives_cors_headers(monkeypatch):
    monkeypatch.delenv("SONICAID_ALLOWED_ORIGINS", raising=False)
    client = TestClient(create_app())
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") is None


def test_untrusted_origin_is_not_allowed(monkeypatch):
    monkeypatch.setenv("SONICAID_ALLOWED_ORIGINS", "http://localhost:5173")
    client = TestClient(create_app())
    response = client.get(
        "/api/health",
        headers={"Origin": "https://untrusted.example"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_custom_origin_configuration(monkeypatch):
    monkeypatch.setenv(
        "SONICAID_ALLOWED_ORIGINS",
        "https://app.example, https://demo.example",
    )
    assert allowed_cors_origins() == [
        "https://app.example",
        "https://demo.example",
    ]


def test_wildcard_origin_is_rejected(monkeypatch):
    monkeypatch.setenv("SONICAID_ALLOWED_ORIGINS", "*")
    with pytest.raises(ValueError, match="explicit"):
        allowed_cors_origins()

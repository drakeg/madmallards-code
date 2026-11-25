"""Password login protects browser, chat, workspace APIs and generated diffs."""
import pytest
from fastapi.testclient import TestClient

from app import auth, main


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_PASSWORD", "test-admin-access-password-is-long")
    monkeypatch.setenv("APP_SESSION_SECRET", "test-session-signing-secret-is-very-long")
    monkeypatch.setattr(main, "configured", auth.configured)
    monkeypatch.setattr(main, "authenticated", auth.authenticated)
    auth.FAILED_ATTEMPTS.clear()
    with TestClient(main.app, follow_redirects=False) as test_client:
        yield test_client


def test_unauthed_routes_are_restricted(client):
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 303
    assert client.get("/").headers["location"] == "/auth/login"
    assert client.get("/docs").status_code == 303
    assert client.get("/api/v1/workspaces").status_code == 401
    assert client.get("/api/v1/conversations").status_code == 401
    assert client.post("/api/v1/models/chat", json={}).status_code == 401
    assert client.get("/auth/login").status_code == 200


def test_login_cookie_and_logout(client):
    bad = client.post("/auth/login", json={"password": "wrong"})
    assert bad.status_code == 401
    good = client.post(
        "/auth/login", json={"password": "test-admin-access-password-is-long"}
    )
    assert good.status_code == 200
    assert good.json()["authenticated"] is True
    assert "httponly" in good.headers["set-cookie"].lower()
    assert "samesite=strict" in good.headers["set-cookie"].lower()
    assert client.get("/").status_code == 200
    assert client.get("/api/v1/workspaces").status_code == 200
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/api/v1/workspaces").status_code == 401


def test_rate_limit_and_invalid_origin(client):
    for _ in range(5):
        assert client.post("/auth/login", json={"password": "wrong"}).status_code == 401
    assert client.post(
        "/auth/login", json={"password": "test-admin-access-password-is-long"}
    ).status_code == 429
    auth.FAILED_ATTEMPTS.clear()
    assert client.post(
        "/auth/login", json={"password": "test-admin-access-password-is-long"}
    ).status_code == 200
    assert client.post(
        "/auth/logout", headers={"Origin": "http://other-host:8096"}
    ).status_code == 403
    assert client.get("/api/v1/workspaces").status_code == 200


def test_missing_configuration_fails_closed(client, monkeypatch):
    monkeypatch.delenv("APP_SESSION_SECRET")
    assert client.get("/api/v1/workspaces").status_code == 503
    assert client.get("/").status_code == 503
    assert client.post("/auth/login", json={"password": "wrong"}).status_code == 503

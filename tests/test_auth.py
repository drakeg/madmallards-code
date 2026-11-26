"""Database-backed login tests including revocation and invalid credentials."""
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import auth, main
from app.models import AuthSession, Base, User


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'auth.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        db.add(User(
            username="admin",
            password_hash=auth.PASSWORDS.hash("temporary-test-password-12345"),
            is_active=True, is_admin=True,
        ))
        db.commit()
    monkeypatch.setattr(auth, "auth_session_factory", lambda: factory)
    monkeypatch.setattr(main, "authenticated", auth.authenticated)
    auth.FAILED_ATTEMPTS.clear()
    try:
        with TestClient(main.app, follow_redirects=False) as test_client:
            yield test_client, factory
    finally:
        engine.dispose()


def test_unauthed_routes_are_restricted(client):
    http, _ = client
    assert http.get("/health").status_code == 200
    assert http.get("/").status_code == 303
    assert http.get("/").headers["location"] == "/auth/login"
    assert http.get("/docs").status_code == 303
    assert http.get("/api/v1/workspaces").status_code == 401
    assert http.get("/api/v1/conversations").status_code == 401
    assert http.post("/api/v1/models/chat", json={}).status_code == 401
    assert 'name="username"' in http.get("/auth/login").text


def test_login_persists_revocable_hashed_token(client):
    http, factory = client
    assert http.post("/auth/login", json={"username": "admin", "password": "wrong"}).status_code == 401
    response = http.post("/auth/login", json={
        "username": "admin", "password": "temporary-test-password-12345",
    })
    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=strict" in response.headers["set-cookie"].lower()
    token = http.cookies.get("mmc_session")
    with factory() as db:
        stored = db.scalar(select(AuthSession))
        assert stored is not None
        assert stored.token_hash == auth.token_digest(token)
        assert token != stored.token_hash
    assert http.get("/").status_code == 200
    assert http.get("/api/v1/workspaces").status_code == 200
    assert http.post("/auth/logout").status_code == 200
    assert http.get("/api/v1/workspaces").status_code == 401
    with factory() as db:
        assert db.scalar(select(AuthSession)) is None


def test_rate_limit_expiry_and_invalid_origin(client):
    http, factory = client
    for _ in range(5):
        assert http.post("/auth/login", json={"username": "admin", "password": "wrong"}).status_code == 401
    assert http.post("/auth/login", json={"username": "admin", "password": "temporary-test-password-12345"}).status_code == 429
    auth.FAILED_ATTEMPTS.clear()
    assert http.post("/auth/login", json={"username": "admin", "password": "temporary-test-password-12345"}).status_code == 200
    assert http.post("/auth/logout", headers={"Origin": "http://other-host:8096"}).status_code == 403
    assert http.get("/api/v1/workspaces").status_code == 200
    with factory() as db:
        stored = db.scalar(select(AuthSession))
        stored.expires_at = auth.utc_naive() - timedelta(seconds=1)
        db.commit()
    assert http.get("/api/v1/workspaces").status_code == 401


def test_disabled_account_and_unknown_user(client):
    http, factory = client
    assert http.post("/auth/login", json={
        "username": "missing", "password": "temporary-test-password-12345",
    }).status_code == 401
    with factory() as db:
        user = db.scalar(select(User).where(User.username == "admin"))
        user.is_active = False
        db.commit()
    assert http.post("/auth/login", json={
        "username": "admin", "password": "temporary-test-password-12345",
    }).status_code == 401


def test_login_page_reflows_with_minmax_grid(client):
    http, _ = client
    html = http.get("/auth/login").text
    assert "grid-template-columns:minmax(0,1fr)" in html
    assert "max-width:430px;min-width:0" in html
    assert "overflow-wrap:anywhere" in html

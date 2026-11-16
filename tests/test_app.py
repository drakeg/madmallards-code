from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    result = client.get("/health")
    assert result.status_code == 200
    assert result.json() == {"status": "ok"}


def test_info():
    result = client.get("/api/v1/info")
    assert result.status_code == 200
    assert result.json()["phase"] == "foundation"


def test_home():
    result = client.get("/")
    assert result.status_code == 200
    assert "Mad Mallards Code" in result.text
    assert 'id="composer"' in result.text

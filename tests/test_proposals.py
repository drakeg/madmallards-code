"""Dry-run diff proposals must not change actual workspace files."""
import hashlib

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.workspaces import workspace_root


@pytest.fixture
def client(tmp_path):
    root = tmp_path / "repos"
    repo = root / "demo"
    repo.mkdir(parents=True)
    (repo / "main.py").write_text("answer = 1\n", encoding="utf-8")
    (repo / ".env").write_text("API_KEY=private", encoding="utf-8")
    (repo / "link.py").symlink_to(tmp_path / "outside.py")
    (tmp_path / "outside.py").write_text("outside")
    app.dependency_overrides[workspace_root] = lambda: root
    try:
        with TestClient(app) as instance:
            yield instance, repo
    finally:
        app.dependency_overrides.clear()


def test_diff_preview_is_read_only(client):
    http, repo = client
    original = "answer = 1\n"
    sha = hashlib.sha256(original.encode()).hexdigest()
    response = http.post("/api/v1/workspaces/demo/proposals", json={
        "path": "main.py", "baseline_sha256": sha,
        "proposed_content": "answer = 2\n",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["changed"] is True
    assert body["read_only"] is True
    assert body["applied"] is False
    assert "-answer = 1" in body["diff"]
    assert "+answer = 2" in body["diff"]
    assert (repo / "main.py").read_text() == original

    same = http.post("/api/v1/workspaces/demo/proposals", json={
        "path": "main.py", "baseline_sha256": sha, "proposed_content": original
    })
    assert same.status_code == 200
    assert same.json()["changed"] is False
    assert same.json()["diff"] == ""


def test_stale_baseline_does_not_write(client):
    http, repo = client
    response = http.post("/api/v1/workspaces/demo/proposals", json={
        "path": "main.py", "baseline_sha256": "0" * 64, "proposed_content": "bad"
    })
    assert response.status_code == 409
    assert (repo / "main.py").read_text() == "answer = 1\n"


@pytest.mark.parametrize(("filename", "status"), [
    ("../outside.py", 400),
    (".env", 400),
    ("link.py", 403),
    ("missing.py", 404),
])
def test_unsafe_paths_rejected(client, filename, status):
    http, _ = client
    response = http.post("/api/v1/workspaces/demo/proposals", json={
        "path": filename, "baseline_sha256": "0" * 64, "proposed_content": "bad",
    })
    assert response.status_code == status


def test_input_bounded(client):
    http, _ = client
    result = http.post("/api/v1/workspaces/demo/proposals", json={
        "path": "main.py", "baseline_sha256": "0" * 64,
        "proposed_content": "x" * (128 * 1024 + 1),
    })
    assert result.status_code == 422

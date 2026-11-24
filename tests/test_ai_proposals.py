"""Model-suggested edits are only previewed, never applied."""
import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from app.api_models import provider
from app.main import app
from app.workspaces import workspace_root


class FakeModel:
    async def list_models(self):
        return [{"name": "tiny:local"}]

    async def stream_chat(self, model, messages):
        assert model == "tiny:local"
        assert "answer = 1" in messages[-1]["content"]
        yield json.dumps({"type": "token", "content": "answer = 2\n"}) + "\n"
        yield json.dumps({"type": "done"}) + "\n"


@pytest.fixture
def client(tmp_path):
    repo = tmp_path / "example"
    repo.mkdir()
    (repo / "main.py").write_text("answer = 1\n", encoding="utf-8")
    (repo / ".env").write_text("SECRET")
    app.dependency_overrides[workspace_root] = lambda: tmp_path
    app.dependency_overrides[provider] = lambda: FakeModel()
    try:
        with TestClient(app) as browser:
            yield browser, repo
    finally:
        app.dependency_overrides.clear()


def payload(path="main.py", sha=None):
    return {
        "path": path, "model": "tiny:local", "instruction": "Change answer to two",
        "baseline_sha256": sha or hashlib.sha256(b"answer = 1\n").hexdigest(),
    }


def test_generated_diff_does_not_modify_file(client):
    http, repo = client
    response = http.post("/api/v1/workspaces/example/ai-proposal", json=payload())
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["applied"] is False
    assert result["proposed_content"] == "answer = 2\n"
    assert "-answer = 1" in result["diff"]
    assert "+answer = 2" in result["diff"]
    assert (repo / "main.py").read_text() == "answer = 1\n"


@pytest.mark.parametrize(("item", "status"), [
    (payload(sha="0" * 64), 409),
    (payload(path=".env"), 400),
    (payload(path="../main.py"), 400),
    (payload(path="missing.py"), 404),
])
def test_invalid_context_rejected(client, item, status):
    http, repo = client
    response = http.post("/api/v1/workspaces/example/ai-proposal", json=item)
    assert response.status_code == status
    assert (repo / "main.py").read_text() == "answer = 1\n"


def test_unknown_model_rejected(client):
    http, _ = client
    bad = payload()
    bad["model"] = "not-installed"
    response = http.post("/api/v1/workspaces/example/ai-proposal", json=bad)
    assert response.status_code == 422

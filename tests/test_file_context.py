"""Context-file attachment tests: no implicit file access or execution."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api_models import provider
from app.conversations import session_factory
from app.main import app
from app.models import Base
from app.ollama import OllamaProvider
from app.workspaces import workspace_root


@pytest.fixture
def client(tmp_path):
    workspaces = tmp_path / "workspaces"
    repository = workspaces / "demo"
    repository.mkdir(parents=True)
    (repository / "main.py").write_text("def answer(): return 42\n", encoding="utf-8")
    (repository / ".env").write_text("SECRET=do-not-send")
    (repository / "large.py").write_text("a" * 25000)
    (repository / "outside.py").symlink_to(tmp_path / "outside.py")
    (tmp_path / "outside.py").write_text("outside contents")
    database = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{database}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    payloads = []

    def respond(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "local:4b"}]})
        if request.url.path == "/api/chat":
            payloads.append(json.loads(request.content))
            return httpx.Response(200, content='{"message":{"content":"42"},"done":false}\n{"done":true}\n')
        return httpx.Response(404)

    app.dependency_overrides[provider] = lambda: OllamaProvider(
        "http://localhost:11434", httpx.MockTransport(respond)
    )
    app.dependency_overrides[session_factory] = lambda: factory
    app.dependency_overrides[workspace_root] = lambda: workspaces
    try:
        with TestClient(app) as test_client:
            yield test_client, payloads
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_only_explicit_attachment_is_sent(client):
    http, captured = client
    conversation_id = http.post("/api/v1/conversations", json={}).json()["id"]
    endpoint = f"/api/v1/conversations/{conversation_id}/messages"
    request = {"model": "local:4b", "prompt": "What does this function return?"}
    assert http.post(endpoint, json=request).status_code == 200
    assert "repository-file" not in str(captured[-1])
    request["context_file"] = {"workspace": "demo", "path": "main.py"}
    assert http.post(endpoint, json=request).status_code == 200
    messages = captured[-1]["messages"]
    assert messages[0]["role"] == "system"
    assert "def answer(): return 42" in messages[0]["content"]
    assert messages[-1]["content"] == request["prompt"]
    history = http.get(f"/api/v1/conversations/{conversation_id}").json()["messages"]
    assert len(history) == 4
    assert "def answer()" not in str(history)
    assert "SECRET=" not in str(captured)


@pytest.mark.parametrize(("path", "expected"), [
    ("../outside.py", 400),
    (".env", 400),
    ("outside.py", 403),
    ("large.py", 413),
    ("missing.py", 404),
])
def test_context_rejects_unsafe_files(client, path, expected):
    http, captured = client
    cid = http.post("/api/v1/conversations", json={}).json()["id"]
    response = http.post(f"/api/v1/conversations/{cid}/messages", json={
        "model": "local:4b", "prompt": "Explain",
        "context_file": {"workspace": "demo", "path": path},
    })
    assert response.status_code == expected
    assert not captured
    assert http.get(f"/api/v1/conversations/{cid}").json()["messages"] == []

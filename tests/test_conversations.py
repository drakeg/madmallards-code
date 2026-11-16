"""End-to-end HTTP tests for saved chat conversations and model streaming."""
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


@pytest.fixture
def client(tmp_path):
    database = tmp_path / "chat.db"
    engine = create_engine(f"sqlite:///{database}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def respond(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:4b", "size": 123}]})
        if request.url.path == "/api/chat":
            messages = json.loads(request.content)["messages"]
            assert messages[-1]["role"] == "user"
            assert messages[-1]["content"] in ("Can you help?", "Another question?")
            return httpx.Response(200, content=(
                '{"message":{"content":"Yes, "},"done":false}\n'
                '{"message":{"content":"I can."},"done":false}\n'
                '{"done":true}\n'
            ))
        return httpx.Response(404)

    local = OllamaProvider("http://localhost:11434", httpx.MockTransport(respond))
    app.dependency_overrides[session_factory] = lambda: factory
    app.dependency_overrides[provider] = lambda: local
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_saved_conversation_and_stream(client):
    assert client.get("/api/v1/conversations").json()["conversations"] == []
    created = client.post("/api/v1/conversations", json={})
    assert created.status_code == 201
    cid = created.json()["id"]
    assert client.get("/api/v1/conversations").json()["conversations"][0]["id"] == cid
    response = client.post(
        f"/api/v1/conversations/{cid}/messages",
        json={"model": "qwen3:4b", "prompt": "Can you help?"},
    )
    assert response.status_code == 200
    assert [json.loads(line)["type"] for line in response.text.splitlines()] == [
        "token", "token", "done"
    ]
    loaded = client.get(f"/api/v1/conversations/{cid}")
    assert loaded.status_code == 200
    assert loaded.json()["title"] == "Can you help?"
    assert [(m["role"], m["content"]) for m in loaded.json()["messages"]] == [
        ("user", "Can you help?"), ("assistant", "Yes, I can.")
    ]
    second = client.post(
        f"/api/v1/conversations/{cid}/messages",
        json={"model": "qwen3:4b", "prompt": "Another question?"},
    )
    assert second.status_code == 200
    assert len(client.get(f"/api/v1/conversations/{cid}").json()["messages"]) == 4


def test_validation_and_missing_conversation(client):
    assert client.get("/api/v1/conversations/not-found").status_code == 404
    assert client.post(
        "/api/v1/conversations/not-found/messages",
        json={"model": "qwen3:4b", "prompt": "Hello"},
    ).status_code == 404
    cid = client.post("/api/v1/conversations", json={}).json()["id"]
    assert client.post(
        f"/api/v1/conversations/{cid}/messages",
        json={"model": "missing:1b", "prompt": "Hello"},
    ).status_code == 422
    assert client.post(
        f"/api/v1/conversations/{cid}/messages",
        json={"model": "qwen3:4b", "prompt": ""},
    ).status_code == 422
    assert client.get(f"/api/v1/conversations/{cid}").json()["messages"] == []


def test_frontend_contains_chat_controls(client):
    document = client.get("/")
    assert document.status_code == 200
    for marker in ('id="composer"', 'id="prompt"', 'id="model-select"', 'id="conversation-list"'):
        assert marker in document.text
    js = client.get("/static/chat.js")
    assert js.status_code == 200
    assert 'requestSubmit()' in js.text

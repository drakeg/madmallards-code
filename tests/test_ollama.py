"""Provider contract tests with no dependency on an installed local model."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api_models import provider
from app.main import app
from app.ollama import ModelProviderError, OllamaProvider


@pytest.mark.asyncio
async def test_model_listing():
    def respond(request):
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": [{"name": "qwen3:4b", "size": 5}, {"name": "remote:cloud", "size": 0}]})

    result = await OllamaProvider("http://localhost:11434", httpx.MockTransport(respond)).list_models()
    assert result == [{"name": "qwen3:4b", "size": "5"}]


@pytest.mark.asyncio
async def test_provider_unavailable():
    def respond(request):
        raise httpx.ConnectError("offline", request=request)

    with pytest.raises(ModelProviderError):
        await OllamaProvider("http://localhost:11434", httpx.MockTransport(respond)).list_models()


@pytest.mark.asyncio
async def test_streamed_chunks():
    def respond(request):
        assert request.url.path == "/api/chat"
        request_body = json.loads(request.content)
        assert request_body["model"] == "qwen3:4b"
        assert request_body["stream"] is True
        events = (
            '{"message":{"content":"Hello"},"done":false}\n'
            '{"message":{"content":" world"},"done":false}\n'
            '{"done":true}\n'
        )
        return httpx.Response(200, content=events)

    instance = OllamaProvider("http://localhost:11434", httpx.MockTransport(respond))
    result = [json.loads(x) async for x in instance.stream_chat("qwen3:4b", [{"role": "user", "content": "Hi"}])]
    assert result == [
        {"type": "token", "content": "Hello"},
        {"type": "token", "content": " world"},
        {"type": "done"},
    ]


def test_http_endpoints(monkeypatch):
    def respond(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:4b", "size": 5}, {"name": "remote:cloud", "size": 0}]})
        if request.url.path == "/api/chat":
            return httpx.Response(200, content='{"message":{"content":"ok"},"done":false}\n{"done":true}\n')
        return httpx.Response(404)

    instance = OllamaProvider("http://localhost:11434", httpx.MockTransport(respond))
    app.dependency_overrides[provider] = lambda: instance
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/models").json()["models"][0]["name"] == "qwen3:4b"
            response = client.post("/api/v1/models/chat", json={
                "model": "qwen3:4b", "messages": [{"role": "user", "content": "Hello"}]
            })
            assert response.status_code == 200
            assert [json.loads(x)["type"] for x in response.text.strip().splitlines()] == ["token", "done"]
            assert client.post("/api/v1/models/chat", json={
                "model": "missing", "messages": [{"role": "user", "content": "Hello"}]
            }).status_code == 422
    finally:
        app.dependency_overrides.clear()

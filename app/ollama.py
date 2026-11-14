"""Ollama HTTP adapter; upstream location is configured by the administrator."""
import json
import os
from collections.abc import AsyncIterator
from typing import Any

import httpx


class ModelProviderError(Exception):
    """Upstream model provider is unavailable or returned malformed data."""


class OllamaProvider:
    def __init__(self, base_url: str | None = None, transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL") or "http://host.docker.internal:11434").rstrip("/")
        self.transport = transport

    async def list_models(self) -> list[dict[str, str]]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, transport=self.transport, timeout=8.0) as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                models = response.json()["models"]
                if not isinstance(models, list):
                    raise TypeError("Invalid models payload")
                return [
                    {"name": item["name"], "size": str(item.get("size", 0))}
                    for item in models
                    if isinstance(item, dict) and isinstance(item.get("name"), str) and not item["name"].endswith(":cloud")
                ]
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise ModelProviderError("Unable to retrieve local models") from exc

    async def stream_chat(self, model: str, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": True}
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                transport=self.transport,
                timeout=httpx.Timeout(connect=5, read=180, write=10, pool=5),
            ) as client, client.stream("POST", "/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        event = json.loads(line)
                        if not isinstance(event, dict):
                            raise TypeError("Invalid Ollama event")
                        if event.get("error"):
                            raise ModelProviderError("Local model generation failed")
                        chunk = event.get("message", {}).get("content", "")
                        if chunk:
                            yield json.dumps({"type": "token", "content": chunk}) + "\n"
                        if event.get("done"):
                            yield json.dumps({"type": "done"}) + "\n"
                            return
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise ModelProviderError("Local model stream failed") from exc

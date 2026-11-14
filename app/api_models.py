"""Local model listing and streaming endpoints."""
import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.ollama import ModelProviderError, OllamaProvider

router = APIRouter(prefix="/api/v1/models", tags=["models"])


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=100_000)


class ChatRequest(BaseModel):
    model: str = Field(min_length=1, max_length=200, pattern=r"^[a-zA-Z0-9._:/-]+$")
    messages: list[Message] = Field(min_length=1, max_length=100)


def provider() -> OllamaProvider:
    return OllamaProvider()


@router.get("")
async def models(selected: Annotated[OllamaProvider, Depends(provider)]) -> dict:
    try:
        return {"provider": "ollama", "models": await selected.list_models()}
    except ModelProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/chat")
async def chat(request: ChatRequest, selected: Annotated[OllamaProvider, Depends(provider)]) -> StreamingResponse:
    try:
        available = await selected.list_models()
    except ModelProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if request.model not in {item["name"] for item in available}:
        raise HTTPException(status_code=422, detail="Model is not installed in the configured Ollama instance")

    async def events():
        try:
            async for chunk in selected.stream_chat(
                request.model, [item.model_dump() for item in request.messages]
            ):
                yield chunk
        except ModelProviderError:
            yield json.dumps({"type": "error", "message": "The local model stream was interrupted"}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson", headers={"Cache-Control": "no-store"})

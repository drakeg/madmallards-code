"""Persistent local chat conversations (single-user localhost MVP)."""
import json
from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.api_models import provider
from app.db import make_session_factory
from app.models import ChatMessage, CodingSession, Project
from app.ollama import ModelProviderError, OllamaProvider

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@lru_cache(maxsize=1)
def session_factory() -> sessionmaker:
    return make_session_factory()


def conversation_data(record: CodingSession) -> dict[str, str]:
    return {
        "id": record.id,
        "title": record.title,
        "created_at": record.created_at.isoformat(),
    }


def session_record(db: Session, conversation_id: str) -> CodingSession:
    session = db.get(CodingSession, conversation_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return session


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=200)


class PromptRequest(BaseModel):
    model: str = Field(min_length=1, max_length=200, pattern=r"^[a-zA-Z0-9._:/-]+$")
    prompt: str = Field(min_length=1, max_length=20_000)


@router.get("")
def list_conversations(factory: Annotated[sessionmaker, Depends(session_factory)]) -> dict:
    with factory() as db:
        items = db.scalars(select(CodingSession).order_by(CodingSession.created_at.desc())).all()
        return {"conversations": [conversation_data(record) for record in items]}


@router.post("", status_code=201)
def create_conversation(
    payload: ConversationCreate,
    factory: Annotated[sessionmaker, Depends(session_factory)],
) -> dict:
    with factory() as db:
        project = db.scalars(select(Project).order_by(Project.created_at).limit(1)).first()
        if project is None:
            project = Project(name="Local workspace")
            db.add(project)
            db.flush()
        session = CodingSession(project_id=project.id, title=payload.title)
        db.add(session)
        db.commit()
        return conversation_data(session)


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    factory: Annotated[sessionmaker, Depends(session_factory)],
) -> dict:
    with factory() as db:
        record = session_record(db, conversation_id)
        history = db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == conversation_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        ).all()
        return {
            **conversation_data(record),
            "messages": [
                {"id": m.id, "role": m.role, "content": m.content}
                for m in history
            ],
        }


@router.post("/{conversation_id}/messages")
async def post_message(
    conversation_id: str,
    payload: PromptRequest,
    factory: Annotated[sessionmaker, Depends(session_factory)],
    selected: Annotated[OllamaProvider, Depends(provider)],
) -> StreamingResponse:
    try:
        available_models = await selected.list_models()
    except ModelProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if payload.model not in {item["name"] for item in available_models}:
        raise HTTPException(status_code=422, detail="Selected model is unavailable")

    # Commit the user's message before producing streaming output.
    with factory() as db:
        record = session_record(db, conversation_id)
        count = db.scalar(
            select(ChatMessage.id).where(ChatMessage.session_id == conversation_id).limit(1)
        )
        if count is None and record.title == "New conversation":
            record.title = payload.prompt.strip()[:80]
        db.add(ChatMessage(session_id=conversation_id, role="user", content=payload.prompt))
        db.commit()
        history = db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == conversation_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(40)
        ).all()
        messages = [
            {"role": message.role, "content": message.content}
            for message in reversed(history)
        ]

    async def events() -> AsyncIterator[str]:
        chunks: list[str] = []
        try:
            async for line in selected.stream_chat(payload.model, messages):
                event = json.loads(line)
                if event.get("type") == "token":
                    chunks.append(event.get("content", ""))
                if event.get("type") == "done":
                    with factory() as db:
                        db.add(ChatMessage(
                            session_id=conversation_id,
                            role="assistant",
                            content="".join(chunks),
                        ))
                        db.commit()
                yield line
        except (ModelProviderError, ValueError, TypeError):
            yield json.dumps({
                "type": "error",
                "message": "Generation failed. Your question was saved; please retry.",
            }) + "\n"

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )

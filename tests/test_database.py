"""Persistence smoke tests without a live external database."""
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Base, ChatMessage, CodingSession, Project


def test_project_session_and_message_round_trip():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        project = Project(name="Sample workspace", repository_url="https://github.com/example/example")
        db.add(project)
        db.flush()
        session = CodingSession(project_id=project.id, title="Fix tests")
        db.add(session)
        db.flush()
        db.add(ChatMessage(session_id=session.id, role="user", content="Hello"))
        db.commit()

        loaded = db.scalar(select(Project).where(Project.name == "Sample workspace"))
        assert loaded is not None
        assert loaded.sessions[0].title == "Fix tests"
        assert loaded.sessions[0].messages[0].content == "Hello"
    engine.dispose()

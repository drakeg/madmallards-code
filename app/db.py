"""Database engine and session factory."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def make_engine(url: str | None = None):
    configured = url or os.environ.get("DATABASE_URL")
    if not configured:
        raise RuntimeError("DATABASE_URL must be set")
    return create_engine(configured, pool_pre_ping=True)


def make_session_factory(url: str | None = None):
    return sessionmaker(bind=make_engine(url), expire_on_commit=False)

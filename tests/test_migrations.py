"""Verify the actual Alembic migration path on an isolated SQLite database."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_initial_migration_upgrade_and_downgrade(tmp_path, monkeypatch):
    database = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database}")
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(cfg, "head")
    engine = create_engine(f"sqlite:///{database}")
    assert {"projects", "coding_sessions", "chat_messages", "alembic_version", "users", "auth_sessions"} <= set(inspect(engine).get_table_names())
    engine.dispose()
    command.downgrade(cfg, "base")
    engine = create_engine(f"sqlite:///{database}")
    assert "projects" not in inspect(engine).get_table_names()
    engine.dispose()

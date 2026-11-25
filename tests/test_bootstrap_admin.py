"""Admin bootstrap uses database accounts and never overwrites unintentionally."""
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import bootstrap_admin
from app.auth import PASSWORDS
from app.models import Base, User


def test_bootstrap_then_rotate_invalidates_sessions(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'bootstrap.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(bootstrap_admin, "make_session_factory", lambda: factory)
    first_password = bootstrap_admin.bootstrap("admin")
    with factory() as db:
        user = db.scalar(select(User))
        assert user.username == "admin"
        assert user.is_admin is True
        assert PASSWORDS.verify(first_password, user.password_hash)
    with pytest.raises(ValueError):
        bootstrap_admin.bootstrap("admin")
    second_password = bootstrap_admin.bootstrap("admin", rotate=True)
    assert second_password != first_password
    with factory() as db:
        user = db.scalar(select(User))
        assert PASSWORDS.verify(second_password, user.password_hash)
        assert not PASSWORDS.verify(first_password, user.password_hash)
    engine.dispose()


@pytest.mark.parametrize("username", ["", "../admin", "hi", "a" * 65])
def test_invalid_admin_username(tmp_path, monkeypatch, username):
    with pytest.raises(ValueError):
        bootstrap_admin.bootstrap(username)

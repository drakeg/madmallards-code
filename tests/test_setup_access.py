"""Credential setup may only touch the intended ignored environment file."""
import pytest

from scripts.setup_access import setup


def test_generates_credentials_and_preserves_database_settings(tmp_path):
    env = tmp_path / ".env"
    env.write_text("DB_NAME=madmallards_code\nDB_PASSWORD=existing-value\nAPP_PORT=8096\n")
    password = setup(env)
    content = env.read_text()
    assert len(password) >= 24
    assert f"APP_ACCESS_PASSWORD={password}" in content
    secret = next(row.split("=", 1)[1] for row in content.splitlines() if row.startswith("APP_SESSION_SECRET="))
    assert len(secret) >= 32
    assert "DB_PASSWORD=existing-value" in content
    assert "APP_PORT=8096" in content
    assert (env.stat().st_mode & 0o777) == 0o600
    with pytest.raises(ValueError):
        setup(env)
    assert env.read_text() == content
    newer = setup(env, rotate=True)
    assert newer != password
    assert f"APP_ACCESS_PASSWORD={newer}" in env.read_text()
    assert env.read_text().count("APP_SESSION_SECRET=") == 1


def test_missing_file_and_symlink_rejected(tmp_path):
    env = tmp_path / ".env"
    with pytest.raises(FileNotFoundError):
        setup(env)
    safe = tmp_path / "original"
    safe.write_text("DB_PASSWORD=keep")
    env.symlink_to(safe)
    with pytest.raises(ValueError):
        setup(env)
    assert safe.read_text() == "DB_PASSWORD=keep"

"""Guard against local secrets entering the Docker build context."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dockerignore_allowlist_and_secret_exclusions():
    ignored = (ROOT / ".dockerignore").read_text().splitlines()
    patterns = {line.strip() for line in ignored if line.strip() and not line.startswith("#")}
    assert "**" in patterns
    assert {"!requirements.txt", "!app/", "!app/**", "!migrations/", "!migrations/**", "!alembic.ini"} <= patterns
    assert {"**/.env", "**/.env.*", "**/.git/", "**/*.pem", "**/*.key"} <= patterns


def test_dockerfile_only_copies_allowlisted_inputs():
    content = (ROOT / "Dockerfile").read_text()
    copy_lines = [line.strip() for line in content.splitlines() if line.startswith("COPY ")]
    assert copy_lines == [
        "COPY requirements.txt .",
        "COPY app ./app",
        "COPY migrations ./migrations",
        "COPY alembic.ini .",
    ]


def test_compose_supports_lan_binding_without_exposing_database():
    compose = (ROOT / "compose.yaml").read_text()
    assert '${APP_BIND_HOST:-0.0.0.0}:${APP_PORT:-8096}:8000' in compose
    db_section = compose.split("  db:\n", 1)[1].split("volumes:\n", 1)[0]
    assert "    ports:" not in db_section

# Mad Mallards Code

A self-hosted AI coding platform, built iteratively with Scrum.

**Status:** Sprint 1 foundation. No AI model calls or code-execution agent functionality yet.

## Quick start

1. Copy `.env.example` to `.env` and **change both database passwords**.
2. Run `docker compose up --build -d`.
3. Visit http://localhost:8096 (or the configured APP_PORT).
4. Validate with `docker compose ps` and `curl http://localhost:8096/health`.

The application listens on loopback by default. Do not expose it publicly until authentication,
authorization, execution isolation, and access controls are implemented.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check app tests
pytest -q
```

## Product and planning

See [PRD](docs/PRD.md), [Architecture](docs/ARCHITECTURE.md), [Agile workflow](docs/AGILE.md),
[Backlog](docs/BACKLOG.md), [Sprint plan](docs/SPRINTS.md), and [Security](docs/SECURITY.md).

The Maitis #r045 material has not yet been supplied or integrated.

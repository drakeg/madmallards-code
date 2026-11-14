# Mad Mallards Code

A self-hosted AI coding platform, built iteratively with Scrum.

**Status:** Sprint 1 foundation. No AI model calls or code-execution agent functionality yet.

## Quick start

1. Copy `.env.example` to `.env` and **change both database passwords**.
2. Run `docker compose up --build -d`.
3. Compose runs Alembic migrations before starting the application.
4. Visit http://localhost:8096 (or the configured APP_PORT).
5. Validate with `docker compose ps` and `curl http://localhost:8096/health`.

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


## Database migrations

`docker compose run --rm migrate` applies the latest schema safely. Schema changes
are handled by Alembic revisions in `migrations/versions`, not `create_all` on startup.
For local development, set `DATABASE_URL` before running `alembic upgrade head`.
Use `docker compose exec db mariadb -u $DB_USER -p $DB_NAME` only when shell
environment variables are intentionally configured; avoid printing passwords.

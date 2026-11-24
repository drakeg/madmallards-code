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

## Ollama integration (MMC-005)

Install and start Ollama on the Docker host, then pull a model such as \`ollama pull qwen3:4b\`.
The Compose web application connects to the host using \`OLLAMA_BASE_URL\`. If you run
Ollama on another trusted machine, configure its reachable URL in the ignored \`.env\`.

- \`GET /api/v1/models\` lists locally available models (cloud-backed Ollama entries are excluded).
- \`POST /api/v1/models/chat\` accepts \`{"model":"qwen3:4b","messages":[{"role":"user","content":"Hi"}]}\`
  and responds with newline-delimited JSON events of type \`token\`, \`done\`, or \`error\`.

This is an API-only integration; the interactive browser chat and persistent conversation
workflow are tracked in MMC-006. **Security:** the application is bound to localhost.
Do not expose the unauthenticated model API to the internet.

## Browser chat (MMC-006)

Open http://localhost:8096 and select a local model. Start a conversation, enter a
question, and watch the response stream. Messages are persisted in MariaDB, so
you can return to earlier conversations after reloading the page.

This is a **single-user localhost MVP**. Do not expose the service publicly:
authentication, authorizations, cross-user isolation, concurrent-turn safety,
and destructive-tool policies are not yet implemented. Cancelling a response
saves the user's question but does not persist a partial assistant response.

## Read-only repository workspace browser

Create \`workspaces/\` in this project (or set \`WORKSPACES_HOST_PATH\` in \`.env\`
to an explicitly approved directory). Put individual repository folders directly
under it, for example \`workspaces/myproject/\`. Only this directory is mounted
into the application, **read-only**. Hidden files, symlinks, large files, and
common secret/configuration paths are excluded from file previews.

The \`/api/v1/workspaces\` endpoints provide workspace listing, directory trees,
and bounded text previews. This **does not grant the AI write or shell access**.
Authentication and robust multi-user isolation are future requirements; keep
the application bound to localhost.

## Ask the AI about a repository file

Use the sidebar workspace browser to preview an allowed text file, then select
**Attach to next question**. The contents are transmitted to the configured
local Ollama instance only when you submit that question; they are not silently
included merely because you preview a file. Attachments are bounded to 24 KB.

File content is treated as untrusted reference data. This is a read-only coding
assistant increment, **not** a permission to modify files or execute commands.
Do not attach confidential text to any provider you do not control.

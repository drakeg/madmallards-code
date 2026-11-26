# Mad Mallards Code

[![CI](https://github.com/drakeg/madmallards-code/actions/workflows/ci.yml/badge.svg)](https://github.com/drakeg/madmallards-code/actions/workflows/ci.yml) [![License](https://img.shields.io/github/license/drakeg/madmallards-code?logo=opensourceinitiative)](https://github.com/drakeg/madmallards-code/blob/main/LICENSE) [![Issues](https://img.shields.io/github/issues/drakeg/madmallards-code)](https://github.com/drakeg/madmallards-code/issues) [![Pull requests](https://img.shields.io/github/issues-pr/drakeg/madmallards-code)](https://github.com/drakeg/madmallards-code/pulls)\
[![Python 3.15](https://img.shields.io/badge/Python-3.15-3776AB?logo=python&logoColor=white)](Dockerfile) [![FastAPI](https://img.shields.io/badge/FastAPI-framework-009688?logo=fastapi&logoColor=white)](requirements.txt) [![MariaDB 11.8](https://img.shields.io/badge/MariaDB-11.8-003545?logo=mariadb&logoColor=white)](compose.yaml) [![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](compose.yaml)\
[![Ollama](https://img.shields.io/badge/Ollama-local%20models-111111)](https://github.com/ollama/ollama) [![Latest release](https://img.shields.io/github/v/release/drakeg/madmallards-code?include_prereleases)](https://github.com/drakeg/madmallards-code/releases)


A self-hosted AI coding platform, built iteratively with Scrum.

**Status:** Active pre-release development. Working LAN chat with local Ollama models, MariaDB-backed logins and conversation history, read-only repository browsing, AI-generated code diffs, public GitHub status, safe repository import and a host-only isolated Python test runner. **Automatic file edits and GitHub writes are not yet implemented.**

## Quick start

1. Copy `.env.example` to `.env` and **change both database passwords**.
2. Run `docker compose up --build -d` to apply Alembic migrations.
3. Run `docker compose exec -T app python -m app.bootstrap_admin --username admin` to create the first database-backed account; save its generated password.
4. Browse to `http://<mac-lan-ip>:8096` and sign in with the generated username and password.
5. Validate with `docker compose ps` and `curl http://localhost:8096/health`.

The application listens across the trusted LAN by default, with password-protected
browser and API endpoints. HTTP is unencrypted; do not expose it to the internet.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check app tests migrations scripts
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

Install and start Ollama on the Docker host, then pull a model such as `ollama pull qwen3:4b`.
The Compose web application connects to the host using `OLLAMA_BASE_URL`. If you run
Ollama on another trusted machine, configure its reachable URL in the ignored `.env`.

- `GET /api/v1/models` lists locally available models (cloud-backed Ollama entries are excluded).
- `POST /api/v1/models/chat` accepts `{"model":"qwen3:4b","messages":[{"role":"user","content":"Hi"}]}`
  and responds with newline-delimited JSON events of type `token`, `done`, or `error`.

The API also powers the browser chat and persistent conversations. All model endpoints
require database-backed login. The LAN HTTP connection is unencrypted and must
not be exposed to the internet.

## Browser chat (MMC-006)

Open http://localhost:8096 and select a local model. Start a conversation, enter a
question, and watch the response stream. Messages are persisted in MariaDB, so
you can return to earlier conversations after reloading the page.

This is a **trusted-LAN development build** with database-backed login.
Per-user conversation/workspace isolation, concurrency safety and agent write
permissions remain unfinished. Cancelling a response saves the question but not
a partial assistant answer. Do not expose it publicly.

## Read-only repository workspace browser

Create `workspaces/` in this project (or set `WORKSPACES_HOST_PATH` in `.env`
to an explicitly approved directory). Put individual repository folders directly
under it, for example `workspaces/myproject/`. Only this directory is mounted
into the application, **read-only**. Hidden files, symlinks, large files, and
common secret/configuration paths are excluded from file previews.

The `/api/v1/workspaces` endpoints provide workspace listing, directory trees,
and bounded text previews. This **does not grant the AI write or shell access**.
Login is required, but robust per-user workspace isolation is not yet implemented.
The default bind host allows trusted-LAN testing and should not be internet-exposed.

## Ask the AI about a repository file

Use the sidebar workspace browser to preview an allowed text file, then select
**Attach to next question**. The contents are transmitted to the configured
local Ollama instance only when you submit that question; they are not silently
included merely because you preview a file. Attachments are bounded to 24 KB.

File content is treated as untrusted reference data. This is a read-only coding
assistant increment, **not** a permission to modify files or execute commands.
Do not attach confidential text to any provider you do not control.

## Propose a code change without writing files

Open a repository text file in the sidebar and expand **Draft a proposed
replacement**. Edit the proposed text and select **Preview diff**. The API
compares it with the original and returns a unified diff with a SHA-256
staleness check. This is a **dry-run only**: there is no apply endpoint,
and the repository mount remains read-only.

## AI-generated file proposals

In the file preview panel, enter the requested code change and choose
**Generate AI diff**. The local model produces a candidate replacement, which
is returned as a read-only diff after rechecking the file SHA-256 baseline.
This does not grant file-editing access or execute model-generated commands.
Model output is untrusted; review every line.

## Docker build safety

Build context is restricted to runtime source, migrations, and requirements by
`.dockerignore`. Never commit credentials into runtime source or mount local
workspace credentials into the web app. To diagnose Docker
Desktop failures, use `docker info`, `docker compose ps`, and targeted Compose
logs, each with a timeout; do not delete volumes or restart the Docker engine
without checking other running workloads.

## Troubleshoot localhost:8096 safely

Run `python3 scripts/diagnose_deployment.py` on the Docker host. The report
identifies whether Docker Engine, the project containers, and the app health
endpoint respond within explicit timeouts. This does not modify or restart
containers; protect MariaDB data and unrelated running stacks during recovery.

## Integration checks in GitHub Actions

The `compose-smoke` CI job builds both application images, brings up an isolated
MariaDB + app stack on an ephemeral GitHub runner, and checks the homepage,
health endpoint and workspace API. It never operates on local Docker Desktop,
so a successful check does **not** mean the Mac deployment is healthy.

## Export a reviewed patch

After generating or editing a proposed diff, select **Download reviewed .patch**.
This downloads the unified diff to your browser without modifying repository files.
Review the patch and use `git apply --check <filename>.patch` in a trusted local
repository before any manual application. Never apply unreviewed AI-generated code.

## Access from other devices on your local network

Docker Compose publishes the web interface to all host interfaces by default
(`APP_BIND_HOST=0.0.0.0`). Find the Docker host's LAN IPv4 address and browse
to `http://<host-lan-ip>:8096` from any device on the same trusted network.
Use `APP_PORT` to customize the port. Use `APP_BIND_HOST=127.0.0.1` in your
local `.env` to disable LAN access.

**Security:** The service requires database-backed login but HTTP traffic is
unencrypted. Do not forward the port on your router or expose it to the internet,
public Wi-Fi or other untrusted networks. Per-user authorization and HTTPS are
required before wider deployment. MariaDB is not published to the host.

## LAN login protection

The web UI, chat APIs, repository browser, and AI diff APIs require a
MariaDB-backed login. Passwords are stored as Argon2 hashes, and only
SHA-256 hashes of opaque session tokens are stored in MariaDB. A session
expires after eight hours; **Sign out** deletes the server-side session.
Bootstrap the first account using the CLI above. No user password or
session-signing secret is configured through `.env`.

The development site uses HTTP on a trusted LAN. Network traffic, including
the login password and subsequent session cookie, is **not encrypted**.
Use HTTPS via a trusted reverse proxy or VPN before using it on untrusted
networks. Set `APP_COOKIE_SECURE=1` only when serving through HTTPS.
Never publish port 8096 to the public internet. Database users do not yet
provide per-user isolation of chats or workspaces.

## Database-backed login administration

After migrations, create the first administrator with:
`docker compose exec -T app python -m app.bootstrap_admin --username admin`.
Save the generated password securely; only its Argon2 hash is stored.
For an explicit password reset (which also revokes sessions):
`docker compose exec -T app python -m app.bootstrap_admin --username admin --rotate`.
Existing projects, chats and other database records remain untouched.
Never commit credentials. HTTP LAN traffic is not encrypted: use HTTPS or a VPN
before exposing the application beyond a trusted network.

## Read-only GitHub status (MMC-011)

The LAN interface now provides **Check GitHub** to inspect a public repository
using `owner/repo`, with its default branch, up to 12 branches, 12 open PRs,
and 10 recent CI runs. This uses GitHub's unauthenticated public REST API,
so rate limits apply and private repositories will not be exposed.
The app has **no GitHub token**, cannot push code, merge PRs, or modify GitHub.
Keep local login enabled. Future GitHub write integration will require scoped
credentials, consent, and an audit trail.

## Import public GitHub repositories into workspaces

From the Docker host, use `python3 scripts/import_public_repo.py owner/repo`
to shallow-clone a public repository into `workspaces/<repo>/`. The existing
read-only Docker mount immediately exposes its text files through the sidebar;
`.git` metadata and hidden files are excluded from previews. For an explicit
name, use `--name safe-folder-name`. If `WORKSPACES_HOST_PATH` points to a
custom approved host folder, pass that path with `--root`.

The importer accepts only GitHub HTTPS owner/repo identifiers, disables
interactive credentials, does not initialize submodules or use custom Git
hooks, times out after 120 seconds, and will not overwrite an existing
workspace. It does not grant the model file-write or shell access. Do not
import untrusted repositories for execution; files are reference data only.

## Sandboxed Python tests (MMC-010)

On the trusted Docker host, run `python3 scripts/run_isolated_tests.py <workspace>`
to execute the selected workspace's `unittest` test discovery in a disposable
Python 3.15 container. The image must already be present locally (`docker pull
python:3.15-slim` once, if required). This CLI is **not** exposed as an HTTP
endpoint and never mounts the Docker socket into the application. It binds
only the selected workspace **read-only**, disables networking, runs as an
unprivileged user with all capabilities dropped, limits CPU/memory/processes,
and enforces a 90-second timeout. It rejects zero discovered tests.

Only Python standard-library `unittest` suites are supported initially.
There is no generic shell-command execution, pip install, privileged mode,
or write access. Docker sandboxes reduce risk but are not a security boundary
against all kernel exploits; do not run untrusted code on sensitive machines
without further isolation. Future work: temporary copy-on-write workspaces,
pytest image support, and an explicit UI approval workflow.

## Workbench interface

The UI follows the bespoke design tokens in [`docs/BRAND.md`](docs/BRAND.md),
with a developer-focused workspace rail, responsive model toolbar, code-reading
surfaces and prompt starter cards. The underlying Bootstrap 5 and authenticated
APIs are unchanged. On small screens, use **Explore** to open the repository rail;
press Escape to close it. Use Cmd/Ctrl+K to start a conversation. Suggested
prompts populate the composer but never submit or contact Ollama automatically.

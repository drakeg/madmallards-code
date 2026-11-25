# Security baseline

This is a development foundation, not production-ready remote execution software.

- Bind the web app to localhost by default.
- Keep secrets in untracked `.env`; never commit tokens or model keys.
- Runtime container uses a non-root UID, read-only root filesystem, and no-new-privileges.
- Database has no published host port.
- Do not mount the Docker socket into the web app.
- Agent shell, credential handling, workspace path containment, and sandbox network policies
  must be threat-modeled and reviewed before implementation.
- Require explicit consent gates for destructive commands and merges.
- Pin dependencies to reviewed secure releases before production release; baseline ranges
  and image tags need routine vulnerability scanning and lockfile management.

## Database major upgrades

MariaDB major upgrades must not be automated against an existing persistent volume.
Keep 11.8 until a verified backup, restoration test, compatibility review, and
explicit migration procedure are available. Renovate ignores MariaDB major upgrades.

## Docker build context

The root `.dockerignore` uses an allowlist and includes only `requirements.txt`,
`app/`, `migrations/`, and `alembic.ini` in the build context. It excludes
`.env` files, credentials, `.git`, workspace snapshots, and local data.
All Dockerfile COPY instructions must remain synchronized with this allowlist.
The CI test `tests/test_docker_context.py` validates both.

## Non-destructive Docker diagnostics

Run `python3 scripts/diagnose_deployment.py` for bounded, read-only local
checks. It probes Docker Engine (5 seconds), then local app HTTP health and
only if the engine is responsive does it inspect project containers. The
script never restarts the daemon, mutates containers, prints secret values,
or changes volumes. If Docker commands time out, inspect Docker Desktop
and other running workloads before considering any restart.

## Local-network listening

The app's Compose binding defaults to `APP_BIND_HOST=0.0.0.0` to support
LAN testing. This does not add authentication: only use on trusted networks,
with no router port forwarding. Set `APP_BIND_HOST=127.0.0.1` for local-only
access. The MariaDB service remains internal to Docker's private network.
Add authentication and access restrictions before production deployment.

## Database-backed authentication

Users live in MariaDB with Argon2 hashed passwords and unique usernames.
Sessions are revocable database rows containing only SHA-256 token digests,
not bearer tokens. The login endpoint is throttled, state-changing requests
perform an Origin check, and the cookie is HTTP-only with SameSite=Strict.
The health endpoint is public for Docker health probes. Login data does not
come from .env. Create/reset an admin with `python -m app.bootstrap_admin`
after migrations. HTTP LAN access remains unencrypted; add HTTPS before
internet-facing use. A shared workspace is not yet per-user isolated.

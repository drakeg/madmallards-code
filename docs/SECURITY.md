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

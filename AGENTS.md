# Coding-agent instructions

These rules apply to coding agents and human contributors working in this repository.

## Purpose and priorities

Build a practical, self-hosted coding assistant for SMB engineering teams.
Prioritize usable local-model chat, safe repository workflows, verified tests,
and a path toward approved code changes. Keep Docker Compose inexpensive.

## Development loop

1. Read the open GitHub issues, current sprint plan in `docs/SPRINTS.md`, and related tests.
2. Fix broken behavior and red CI before adding new features.
3. Make changes on a focused `feature/`, `fix/`, or `ci/` branch, referencing an issue.
4. Run `ruff check app tests migrations scripts`, `pytest -q`, and `docker compose config` with required development DB placeholders.
5. Verify changed workflows in an isolated or live test environment; report unverified operations clearly.
6. Open a reviewable PR; merge after required checks pass without imposing unnecessary mandatory reviews.
7. Continue to the next ready backlog item, keeping relevant documentation synchronized.

## Safety boundaries

- Never commit `.env`, raw passwords, session tokens, SSH keys, or user files.
- Preserve the named MariaDB data volume and existing project/chat records.
- Do not expose Docker socket, shell execution or host writable mounts via the web app.
- Review model-generated diffs; do not automatically run or apply them.
- Use fixed-image, read-only, network-isolated sandboxes for explicitly requested tests.
- Keep unauthenticated health checks minimal. Authenticated LAN HTTP is not internet-safe; HTTPS and per-user isolation are outstanding work.
- Do not restart Docker Desktop or unrelated containers for a routine change.

## README badges

Keep dynamic GitHub Actions, license, issue, PR and release badges accurate.
Only advertise Python, frameworks, MariaDB, Docker, local model support or
versions after checking `Dockerfile`, `requirements.txt`, `compose.yaml` and
`.github/workflows`. Maintain badges directly below the root README title,
within three compact rows. Static badge validity is checked in CI tests.

## Releases

Follow semantic versioning for actual tagged releases. Record verified changes
in `RELEASES.md` and never invent a published tag, passing status or metrics.
The application is currently pre-release development.

## Frontend dependency maintenance

The Bootstrap 5.3.3 CSS bundle is vendored in `app/static/vendor/bootstrap/`
with its upstream MIT license. Do not silently introduce remote CDN runtime
requirements or copy paid design blocks. If updating this dependency, verify
upstream version, license, checksum, styles and browser QA at responsive widths.

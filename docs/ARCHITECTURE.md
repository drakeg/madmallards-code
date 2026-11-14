# Architecture — ADR-000 baseline

- Python FastAPI for HTTP API and initial server-rendered Bootstrap 5 interface.
- MariaDB 11.8 LTS as persistent database for future projects, sessions, and task state.
- Docker Compose for local runtime; app container is non-root/read-only.
- Future agent runtime will use separate disposable sandbox containers, not app-host shell.
- Ollama and API-provider adapters are planned, not implemented.
- Future authentication and authorization are required before network exposure.

## Current components
`app` serves `/`, `/health`, `/api/v1/info`, and OpenAPI `/docs`.
`db` is provisioned and health-checked, but persistence models/migrations remain open backlog items.

## Decision rationale
Server-rendered UI reduces initial operational complexity; client-side enhancements can
be introduced after agent workflows stabilize. MariaDB supports the user's existing stack
preference without introducing multiple database engines.

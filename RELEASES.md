# Releases and development milestones

No formal GitHub release tag is asserted by this document. The milestones
below describe merged development features, not independently published releases.

## Unreleased — active pre-release development

- Creative Studio workbench and responsive login refresh, offline Bootstrap CSS, conversation search
- Local Ollama model discovery and streaming chat; MariaDB-backed history
- Database-backed Argon2 passwords, revocable server-side sessions and admin bootstrap
- Read-only repository browser, explicit file context, AI-generated diffs, patch export
- Authenticated LAN UI with public GitHub PR/branch/Actions status
- Safe host-side public-repository workspace import and isolated unittest runner
- MariaDB migrations, Docker Compose deployment and CI smoke testing

## Remaining for a production-ready release

- HTTPS and per-user authorization boundaries
- Approved sandboxed writes to isolated workspaces with rollback and audit logs
- Authorized GitHub PR lifecycle and private-repository integration
- Broader end-to-end UI tests, concurrency safeguards, and release packaging

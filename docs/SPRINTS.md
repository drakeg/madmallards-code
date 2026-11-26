# Sprint roadmap

Each sprint is two weeks; dates are assigned at sprint planning, not assumed.

| Sprint | Goal | Exit |
|---|---|---|
| 1 | Foundation | Compose app starts, API and UI respond, CI green, docs ready |
| 2 | Local AI chat | Stream local model reply and restore session |
| 3 | Safe workspaces | Edit files and test in isolated sandbox |
| 4 | GitHub workflows | Create a tested, reviewable PR |
| 5 | Autonomous tasks | Plan, execute, recover with approvals |
| 6 | Release candidate | Dashboard and audited release tests |

## Sprint 1 execution
- MMC-001 architecture, docs and repository: in progress
- MMC-002 Compose with database and health checks: in progress
- MMC-003 persistence models/migrations implemented; test and PR review pending
- MMC-004 Bootstrap 5 shell: in progress
- Test and CI validation required before declaring completion

## Sprint 2 implementation candidate

- MMC-005 local Ollama adapter, model discovery, streaming API, mock tests
- MMC-006 responsive browser chat and persisted sessions (following increment)

## MMC-006 — Usable browser chat increment

- Responsive Bootstrap 5 chat composer and conversation sidebar
- Model selector backed by installed local Ollama models
- NDJSON response streaming with stop button
- MariaDB persistence for user and assistant messages
- Conversation history reload and automated API tests

Still out of scope: GitHub code-edit agents, multi-user security, concurrency locks, token budgets.

## MMC-008 — Read-only workspace discovery increment

- Bind only an administrator-selected dedicated host directory, read-only, into the app
- Expose workspace list, safe directory tree and text preview API endpoints
- Explicitly reject hidden files, known secrets, symlinks, traversal and large/binary files
- Provide file preview in the web interface without execution or editing
- Remaining: authorized workspace provisioning and isolated write-capable agent workers

## MMC-009 — Explicit read-only file context (increment)

- Attach one reviewed repository text file to a chat turn using a visible UI action
- Server revalidates workspace path, extension and 24 KB attachment limit
- File content sent as untrusted reference, not an executable agent instruction
- Persistent user question remains separate from transient attached source text
- No file editing or executable tool grants in this increment

## MMC-009 — Reviewed change proposals (next increment)

- Preview a proposed complete-file replacement as a unified diff
- Check SHA-256 baseline to reject stale edits and preserve source files
- No apply endpoint, filesystem modification, or shell execution
- Manual reviewer approval and isolated write-enabled workers remain future work

## MMC-022 — Local AI-generated proposals

- Selected local Ollama model generates proposed complete-file text on request
- Source path and SHA-256 baseline checked before and after inference
- No write/apply endpoint; model output shown only as a diff
- Incomplete and oversized responses rejected

## MMC-024 — Docker Compose integration smoke test

- Build and start the actual FastAPI + MariaDB stack on an ephemeral CI runner
- Confirm Alembic migrations complete before app becomes healthy
- Verify HTTP health, browser composer markup and workspace API
- Bound build/start/log/cleanup operations to avoid indefinite CI hangs
- Preserve all volumes on the user's local Docker host (CI only)

## MMC-025 — Export reviewed patches

- Download the current reviewed unified diff as a patch file
- Hide stale patch download after navigating to another file or a failed preview
- Never automatically apply or execute the downloaded patch

## LAN accessibility

- Configurable `APP_BIND_HOST`, default all interfaces for LAN testing
- Keep MariaDB container-only and retain named volume
- Validate binding and health from host LAN IP
- Backlog: mandatory authentication for any shared or internet deployment

## MMC-026 — LAN access protection

- Fail-closed single-user password gate for browser and APIs
- Signed, time-limited HTTP-only session, logout, login throttling
- Authentication smoke checks in CI and negative security tests
- Next backlog: HTTPS termination and individual user accounts

## MMC-027 — Access credential bootstrap

- One-command local password/signing-secret generation
- No database configuration changes and no committed secrets
- Atomic writes, restrictive file permissions, and explicit rotation
- Tests for missing `.env`, symlink handling and credential preservation

## MMC-028 — Database user accounts and revocable sessions

- Alembic migration adds users and auth_sessions without touching existing chats
- Argon2 password hashes and short-lived opaque cookie tokens, server-side revocation
- Explicit admin bootstrap/reset CLI; no credentials in .env or repository
- Updated authentication regression tests and full Compose login smoke test

## MMC-011 — Public GitHub status increment

- Show public repository metadata, branches, open PRs and recent CI conclusions
- Validate owner/repo, limit response sizes and restrict upstream to GitHub API
- Do not require tokens, credentials, repository writes or other GitHub permissions
- Add mocked HTTP tests including rate-limit, missing repo and invalid input
- Remaining: authorized private repos and state-changing PR/branch workflows

## MMC-008 — Public repository provisioning increment

- Add safe host-side import of explicit public GitHub owner/repo identifiers
- Shallow clone without token, interactive prompts, hooks, or submodules
- Stage then rename to avoid partial imports; refuse overwriting workspaces
- Keep the application mount read-only and credentials outside source control
- Add tests for input safety, non-overwrite, failure cleanup and timeout
- Remaining: authorized private repositories, authenticated GUI provisioning

## MMC-010 — Restricted host-side test runner increment

- One fixed Python unittest discovery command, not arbitrary shell execution
- Disposable container, network disabled, non-root, read-only repo mount
- CPU/memory/PID limits, reduced privileges and execution timeout
- Validate workspace location and forbid symlink workspaces
- Fail closed on absent tests, timeouts, missing Docker or test errors
- Remaining: isolated writable agent worker and authenticated approval UI

## MMC-029 — Creative Studio workbench UI

- Preserve working Bootstrap 5, local model chat, file explorer, code diff review and GitHub pulse
- Replace generic dark/light framing with an original developer workbench design system
- Add mobile sidebar controls, accessible labels/focus, reduced-motion CSS and starter prompts
- Test the existing widget IDs, actual JS syntax, responsive breakpoints and UI asset availability
- Document brand tokens and design provenance without claiming a finalized logo

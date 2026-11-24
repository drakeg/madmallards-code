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

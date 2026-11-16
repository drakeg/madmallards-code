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

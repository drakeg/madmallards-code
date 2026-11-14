# Product Requirements (initial)

## Vision
An extensible, self-hosted OpenCode-style AI coding environment without application-imposed
daily prompt quotas. Local inference is constrained by hardware; external APIs by terms,
provider rate limits, and billing.

## Personas
Developer managing multiple GitHub projects; administrator maintaining models and execution policies.

## MVP capabilities
1. Project workspaces with persistent conversations.
2. Local OpenAI-compatible/Ollama model support with streamed responses.
3. Scoped file reading, edits and human-reviewed diffs.
4. Sandboxed, policy-controlled tool invocation and test execution.
5. GitHub branch, commit, pull request, and CI integration.
6. Visible task queue, logs, status, and recovery.

## Non-functional requirements
Single Docker Compose development stack; Bootstrap 5 UI; accessible navigation;
auditable actions; no secret leakage; documented backup/recovery; regression tests.

## Acceptance
No 'unlimited' promises for third-party provider limits. No unrestricted host shell access.
No autonomous merge without explicitly configured governance.

## External dependency
Maitis resource #r045 must be reviewed once its full prompt text is supplied.

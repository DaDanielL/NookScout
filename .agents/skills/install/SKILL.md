---
name: install
description: Use when a project needs dependency installation, local setup, service startup, and setup verification.
---

# Install

Prepare the project for local development using the commands documented in `AGENTS.md`.

**Input**: the user request, supplied path, issue or PR reference, or current conversation context

---

## Phase 1: Read Setup Instructions

Read:

1. `AGENTS.md`
2. `README.md`
3. Package or workspace manifests
4. Environment examples such as `.env.example`
5. Docker or compose files, if present

Identify:

- Package manager
- Dependency install command
- Required environment variables
- Database or service setup
- Development server command
- Verification URL or smoke test, if applicable

---

## Phase 2: Install and Setup

Run only commands that apply to this project. Common examples:

```bash
{install-command}
{database-setup-command}
{codegen-command}
{dev-command}
```

If a command requires secrets, paid services, destructive database changes, or external infrastructure, stop and ask before running it.

If this repository is only the reusable AI-agent-layer template, do not scaffold or start a demo app.

---

## Phase 3: Verify

Verify setup with the project's documented smoke check:

- Dev server reachable, if applicable
- CLI command runs, if applicable
- Tests or build pass, if setup expects that
- Generated files are present, if codegen is required

---

## Report

Output a concise summary:

- **Dependencies**: installed / already up to date / skipped
- **Environment**: configured / missing required values / not needed
- **Services**: started / not applicable / blocked
- **Verification**: passed / failed / not run
- **Issues**: any blockers and next action

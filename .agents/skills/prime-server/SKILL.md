---
name: prime-server
description: Use before backend work when Codex needs to learn server architecture, data flow, contracts, and validation patterns.
---

# Prime Server: Load Backend Context

**Input**: the user request, supplied path, issue or PR reference, or current conversation context

## Objective

Understand the server-side architecture, data flow, contracts, and validation patterns before making backend changes.

---

## Step 0: Load GitHub Context

If the input includes a GitHub issue, use:

```bash
gh issue view {NUMBER} --json number,title,body,labels,state,url
```

If the input includes a GitHub PR, use:

```bash
gh pr view {NUMBER} --json number,title,body,files,state,url
```

---

## Step 1: Discover Server Shape

Read `AGENTS.md` first. Then identify backend code by looking for:

- API routes, controllers, handlers, resolvers, jobs, workers, or CLIs
- Service/domain layers
- Data access layers, repositories, ORMs, migrations, or schemas
- Validation schemas and request/response DTOs
- Auth, permissions, logging, configuration, and error handling
- Backend tests and fixtures

Use provided paths first. If no paths are provided, search common backend locations such as `src/`, `server/`, `api/`, `backend/`, `app/`, `packages/*`, and framework-specific directories.

---

## Step 2: Trace a Representative Flow

Find one existing backend flow similar to the requested work and trace it end to end:

1. Entry point
2. Validation
3. Authorization
4. Service/domain logic
5. Persistence or external calls
6. Error handling
7. Tests

Capture file:line references for patterns that implementation should mirror.

---

## Output

Summarize:

- **Backend Purpose**: what the server side is responsible for
- **Stack**: framework, runtime, database, validation, auth, logging
- **Data Flow**: request/job/event path through the system
- **Contracts**: important schemas, types, DTOs, or API shapes
- **Patterns**: service boundaries, errors, transactions, tests
- **Validation Commands**: backend-specific commands from `AGENTS.md` or project scripts

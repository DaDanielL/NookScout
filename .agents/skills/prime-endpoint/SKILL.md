---
name: prime-endpoint
description: Use before endpoint or external contract work when Codex needs to learn boundary, validation, auth, and test patterns.
---

# Prime Endpoint: Learn Contract Patterns

**Input**: the user request, supplied path, issue or PR reference, or current conversation context

## Objective

Understand how this codebase defines, validates, serves, tests, and documents API endpoints or external contracts.

Use this for REST routes, RPC handlers, GraphQL resolvers, webhooks, background jobs with external inputs, CLIs, or any boundary where another system calls into the project.

---

## Step 0: Load GitHub Context

If the input includes a GitHub issue or PR, inspect it:

```bash
gh issue view {NUMBER} --json number,title,body,labels,state,url
gh pr view {NUMBER} --json number,title,body,files,state,url
```

Use the command that matches the input.

---

## Step 1: Discover Endpoint Shape

Read `AGENTS.md` first. Then inspect:

- Existing route/handler/resolver/job definitions
- Request parsing and validation
- Auth and authorization checks
- Service/domain layer calls
- Persistence or external integrations
- Response formatting and error mapping
- Contract tests, integration tests, API docs, or schema generation

Use provided paths first. Otherwise search for framework-specific endpoint locations and terms such as `route`, `controller`, `handler`, `resolver`, `webhook`, `schema`, `service`, `repository`, and `test`.

---

## Step 2: Trace a Similar Contract

Find one existing endpoint or contract similar to the intended change and trace:

1. Input boundary
2. Validation
3. Authorization
4. Domain/service behavior
5. Data access or external call
6. Response or output shape
7. Tests and documentation

Capture file:line references for patterns to mirror.

---

## Output

Summarize:

- **Contract Type**: REST, GraphQL, RPC, webhook, CLI, job, or other
- **Flow**: boundary to response/output
- **Validation**: schemas, parsing, error messages
- **Auth/Security**: checks required before work happens
- **Persistence/Integrations**: where data is read/written or external calls happen
- **Tests**: patterns and commands to run
- **Examples to Mirror**: file:line references

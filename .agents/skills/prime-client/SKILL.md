---
name: prime-client
description: Use before frontend work when Codex needs to learn client architecture, UI patterns, and validation commands.
---

# Prime Client: Load Frontend Context

**Input**: the user request, supplied path, issue or PR reference, or current conversation context

## Objective

Understand the frontend architecture, design system, state/data patterns, and testing approach before making client changes.

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

## Step 1: Discover Client Shape

Read `AGENTS.md` first. Then identify frontend code by looking for:

- App/page/route directories
- Components and design-system primitives
- Styling setup and theme tokens
- State management and data fetching
- Forms, validation, loading, empty, and error states
- Frontend tests, visual tests, and end-to-end tests

Use provided paths first. If no paths are provided, search common frontend locations such as `src/`, `app/`, `pages/`, `components/`, `features/`, `client/`, `frontend/`, and `packages/*`.

---

## Step 2: Trace a Representative Flow

Find one existing UI flow similar to the requested work and trace it:

1. Route or screen entry point
2. Data loading
3. Component composition
4. State changes or mutations
5. Styling and accessibility patterns
6. Tests or manual verification

Capture file:line references for patterns that implementation should mirror.

---

## Output

Summarize:

- **Frontend Purpose**: what the UI is responsible for
- **Stack**: framework, styling, component library, state/data tools
- **Structure**: routes, features, components, utilities
- **Data Flow**: loading, mutation, caching, and error handling
- **Design Patterns**: layout, forms, accessibility, responsive behavior
- **Validation Commands**: frontend-specific checks from `AGENTS.md` or project scripts

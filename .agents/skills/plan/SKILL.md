---
name: plan
description: Use when a PRD, story, GitHub issue, or feature request needs a codebase-aware implementation plan.
---

# Implementation Plan Generator

**Input**: the user request, supplied path, issue or PR reference, or current conversation context

## Objective

Transform the input into a concrete implementation plan through codebase exploration and pattern extraction.

**Core principle**: Plan only. Do not edit product code while planning. Create a context-rich document that enables one focused implementation pass.

**Order**: Codebase first. The solution must fit existing project patterns and the rules in `AGENTS.md`.

---

## Phase 1: Parse

### Determine Input Type

| Input | Action |
|-------|--------|
| `.prd.md` file | Read the PRD and identify the next pending phase or story |
| `.stories.md` file | Read the story manifest and select the requested or next unplanned story |
| GitHub issue number or URL | Run `gh issue view` and use the issue body as source context |
| Other `.md` file | Read and extract the feature description |
| Free-form text | Use directly as feature input |
| Blank | Use conversation context |

Use GitHub CLI when useful:

```bash
gh issue view {NUMBER} --json number,title,body,labels,state,url
```

### Extract Feature Understanding

- **Problem**: What are we solving?
- **User Story**: As a [user], I want to [action], so that [benefit].
- **Type**: NEW_CAPABILITY / ENHANCEMENT / REFACTOR / BUG_FIX / SPIKE
- **Complexity**: LOW / MEDIUM / HIGH
- **GitHub Issue**: If an issue number or URL is available from `prime`, the user, the PRD, or a story manifest, capture it for plan metadata.

---

## Phase 2: Explore

### Read Required Context

1. Read `AGENTS.md` for project rules, architecture, commands, and validation expectations.
2. Read `.agents/README.md` if present for AI-layer workflow conventions.
3. Inspect the current branch and working tree:
   ```bash
   git branch --show-current
   git status --short
   ```

### Study the Codebase

Find:

1. **Similar implementations** with file:line references.
2. **Naming conventions** with real examples.
3. **Error handling patterns** and failure behavior.
4. **Type/schema/data contracts** relevant to the change.
5. **Test patterns** and verification style.
6. **Integration boundaries** such as API routes, services, jobs, UI flows, CLIs, or external systems.

Use `rg` and targeted file reads first. Avoid broad, noisy scans when a focused search is enough.

### Document Patterns

| Category | File:Lines | Pattern |
|----------|------------|---------|
| Naming | `path/to/file.ts:10` | {pattern description} |
| Errors | `path/to/file.ts:20` | {pattern description} |
| Types | `path/to/file.ts:1` | {pattern description} |
| Tests | `path/to/test.ts:1` | {pattern description} |

---

## Phase 3: Design

### Map the Changes

- What files need to be created?
- What files need to be modified?
- What existing behavior must remain stable?
- What dependencies or migrations are involved?
- What is the safest implementation order?

### Identify Risks

| Risk | Mitigation |
|------|------------|
| {potential issue} | {how to handle} |

---

## Phase 4: Generate

Create the directory if needed:

```bash
mkdir -p .agents/plans
```

Write the plan to:

```text
.agents/plans/{kebab-case-name}.plan.md
```

Use this structure:

```markdown
# Plan: {Feature Name}

## Summary

{One paragraph: what is changing and the implementation approach}

## User Story

As a {user type}, I want to {action}, so that {benefit}.

## Metadata

| Field | Value |
|-------|-------|
| Type | {type} |
| Complexity | {LOW/MEDIUM/HIGH} |
| Systems Affected | {list} |
| GitHub Issue | #{number}, {URL}, or N/A |
| Source PRD | `.agents/PRDs/{name}.prd.md` or N/A |
| Source Story | `.agents/stories/{name}.stories.md#STORY-001` or N/A |

---

## Patterns to Follow

### Naming

```text
SOURCE: {file:line}
{small relevant snippet or summary}
```

### Error Handling

```text
SOURCE: {file:line}
{small relevant snippet or summary}
```

### Tests

```text
SOURCE: {file:line}
{small relevant snippet or summary}
```

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `path/to/file.ts` | CREATE | {why} |
| `path/to/other.ts` | UPDATE | {why} |

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: {Description}

- **File**: `path/to/file.ts`
- **Action**: CREATE / UPDATE
- **Implement**: {what to do}
- **Mirror**: `path/to/example.ts:line` - follow this pattern
- **Validate**: `{specific command from AGENTS.md}`

### Task 2: {Description}

- **File**: `path/to/file.ts`
- **Action**: CREATE / UPDATE
- **Implement**: {what to do}
- **Mirror**: `path/to/example.ts:line`
- **Validate**: `{specific command from AGENTS.md}`

---

## Validation

List the exact commands from `AGENTS.md` or package scripts:

```bash
{typecheck-command}
{lint-command}
{test-command}
{build-command}
```

## End-to-End Verification

- [ ] {manual or automated smoke test for the changed workflow}
- [ ] {expected result}

## Acceptance Criteria

- [ ] All planned tasks completed
- [ ] Relevant tests added or updated
- [ ] Validation commands pass
- [ ] End-to-end verification passes
- [ ] Implementation follows `AGENTS.md`
```

---

## Phase 5: Output

```markdown
## Plan Created

**File**: `.agents/plans/{name}.plan.md`
**GitHub Issue**: #{number or N/A}

**Summary**: {2-3 sentence overview}

**Scope**:
- {N} files to create
- {M} files to update
- {K} total tasks

**Key Patterns**:
- {Pattern 1 with file:line}
- {Pattern 2 with file:line}

**Next Step**: Review the plan, then run `implement .agents/plans/{name}.plan.md`.
```

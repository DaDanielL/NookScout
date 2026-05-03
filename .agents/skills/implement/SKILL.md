---
name: implement
description: Use when Codex should execute an existing implementation plan with validation loops and write a report.
---

# Implement Plan

**Plan**: the implementation plan path supplied by the user

## Mission

Execute the plan end to end with rigorous self-validation.

**Core philosophy**: Validation loops catch mistakes early. Run focused checks as you work, then run the full validation suite before reporting completion.

**Golden rule**: If validation fails, fix it before moving on. Do not accumulate broken state.

---

## Phase 1: Load

### Read the Plan

Load the plan file and extract:

- **Summary**: What is being built
- **Patterns to Follow**: Code to mirror
- **Files to Change**: CREATE / UPDATE list
- **Tasks**: Implementation order
- **Validation Commands**: Exact commands to run
- **End-to-End Verification**: Manual or automated smoke tests
- **GitHub Issue**: Issue number or URL from the Metadata table, if present

If the plan is missing:

```text
Error: Plan not found at the user input
Create a plan first: plan "feature description"
```

If a GitHub Issue is linked, load current issue context:

```bash
gh issue view {NUMBER} --json number,title,body,labels,state,url
```

---

## Phase 2: Prepare

### Git State

```bash
git branch --show-current
git status --short
```

| State | Action |
|-------|--------|
| On main/default branch and clean | Create a branch: `git checkout -b feature/{plan-name}` |
| On main/default branch and dirty | Stop and ask before touching unrelated work |
| On feature branch | Continue on the current branch |

Respect existing user changes. Do not revert files you did not change unless explicitly asked.

---

## Phase 3: Execute

For each task in the plan:

### 3.1 Verify Assumptions

Before editing:

- Read the target file.
- Read adjacent files that import it or are imported by it.
- Verify referenced functions, interfaces, routes, tables, commands, or components still exist.
- If the plan is stale, adapt the implementation and document the deviation.

### 3.2 Implement

- Follow the plan's **Mirror** references and `AGENTS.md` conventions.
- Make the smallest coherent change for the task.
- Check integration points: imports, callers, data flow, API contracts, and user-visible behavior.

### 3.3 Validate Immediately

Run the task-specific validation command from the plan. If none is listed, run the smallest relevant command from `AGENTS.md`.

If validation fails:

1. Read the error.
2. Fix the implementation or test.
3. Re-run validation.
4. Continue only when passing or when the failure is clearly unrelated and documented.

### 3.4 Track Progress

```text
Task 1: CREATE src/x.ts - done
Task 2: UPDATE src/y.ts - done
```

Document any deviations from the plan with the reason.

---

## Phase 4: Validate

### Run All Checks

Run every validation command specified in the plan. If the plan is incomplete, use `AGENTS.md` and project scripts to identify the full check set, commonly:

```bash
{typecheck-command}
{lint-command}
{test-command}
{build-command}
```

### Write or Update Tests

Add tests when behavior changes:

- New domain logic should have direct tests.
- New UI, API, CLI, or workflow behavior should have integration or end-to-end coverage when practical.
- Edge cases and error cases should be covered.
- Update existing tests when expected behavior changes.

### Required End-to-End Verification

Re-read the plan and execute every end-to-end step as a checklist:

- [ ] Start required services if applicable.
- [ ] Exercise the changed workflow exactly as described.
- [ ] Verify the expected outcome.
- [ ] Fix and re-run if the result does not match.

If the plan has no end-to-end section, perform a reasonable smoke test for the changed behavior and document what you checked.

Do not report the implementation as complete until validation and smoke testing are done or a blocker is documented clearly.

---

## Phase 5: Report

Create the directory if needed:

```bash
mkdir -p .agents/reports
```

Write the report to:

```text
.agents/reports/{plan-name}-report.md
```

Use this structure:

```markdown
# Implementation Report: {Feature Name}

**Plan**: `{plan-path}`
**Branch**: `{branch-name}`
**GitHub Issue**: #{number}, {URL}, or N/A
**Status**: COMPLETE

## Summary

{Brief description of what was implemented}

## Tasks Completed

| # | Task | File | Status |
|---|------|------|--------|
| 1 | {description} | `src/x.ts` | Done |

## Validation Results

| Check | Result |
|-------|--------|
| Type check | Pass/Fail/Not run |
| Lint | Pass/Fail/Not run |
| Tests | Pass/Fail/Not run |
| Build | Pass/Fail/Not run |
| E2E / Smoke | Pass/Fail/Not run |

## Files Changed

| File | Action | Notes |
|------|--------|-------|
| `src/x.ts` | CREATE | {notes} |

## Tests Written

| Test File | Test Cases |
|-----------|------------|
| `src/x.test.ts` | {list} |

## Deviations from Plan

{List deviations with rationale, or "None"}
```

### Archive Plan

After the report is written:

```bash
mkdir -p .agents/plans/completed
mv the user input .agents/plans/completed/
```

---

## Phase 6: GitHub Handoff

Use GitHub CLI where useful.

### Linked Issue

If the plan has a GitHub Issue, include the issue in the final report and recommend the next issue transition or label update. If the local environment and permissions allow comments, add a concise implementation note:

```bash
gh issue comment {NUMBER} --body-file .agents/reports/{plan-name}-report.md
```

Use this only when appropriate for the repository. If commenting is not desired or unavailable, leave the local report as the source of truth.

### Pull Request

If the branch has completed implementation changes and the user wants a PR, use:

```bash
gh pr create --fill
gh pr view --web
```

If the PR body needs more detail, use the implementation report as source material.

---

## Phase 7: Output

```markdown
## Implementation Complete

**Plan**: `{plan-path}`
**Branch**: `{branch-name}`
**GitHub Issue**: #{number or N/A}
**Status**: Complete

### Validation

| Check | Result |
|-------|--------|
| Type check | Pass/Fail/Not run |
| Lint | Pass/Fail/Not run |
| Tests | Pass/Fail/Not run |
| Build | Pass/Fail/Not run |
| E2E / Smoke | Pass/Fail/Not run |

### Artifacts

- Report: `.agents/reports/{name}-report.md`
- Plan archived: `.agents/plans/completed/`

### Next Steps

1. Review the report.
2. Create or inspect a PR with `gh pr create` or `gh pr view`.
3. Merge when approved.
```

---

## Handling Failures

| Failure | Action |
|---------|--------|
| Type check fails | Read the error, fix the issue, re-run |
| Tests fail | Fix the implementation or test, re-run |
| Lint fails | Run the project formatter if appropriate, then manual fixes |
| Build fails | Check error output, fix, and re-run |
| E2E fails | Reproduce, fix behavior, re-run the scenario |

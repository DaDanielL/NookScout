---
name: validate
description: Use when current work needs project validation commands discovered, run, and summarized.
---

# Validate

Run the validation checks defined for this project and report results clearly.

**Input**: the user request, supplied path, issue or PR reference, or current conversation context

---

## Phase 1: Discover Commands

Read `AGENTS.md` first. Use its validation section as the source of truth.

If `AGENTS.md` is missing or incomplete, infer commands from project files:

| Ecosystem | Common Files | Common Commands |
|-----------|--------------|-----------------|
| Node/JS/TS | `package.json` | package scripts for lint, typecheck, test, build |
| Python | `pyproject.toml`, `requirements.txt` | `pytest`, `ruff`, `mypy`, project scripts |
| Rust | `Cargo.toml` | `cargo fmt --check`, `cargo clippy`, `cargo test` |
| Go | `go.mod` | `go test ./...`, `go vet ./...` |
| Java/Kotlin | `pom.xml`, `build.gradle*` | Maven or Gradle test/build tasks |

Prefer exact project scripts over generic commands.

---

## Phase 2: Run Checks

Typical validation categories:

1. Formatting
2. Linting
3. Type checking or static analysis
4. Unit tests
5. Integration tests
6. Build
7. End-to-end or smoke checks, when relevant

Run only commands that apply to this project and scope. Capture failures exactly enough that the next fix is obvious.

---

## Phase 3: Report

Use this format:

```markdown
## Validation Results

| Check | Command | Result | Details |
|-------|---------|--------|---------|
| Lint | `{command}` | Pass/Fail/Skipped | {details} |
| Type check | `{command}` | Pass/Fail/Skipped | {details} |
| Tests | `{command}` | Pass/Fail/Skipped | {details} |
| Build | `{command}` | Pass/Fail/Skipped | {details} |

### Summary

- **Status**: ALL PASSING / FAILURES FOUND / BLOCKED
- **Action needed**: {None or concrete fixes}
```

---

## If Failures Are Found

List each actionable failure with:

1. File and line number, if available
2. Error message
3. Likely cause
4. Suggested fix, if clear

Example:

```markdown
### Failures

1. **src/service.ts:42**
   - Error: `Type 'string' is not assignable to type 'number'`
   - Likely cause: changed API contract
   - Fix: update the type or convert the value before assignment
```

If a command cannot run because dependencies are missing, say which install/setup command is needed from `AGENTS.md`.

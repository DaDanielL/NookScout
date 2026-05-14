# Code Review: Issue #10 Unstaged Changes

**Scope**: current unstaged changes for GitHub issue #10, `STORY-010: Persist Indicator Snapshots and Refresh Pipeline`
**Recommendation**: NEEDS WORK

## Summary

Reviewed the indicator snapshot contracts, refresh service, persistence model/repository changes, Alembic migration, tests, documentation updates, implementation report, and completed plan artifact. The implementation covers the main snapshot persistence and cached-candle refresh flow well, and the automated backend validation passes. One issue needs attention before approval: failure-log sanitization can still leak secret values.

## Issues Found

### Critical

None.

### High Priority

1. **`app/indicators/refresh.py:299`**
   - Error: `_safe_log_message()` redacts secret keywords but leaves their values in the logged `error_message`.
   - Why it matters: Issue #10 explicitly requires refresh failures to be logged without secrets. For an exception like `password=hunter2` or `apiKey=abc123`, the current regex turns the key label into `[redacted]` but still logs `hunter2` / `abc123`.
   - Likely cause: The test only asserts forbidden fragments such as `token`, `secret`, and `password` are absent; it does not include realistic key-value examples and assert the values are removed too.
   - Recommendation: Prefer not logging arbitrary exception text at all, since `error_type` plus symbol/provider/date/version already gives useful context. If the message is kept, redact complete key-value patterns and add tests for representative values, for example `password=hunter2`, `apiKey=abc123`, `Authorization: Bearer test-token`, and database URLs.

### Medium Priority

None.

### Suggestions

None.

## Validation Results

| Check | Status |
|-------|--------|
| Lint | PASS: `uv run ruff check .` |
| Format | PASS: `uv run ruff format --check .` |
| Type Check | PASS: `uv run mypy .` |
| Tests | PASS: `uv run pytest` (`127 passed`) |
| Frontend | SKIPPED: no `package.json` is present and the issue #10 scope is backend/docs only |

## What's Good

- The snapshot table and repository preserve immutable, versioned records with input ranges, completeness flags, JSON indicator payloads, benchmark metadata, and latest lookup helpers.
- The refresh service composes cached candle reads with existing deterministic indicator functions and does not call providers directly.
- Repository and refresh tests cover creation, latest/versioned lookup, incomplete state persistence, missing benchmarks, and per-symbol refresh failures.

## Recommendation

Update the failure-message sanitization and add regression coverage for secret values, then rerun backend validation.

---

## Follow-up Review: Current Unstaged Changes

**Scope**: Current unstaged worktree after failure-log sanitization fix for GitHub issue #10
**Recommendation**: APPROVE

### New Issues Found

#### High Priority

1. **`app/indicators/refresh.py:299`**
   - Error: `_safe_log_message()` redacts secret keywords but leaves their values in the logged `error_message`.
   - Likely cause: The test only asserted forbidden fragments such as `token`, `secret`, and `password` were absent; it did not include realistic key-value examples and assert the values were removed too.
   - Fix: Avoid logging arbitrary exception text. Preserve `error_type` plus symbol/provider/date/version context, and add regression coverage for representative secret values.
   - Resolution: Fixed in the current unstaged changes. `_failure()` now stores the generic message `Indicator refresh failed.` while preserving `error_type`, symbol, provider, calculation date, and calculation version. `test_refresh_failure_logs_context_without_secrets` now uses fake key-value secrets including `apiKey=abc123`, `password=hunter2`, bearer text, and a database URL, and asserts those values are absent from logs and returned failure messages.

### Validation Results

| Check | Status |
|-------|--------|
| Lint | PASS: `uv run ruff check .` |
| Format | PASS: `uv run ruff format --check .` |
| Type Check | PASS: `uv run mypy .` |
| Tests | PASS: `uv run pytest` (`127 passed`) |
| Frontend | SKIPPED: no `package.json` is present and the issue #10 scope is backend/docs only |

### Fix Validation Results

| Check | Status |
|-------|--------|
| Lint | PASS: `uv run ruff check .` |
| Format | PASS: `uv run ruff format --check .` |
| Type Check | PASS: `uv run mypy .` |
| Tests | PASS: `uv run pytest` (`127 passed`) |
| Frontend | SKIPPED: no `package.json` is present and the issue #10 scope is backend/docs only |

---

## Final Review: Current Unstaged Changes

**Scope**: Full current unstaged worktree for GitHub issue #10
**Recommendation**: APPROVE

### Issues Found

#### Critical

None.

#### High Priority

None.

#### Medium Priority

None.

#### Suggestions

None.

### Validation Results

| Check | Status |
|-------|--------|
| Lint | PASS: `uv run ruff check .` |
| Format | PASS: `uv run ruff format --check .` |
| Type Check | PASS: `uv run mypy .` |
| Tests | PASS: `uv run pytest` (`127 passed`) |
| Frontend | SKIPPED: no `package.json` is present and the issue #10 scope is backend/docs only |

### Summary

The current unstaged issue #10 work satisfies the story acceptance criteria: indicator snapshot models store versioned calculation metadata and indicator payloads, the refresh service recomputes snapshots from cached candles without provider calls, repository tests cover creation/latest/versioned/incomplete persistence paths, and refresh failure logs keep ticker/provider/calculation context without secret-bearing exception messages. No remaining review blockers were found.

# Code Review: Issue #11

**Scope**: Issue #11 unstaged changes
**Recommendation**: NEEDS WORK

## Summary

Reviewed the new setup scoring contracts in `app/scoring`, the scoring schema tests, the scoring methodology update, and the issue #11 plan/report artifacts. The implementation is well-scoped and passes backend validation, but the scoring input contract currently allows mismatched indicator snapshots to be bundled under a different ticker/provider.

## Issues Found

### Critical

None.

### High Priority

None.

### Medium Priority

1. `app/scoring/models.py:84` - `SetupScoringInput` does not validate that its indicator snapshots match the input `symbol` and `provider`.
   - Error: A caller can construct `SetupScoringInput(symbol="AAPL", provider="massive", ...)` while passing a `technical_snapshot`, `support_resistance_snapshot`, or `relative_strength_snapshot` for a different symbol or provider.
   - Likely cause: The model validates its own metadata fields, but has no `model_validator` for cross-snapshot consistency.
   - Fix: Add an `after` model validator that compares each snapshot's non-`None` `symbol` and `provider` against the normalized input values, and add a regression test that mismatched snapshot metadata raises `ValidationError`.

### Suggestions

1. `app/scoring/models.py:273` - If the intended contract is that omitted holding windows default to 3 to 20 trading days, make `SetupTradePlan.expected_holding_window` use `Field(default_factory=ExpectedHoldingWindow)` and test that omission applies the default. If explicit emission is preferred, the current required field is fine.

## Validation Results

| Check | Status |
|-------|--------|
| Lint | PASS: `uv run ruff check .` |
| Formatting | PASS: `uv run ruff format --check .` |
| Type Check | PASS: `uv run mypy .` |
| Tests | PASS: `uv run pytest` (147 passed) |
| Frontend | SKIPPED: no `package.json` / frontend scaffold exists yet |

## What's Good

The new models follow the repository's frozen Pydantic contract pattern, reuse existing symbol/text normalization helpers, and keep scoring contracts separate from persistence/API DTOs. The tests directly cover the issue acceptance criteria for version defaults, trade-plan completeness, wait-state outputs, level shape validation, and required failure-case data.

## Recommendation

Add the cross-snapshot consistency validator before closing issue #11. After that change, rerun the same backend validation suite.

---

# Code Review: Issue #11 Follow-up

**Scope**: Issue #11 current unstaged changes after medium-priority fix and holding-window default update
**Recommendation**: APPROVE

## Summary

Reviewed the current unstaged issue #11 changes, including the new scoring contracts, scoring tests, scoring methodology update, and issue artifacts. The previously reported snapshot consistency issue is fixed, the holding-window default now matches the product decision, and backend validation is passing.

## Issues Found

### Critical

None.

### High Priority

None.

### Medium Priority

None.

### Suggestions

1. `.agents/reports/story-011-setup-scoring-schemas-version-contracts-report.md` still says `uv run pytest` passed with 147 tests and does not mention the new mismatch/default-window tests. Refreshing that report before final handoff would make the artifact match the current 154-test state, but this is non-blocking.

## Validation Results

| Check | Status |
|-------|--------|
| Lint | PASS: `uv run ruff check .` |
| Formatting | PASS: `uv run ruff format --check .` |
| Type Check | PASS: `uv run mypy .` |
| Tests | PASS: `uv run pytest` (154 passed) |
| Frontend | SKIPPED: no `package.json` / frontend scaffold exists yet |

## What's Good

`SetupScoringInput` now rejects symbol/provider mismatches across the bundled indicator snapshots, which protects future scoring from mixing ticker or provider bases. `SetupTradePlan` now safely defaults omitted holding windows to `3 to 20 trading days`, and tests cover both the validator behavior and the default.

## Recommendation

No blocking issues found. The current issue #11 implementation is ready to proceed, with only the optional report refresh noted above.

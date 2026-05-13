# Code Review: Issue #8 Unstaged Changes

**Scope**: Unstaged and untracked changes for issue #8, "STORY-008: Compute Core Technical Indicators"
**Recommendation**: APPROVE

## Summary

Reviewed the new provider-neutral indicator package, indicator tests, scoring methodology
documentation, and local AI-layer plan/report artifacts for issue #8. The implementation
matches the story intent: deterministic SMA, RSI, MACD, ATR, and relative-volume snapshots
from normalized `DailyCandle` inputs, with explicit incomplete-data states and no provider
payload coupling.

## Issues Found

### Critical

None.

### High Priority

None.

### Medium Priority

None.

### Suggestions

1. `.agents/reports/story-008-core-technical-indicators-report.md:3` points to
   `.agents/plans/story-008-core-technical-indicators.plan.md`, but the plan currently
   lives at `.agents/plans/completed/story-008-core-technical-indicators.plan.md`.
   Updating the path would make the artifact trail easier to follow.
2. `tests/indicators/test_technical.py` covers ATR with a simple hand-checkable series and
   a volatile smoke assertion. A future tightening pass could add a dedicated gapped OHLC
   fixture to lock the first true-range seed and gap branches independently.

## Validation Results

| Check | Status |
|-------|--------|
| Type Check | PASS: `uv run mypy .` |
| Lint | PASS: `uv run ruff check .` |
| Format | PASS: `uv run ruff format --check .` |
| Tests | PASS: `uv run pytest` |
| Frontend | SKIPPED: no `package.json` or frontend scaffold present |

## What's Good

- Indicator code consumes only normalized `DailyCandle` contracts and keeps provider
  response shapes out of the indicator layer.
- Warm-up values remain `None`, public snapshots reject `NaN`/`inf`, and latest missing
  indicators produce explicit incomplete details.
- Relative volume excludes the current session from its baseline, which protects scoring
  from same-candle volume leakage.
- Tests cover no-candle snapshots, default 200-candle completeness, flat and volatile
  series, RSI smoothing, MACD convention, relative-volume anti-leakage, zero-volume
  baselines, sorting/no mutation, invalid mixed candle bases, and missing volume contract
  behavior.
- Documentation now records the implemented formulas, warm-up rules, anti-leakage policy,
  and provider-indicator boundary.

## Recommendation

Approve. No blocking changes are needed before opening a PR.

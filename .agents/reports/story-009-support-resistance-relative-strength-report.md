# Implementation Report: STORY-009 Support, Resistance, and Relative Strength Signals

**Plan**: `.agents/plans/story-009-support-resistance-relative-strength.plan.md`
**Branch**: `feature-9-support-resistance-relative-strength`
**GitHub Issue**: #9, https://github.com/DaDanielL/NookScout/issues/9
**Status**: COMPLETE

## Summary

Implemented provider-neutral support/resistance and benchmark-relative strength signals
from normalized `DailyCandle` inputs. The new signal layer is deterministic, does not
fetch provider data directly, returns explicit incomplete states, distinguishes missing
benchmark data from underperformance, and documents the MVP methodology and deferrals.

## Tasks Completed

| # | Task | File | Status |
|---|------|------|--------|
| 1 | Add signal models and config validation | `app/indicators/signals.py` | Done |
| 2 | Implement shared candle preparation helpers | `app/indicators/signals.py` | Done |
| 3 | Implement support/resistance calculation | `app/indicators/signals.py` | Done |
| 4 | Implement relative strength calculation | `app/indicators/signals.py` | Done |
| 5 | Export new signal API | `app/indicators/__init__.py` | Done |
| 6 | Add signal fixture tests | `tests/indicators/test_signals.py` | Done |
| 7 | Document methodology and deferrals | `docs/scoring-methodology.md` | Done |
| 8 | Run full backend validation | N/A | Done |

## Validation Results

| Check | Result |
|-------|--------|
| Lint | Pass: `uv run ruff check .` |
| Format | Pass: `uv run ruff format --check .` |
| Type check | Pass: `uv run mypy .` |
| Tests | Pass: `uv run pytest` (`119 passed`) |
| Focused tests | Pass: `uv run pytest tests/indicators/test_signals.py` (`20 passed`) |
| E2E / Smoke | Pass: signal fixture smoke and doc deferral check |

## Files Changed

| File | Action | Notes |
|------|--------|-------|
| `app/indicators/signals.py` | CREATE | Added signal configs, enums, snapshots, support/resistance calculation, relative-strength calculation, validation helpers, and finite-float guards. |
| `app/indicators/__init__.py` | UPDATE | Exported new signal contracts and calculation functions. |
| `tests/indicators/test_signals.py` | CREATE | Added deterministic fixtures for support/resistance states, relative strength labels, incomplete benchmark states, sorting, and invalid candle basis. |
| `docs/scoring-methodology.md` | UPDATE | Documented support/resistance defaults, pivot/zone rules, relative-strength defaults, incomplete behavior, tuning policy, and sector-relative-strength deferral. |

## Tests Written

| Test File | Test Cases |
|-----------|------------|
| `tests/indicators/test_signals.py` | Breakout, pullback-near-support, failed-resistance, no candles, insufficient history, no swing levels, flat non-pivot data, input sorting, invalid support/resistance basis, SPY/QQQ outperformance, underperformance, sparse matched-date benchmark comparisons, missing benchmark data, insufficient benchmark history, no overlapping dates, and invalid relative-strength basis. |

## Deviations from Plan

- Used branch `feature-9-support-resistance-relative-strength` instead of
  `feature/story-009-support-resistance-relative-strength` because the slash-style branch
  could not be created in the local Git ref layout. This also matches the branch naming
  convention in `AGENTS.md`.
- The support/resistance snapshot `required_candles` records the minimum pivot-confirming
  history, `pivot_left + pivot_right + 1`, while `lookback_period` caps the recent window
  used for eligible pivots. This keeps shorter-but-valid fixtures and early local data
  usable without pretending a full 60-session lookback is mandatory.

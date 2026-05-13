# Implementation Report: STORY-008 Core Technical Indicators

**Plan**: `.agents/plans/story-008-core-technical-indicators.plan.md`
**Branch**: `feature-008-core-technical-indicators`
**GitHub Issue**: #8, https://github.com/DaDanielL/NookScout/issues/8
**Status**: COMPLETE

## Summary

Implemented a provider-neutral `app/indicators` package that calculates deterministic
SMA, RSI, MACD, relative volume, and ATR snapshots from normalized `DailyCandle` inputs.
The implementation sorts inputs by session date, rejects mixed candle bases, preserves
warm-up gaps as `None`, reports latest incomplete details, and avoids provider, API,
persistence, migration, or frontend changes.

## Tasks Completed

| # | Task | File | Status |
|---|------|------|--------|
| 1 | Add indicator package exports | `app/indicators/__init__.py` | Done |
| 2 | Add typed indicator contracts | `app/indicators/technical.py` | Done |
| 3 | Implement input preparation | `app/indicators/technical.py` | Done |
| 4 | Implement leak-free calculations | `app/indicators/technical.py` | Done |
| 5 | Build snapshot output and incomplete details | `app/indicators/technical.py` | Done |
| 6 | Add indicator fixture tests | `tests/indicators/test_technical.py` | Done |
| 7 | Document implemented methodology | `docs/scoring-methodology.md` | Done |

## Validation Results

| Check | Result |
|-------|--------|
| Focused indicator tests | Pass: `uv run pytest tests/indicators/test_technical.py` |
| Type check | Pass: `uv run mypy .` |
| Lint | Pass: `uv run ruff check .` |
| Format check | Pass: `uv run ruff format --check .` |
| Tests | Pass: `uv run pytest` |
| Docs smoke | Pass: `rg -n "SMA\|RSI\|MACD\|ATR\|relative volume\|warm-up\|leak" docs/scoring-methodology.md` |
| E2E / Smoke | Pass: fixture tests call `calculate_technical_indicators(...)`, confirm default 200-candle completeness, no public `NaN`/`inf`, and formula docs alignment |

## Files Changed

| File | Action | Notes |
|------|--------|-------|
| `app/indicators/__init__.py` | CREATE | Public exports for indicator contracts and calculation entrypoint |
| `app/indicators/technical.py` | CREATE | Indicator config/models, input validation, SMA, RSI, MACD, relative volume, ATR, snapshot assembly |
| `tests/indicators/__init__.py` | CREATE | Indicator test package marker |
| `tests/indicators/test_technical.py` | CREATE | Formula, warm-up, anti-leakage, invalid-input, and missing-data coverage |
| `docs/scoring-methodology.md` | UPDATE | Replaced future indicator text with implemented methodology |

## Tests Written

| Test File | Test Cases |
|-----------|------------|
| `tests/indicators/test_technical.py` | No-candle incomplete snapshot; hand-checkable SMA/MACD/relative volume/ATR; Wilder RSI; tiny RSI movement boundary; relative-volume anti-leakage; zero-volume baseline; default 200-candle warm-up; flat series; volatile series; input sorting/no mutation; mixed symbol/provider/adjusted, duplicate sessions/timestamps; non-`DailyCandle` rejection; missing volume contract rejection |

## Deviations from Plan

- Used a module-level frozen default `IndicatorConfig` singleton for
  `calculate_technical_indicators(...)` instead of calling `IndicatorConfig()` directly
  in the default argument. This preserves behavior and satisfies Ruff B008.
- Created branch `feature-008-core-technical-indicators` instead of a slash-style
  `feature/...` branch because the local git ref layout rejected slash-style branch
  creation.

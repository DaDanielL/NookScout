# Implementation Report: Setup Scoring Schemas and Version Contracts

**Plan**: `.agents/plans/story-011-setup-scoring-schemas-version-contracts.plan.md`
**Branch**: `feature-11-setup-scoring-schemas`
**GitHub Issue**: #11, https://github.com/DaDanielL/NookScout/issues/11
**Status**: COMPLETE

## Summary

Implemented the first scoring-domain contract package with frozen Pydantic models for
setup scoring inputs, setup ideas, setup levels, trade plans, risk/reward estimates,
expected holding windows, confidence factors, signal explanations, failure conditions,
and setup/version enums. Added focused schema tests and documented the contract in the
scoring methodology. Follow-up review fixes added snapshot metadata mismatch validation
and a default 3 to 20 trading day holding window for trade plans.

## Tasks Completed

| # | Task | File | Status |
|---|------|------|--------|
| 1 | Create scoring package shell | `app/scoring/__init__.py` | Done |
| 2 | Define version constants and enums | `app/scoring/models.py` | Done |
| 3 | Define scoring input and helper models | `app/scoring/models.py` | Done |
| 4 | Define trade plan and setup idea validators | `app/scoring/models.py` | Done |
| 5 | Add focused scoring schema tests | `tests/scoring/test_models.py` | Done |
| 6 | Update scoring methodology docs | `docs/scoring-methodology.md` | Done |
| 7 | Run full backend validation | N/A | Done |

## Validation Results

| Check | Result |
|-------|--------|
| Type check | Pass: `uv run mypy .` |
| Lint | Pass: `uv run ruff check .` |
| Formatting | Pass: `uv run ruff format --check .` |
| Tests | Pass: `uv run pytest` (154 passed) |
| E2E / Smoke | Pass: scoring schema tests construct valid bullish/no-clear/wait outputs, reject incomplete trade-plan outputs, reject mismatched scoring snapshot metadata, and apply the default holding window when omitted |

## Files Changed

| File | Action | Notes |
|------|--------|-------|
| `app/scoring/__init__.py` | CREATE | Exports scoring contracts and version constants. |
| `app/scoring/models.py` | CREATE | Adds setup scoring schemas, enums, constants, validators, and trade-plan completeness rules. |
| `tests/scoring/__init__.py` | CREATE | Marks scoring tests as a package. |
| `tests/scoring/test_models.py` | CREATE | Adds schema normalization and validation tests. |
| `docs/scoring-methodology.md` | UPDATE | Documents STORY-011 contracts and version fields while keeping scoring logic deferred. |

## Tests Written

| Test File | Test Cases |
|-----------|------------|
| `tests/scoring/test_models.py` | Scoring input normalization, snapshot symbol/provider mismatch rejection, bullish setup version defaults, default 3 to 20 trading day holding window when omitted, no-clear and avoid/wait outputs, missing trade-plan rejection, missing/incorrect entry/stop/target/failure-case rejection, non-trade trade-plan rejection, reason text requirement, invalid level zones, invalid holding windows. |

## Deviations from Plan

- Branch name uses the repository convention `feature-11-setup-scoring-schemas` because the slash-style `feature/11-...` branch could not be created in the existing Git refs layout.
- The local Python 3.12 runtime backing `.venv` was missing standard-library `encodings`, so validation could not run. Reinstalled uv-managed Python 3.12, recreated `.venv`, and re-ran validation successfully.

# Plan: Indicator Ownership Strategy

## Summary

Document the MVP indicator ownership decision for NookScout: deterministic in-app code owns technical indicator calculations from normalized market-data contracts, while provider-precomputed indicators are reference-only and cannot drive scoring unless a future PRD explicitly changes that policy. The implementation should expand `docs/scoring-methodology.md` into the canonical decision record for moving averages, RSI, MACD, ATR, relative volume, support/resistance, and relative strength, then update provider documentation so it no longer says STORY-007 is pending. No production indicator code, migrations, API changes, or frontend work are part of this spike.

## User Story

As a developer, I want to decide whether NookScout computes indicators internally or uses provider indicators as a fallback, so that setup scoring remains deterministic and reproducible.

## Metadata

| Field | Value |
|-------|-------|
| Type | SPIKE |
| Complexity | LOW |
| Systems Affected | Documentation, scoring methodology, provider constraints, future indicator/testing guidance |
| GitHub Issue | #7, https://github.com/DaDanielL/NookScout/issues/7 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-007` |
| Current Branch | `main` |
| Working Tree | Clean at planning time |

---

## Patterns to Follow

### Naming

```text
SOURCE: AGENTS.md:181
Use clear domain names such as IndicatorSnapshot, SetupRun, SetupIdea, and SetupScore.
Documentation should use the same product vocabulary: indicator calculations,
indicator snapshots, setup scoring, scoring versions, and calculation versions.
```

```text
SOURCE: .agents/stories/nookscout-technical-setup-discovery.stories.md:278
Story IDs use the `STORY-###` format. Refer to this decision as STORY-007 and keep
follow-up references to STORY-008, STORY-009, and STORY-010 where useful.
```

### Documentation

```text
SOURCE: docs/scoring-methodology.md:5
This file is the canonical MVP reference for rules that determine which tickers and
future setup ideas NookScout surfaces or suppresses. Put the recommendation-impacting
indicator decision here.
```

```text
SOURCE: docs/scoring-methodology.md:103
The current "Future Indicator Methodology" section is only a placeholder. Replace or
expand it with the STORY-007 decision, explicit signal-by-signal coverage, provider
fallback policy, and follow-up implementation notes.
```

```text
SOURCE: README.md:60
README already points readers to scoring-methodology.md for recommendation-impacting
rules. Keep the indicator ownership decision in that document rather than scattering
it into README.
```

### Market Data Boundary

```text
SOURCE: AGENTS.md:101
Market data providers fetch quotes, daily candles, reference data, and liquidity inputs.
Indicator/scoring logic should not call providers directly.
```

```text
SOURCE: app/market_data/base.py:35
MarketDataProvider is the adapter boundary and returns normalized contracts only.
The decision should reinforce that future indicator code consumes normalized candles
and cached benchmark data, not provider-specific JSON or provider indicator endpoints.
```

```text
SOURCE: app/market_data/schemas.py:149
DailyCandle is the normalized OHLCV contract with adjusted flag, provider metadata,
data recency, and timezone-aware session data. It is the natural source for moving
average, RSI, MACD, ATR, relative volume, support/resistance, and relative-strength
inputs.
```

### Indicator and Scoring Policy

```text
SOURCE: AGENTS.md:209
Deterministic code owns prices, indicators, setup levels, risk/reward, classification,
confidence factors, and failure conditions. This should be the headline decision.
```

```text
SOURCE: .agents/PRDs/nookscout-technical-setup-discovery.prd.md:32
MVP technical setup scoring must evaluate trend, 20/50/200 moving averages,
support/resistance, RSI, MACD, volume/relative volume, ATR volatility, and relative
strength vs SPY/QQQ.
```

```text
SOURCE: .agents/PRDs/nookscout-technical-setup-discovery.prd.md:85
Future persisted setup data should include setup inputs, indicator values, setup type,
generated rationale, confidence factors, chart levels, scoring version, and user
interactions. Use this to justify calculation/scoring versioning from the first
indicator implementation.
```

### Provider Documentation

```text
SOURCE: docs/market-data-providers.md:52
Provider-Supplied Indicators currently says provider indicators are not approved before
STORY-007. Update this wording after the decision so it states provider indicator
endpoints remain reference-only for MVP scoring unless a future PRD changes the policy.
```

```text
SOURCE: docs/market-data-providers.md:79
Provider tests should use mocked provider responses and fixtures, not live provider
calls. The indicator testing guidance should mirror that fixture-based approach.
```

### Tests

```text
SOURCE: AGENTS.md:237
Future unit tests should cover indicators and support/resistance helpers. This spike
does not implement those tests, but the doc must specify the fixture and tolerance
expectations for the later implementation stories.
```

```text
SOURCE: tests/market_data/test_schemas.py:21
Existing tests use small payload factories with overrides for deterministic cases.
Recommend the same style for future indicator fixtures: known candle series plus
focused variants for insufficient history, flat series, volatile series, and missing
volume.
```

```text
SOURCE: tests/market_data/test_liquidity.py:116
Tests assert exact Decimal-derived values where formulas are deterministic. The
indicator guidance should distinguish exact values from approximate float tolerances.
```

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `docs/scoring-methodology.md` | UPDATE | Record the MVP indicator ownership decision, signal coverage, provider indicator policy, fixture guidance, numerical tolerance expectations, and versioning notes. |
| `docs/market-data-providers.md` | UPDATE | Replace pending STORY-007 language with the finalized provider-indicator policy and cross-reference scoring methodology. |

No app modules, migrations, API schemas, jobs, frontend files, or dependency files should change for this spike.

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: Mark STORY-007 Decision Status

- **File**: `docs/scoring-methodology.md`
- **Action**: UPDATE
- **Implement**:
  - Update `Last updated` to the implementation date.
  - Add STORY-007 to the implementation status section.
  - Make clear that technical indicator calculations are still not implemented, but the ownership decision is now decided.
  - Keep existing STORY-005 liquidity content intact.
- **Mirror**: `docs/scoring-methodology.md:10` - current implementation status structure.
- **Validate**: `uv run ruff format --check .`

### Task 2: Document the MVP Ownership Decision

- **File**: `docs/scoring-methodology.md`
- **Action**: UPDATE
- **Implement**:
  - Replace the placeholder `Future Indicator Methodology` section with an `MVP Indicator Ownership Decision` section.
  - State the decision plainly: NookScout computes MVP indicators internally from normalized/cached OHLCV data using pandas/NumPy; provider-precomputed indicators are not the scoring source of truth.
  - Explain why: deterministic scoring, provider portability, reproducibility, fixture regression testing, old-output interpretability, and avoidance of hidden provider formula differences.
  - State that provider indicators may be used only for manual reference/comparison or future fallback behavior approved by PRD update; if ever used, responses must be normalized, labeled, versioned, and never mixed silently with internal calculations.
- **Mirror**: `AGENTS.md:209` - deterministic code owns prices, indicators, setup levels, and scoring behavior.
- **Validate**: `uv run ruff format --check .`

### Task 3: Add Signal-by-Signal Coverage

- **File**: `docs/scoring-methodology.md`
- **Action**: UPDATE
- **Implement**:
  - Add a compact table covering each required signal:
    - Moving averages: internally calculate 20/50/200-day moving averages from adjusted daily close.
    - RSI: internally calculate RSI from adjusted daily close; document the intended smoothing method so STORY-008 can test it consistently.
    - MACD: internally calculate MACD from adjusted daily close; document standard period defaults intended for MVP.
    - ATR: internally calculate ATR from normalized daily high/low/close; document standard period defaults intended for MVP.
    - Relative volume: internally calculate recent volume versus a configurable historical average from normalized daily volume.
    - Support/resistance: internally derive deterministic levels from normalized daily candles; provider levels must not be consumed as setup levels.
    - Relative strength: internally compare normalized ticker performance against cached benchmark candles for SPY and QQQ unless a later story changes benchmark scope.
  - For each row, include owner, primary inputs, MVP provider-indicator policy, and implementation-story notes.
- **Mirror**: `.agents/PRDs/nookscout-technical-setup-discovery.prd.md:32` - required technical signals.
- **Validate**: `uv run ruff format --check .`

### Task 4: Add Fixture and Numerical Tolerance Guidance

- **File**: `docs/scoring-methodology.md`
- **Action**: UPDATE
- **Implement**:
  - Add follow-up implementation notes for STORY-008 and STORY-009.
  - Required fixtures should include:
    - Known adjusted daily OHLCV series with enough history for 20/50/200 MA, RSI, MACD, ATR, and relative volume.
    - Insufficient-history series that produce explicit incomplete-data states.
    - Flat price series.
    - Volatile gap/large-range series for ATR behavior.
    - Missing or zero-volume cases for relative volume behavior.
    - Benchmark comparison series for SPY and QQQ.
    - Provider-reference comparison fixtures if provider indicators are used for non-scoring comparison.
  - State expected test tolerance policy:
    - Exact assertions for metadata, incomplete-data states, windows, counts, labels, and version strings.
    - Approximate tolerances for float indicators, preferably `pytest.approx` with documented absolute/relative tolerance per indicator family.
    - Decimal or rounded display values should be tested at the API/display boundary, not inside raw calculation internals unless those internals deliberately use Decimal.
  - Add versioning guidance: future persisted indicator snapshots should record calculation version, input candle range, adjusted/unadjusted status, benchmark symbols, and scoring version linkage.
- **Mirror**: `tests/market_data/test_schemas.py:21` - deterministic fixture helpers with focused overrides.
- **Validate**: `uv run ruff format --check .`

### Task 5: Update Provider Indicator Notes

- **File**: `docs/market-data-providers.md`
- **Action**: UPDATE
- **Implement**:
  - Update the `Provider-Supplied Indicators` section so it no longer says ownership is deferred to STORY-007.
  - State that STORY-007 decided internal calculations are the MVP source of truth.
  - Keep Massive/Twelve Data provider indicators documented as available provider context only.
  - Cross-reference `docs/scoring-methodology.md` for formula ownership, fallback/reference policy, fixtures, tolerances, and versioning.
- **Mirror**: `docs/market-data-providers.md:52` - existing provider-supplied indicator section.
- **Validate**: `uv run ruff format --check .`

### Task 6: Final Review and Validation

- **File**: `docs/scoring-methodology.md`, `docs/market-data-providers.md`
- **Action**: UPDATE
- **Implement**:
  - Search for stale language such as "before STORY-007" and "later story explicitly approves" where the new decision should supersede it.
  - Confirm all issue acceptance criteria are directly traceable in the docs.
  - Confirm the docs do not imply buy/sell instructions, guaranteed outcomes, real-time precision, or personalized financial advice.
  - Confirm no production code or dependencies changed.
- **Mirror**: `AGENTS.md:304` - keep financial language educational and non-personalized.
- **Validate**:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run mypy .`
  - `uv run pytest`

---

## Validation

Run the backend validation commands from `AGENTS.md`. There is no frontend scaffold in this repo yet, so frontend commands are not applicable to this docs-only spike.

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

For this docs-only spike, no new tests are expected. The implementation should still run the backend checks to catch accidental code/config drift.

## End-to-End Verification

- [ ] `docs/scoring-methodology.md` explicitly states internal deterministic calculation is the MVP source of truth.
- [ ] `docs/scoring-methodology.md` explicitly covers moving averages, RSI, MACD, ATR, relative volume, support/resistance, and relative strength.
- [ ] Provider indicator use is limited to manual reference/comparison or future PRD-approved fallback behavior.
- [ ] Fixture and numerical tolerance notes are specific enough to guide STORY-008 and STORY-009 implementation.
- [ ] `docs/market-data-providers.md` no longer treats STORY-007 as undecided.
- [ ] Documentation language remains educational and non-personalized.

## Acceptance Criteria

- [ ] All planned tasks completed.
- [ ] Relevant tests added or updated, or documented as not applicable because this spike is docs-only.
- [ ] Validation commands pass.
- [ ] End-to-end verification passes.
- [ ] Implementation follows `AGENTS.md`.
- [ ] GitHub issue #7 acceptance criteria are fully covered.

# Plan: STORY-009 Support, Resistance, and Relative Strength Signals

## Summary

Add a provider-neutral indicator signal module that derives simple support/resistance
zones and benchmark-relative strength from normalized `DailyCandle` inputs. The
implementation should remain pure and deterministic: callers provide ticker candles and
benchmark candles fetched or cached through the existing market-data layer, while the
indicator layer validates inputs, returns typed signal snapshots, and distinguishes
incomplete benchmark data from underperformance. Update scoring methodology docs with
the chosen parameters and add fixture tests for breakout, pullback-near-support,
failed-resistance, outperforming-benchmark, and underperforming-benchmark scenarios.

## User Story

As a developer, I want support/resistance and benchmark-relative strength signals, so
that setup scoring can reason about key chart levels and stock strength versus broad
market benchmarks.

## Metadata

| Field | Value |
|-------|-------|
| Type | NEW_CAPABILITY |
| Complexity | MEDIUM |
| Systems Affected | Backend indicator layer, scoring methodology docs, backend tests |
| GitHub Issue | #9, https://github.com/DaDanielL/NookScout/issues/9 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-009` |

---

## Patterns to Follow

### Naming

```text
SOURCE: app/indicators/technical.py:19
Indicator contracts use explicit domain names such as IndicatorConfig,
IndicatorIncompleteReason, IndicatorIncompleteDetail, IndicatorPoint, and
TechnicalIndicatorSnapshot. Mirror this style with names like
SupportResistanceConfig, PriceLevelZone, SupportResistanceSnapshot,
RelativeStrengthConfig, BenchmarkRelativeStrength, and RelativeStrengthSnapshot.
```

### Provider-Neutral Contracts

```text
SOURCE: app/market_data/schemas.py:44
MarketDataModel is a frozen Pydantic base used for normalized market-data/domain
contracts. New signal config, point, zone, comparison, and snapshot models should inherit
from it.
```

```text
SOURCE: app/market_data/schemas.py:149
DailyCandle is the normalized daily OHLCV contract. Signal calculations should consume
DailyCandle objects only and must not know Massive/Polygon or other provider payload
shapes.
```

### Integration Boundary

```text
SOURCE: app/market_data/base.py:35
MarketDataProvider exposes get_daily_candles(symbol, start_date, end_date). Benchmark
candles for SPY/QQQ should reach the signal function through this provider-neutral
boundary, or through cached DailyCandleRepository reads, not direct provider calls from
the indicator module.
```

```text
SOURCE: app/persistence/repositories.py:137
DailyCandleRepository.get_range returns ordered DailyCandle contracts and defaults to
adjusted=True. Relative-strength callers can use this repository once benchmark candles
are cached; this story should not add persistence or migrations.
```

### Deterministic Pure Functions

```text
SOURCE: app/market_data/liquidity.py:138
Existing backend domain calculations expose deterministic functions that accept typed
inputs and return typed domain results. Mirror this with calculate_support_resistance(...)
and calculate_relative_strength(...).
```

### Error Handling And Incomplete Data

```text
SOURCE: app/indicators/technical.py:294
No-candle input returns an explicit incomplete snapshot instead of fabricating values.
Use the same pattern for support/resistance and relative strength.
```

```text
SOURCE: app/indicators/technical.py:500
Unavailable latest indicator values produce IndicatorIncompleteDetail records. New
signal code should expose its own typed incomplete details, including benchmark-specific
missing/insufficient data reasons.
```

```text
SOURCE: app/indicators/technical.py:610
Public numeric values are sanitized so NaN/inf do not escape. Reuse or mirror the
finite-float guard pattern for level prices, returns, and excess returns.
```

### Tests

```text
SOURCE: tests/indicators/test_technical.py:64
Indicator tests use compact candle fixture builders and deterministic sequential
session dates. Create equivalent signal fixtures, with symbol/provider overrides for
benchmark series.
```

```text
SOURCE: tests/indicators/test_technical.py:119
Formula tests assert metadata exactly and numeric outputs with pytest.approx. Follow
this style for level boundaries, return percentages, and excess returns.
```

```text
SOURCE: tests/indicators/test_technical.py:308
Invalid candle-basis tests raise ValueError for mixed symbols/providers/adjustment basis.
New signal tests should cover the same validation expectations for ticker and benchmark
candle inputs.
```

---

## Proposed Signal Contracts

### Support And Resistance

Implement in a new `app/indicators/signals.py` module.

- `SupportResistanceConfig`
  - `lookback_period: int = 60`
  - `pivot_left: int = 2`
  - `pivot_right: int = 2`
  - `zone_percent: float = 0.01`
  - `proximity_percent: float = 0.03`
  - `breakout_buffer_percent: float = 0.005`
  - `max_levels: int = 3`
  - Validate positive periods/counts and non-negative percentage values.
- `PriceLevelKind`
  - `SUPPORT = "support"`
  - `RESISTANCE = "resistance"`
- `SupportResistanceState`
  - `BREAKOUT = "breakout"`
  - `PULLBACK_NEAR_SUPPORT = "pullback_near_support"`
  - `FAILED_RESISTANCE = "failed_resistance"`
  - `BETWEEN_LEVELS = "between_levels"`
  - `NO_CLEAR_LEVEL = "no_clear_level"`
  - `INCOMPLETE = "incomplete"`
- `PriceLevelZone`
  - `kind`, `price`, `zone_low`, `zone_high`, `touch_count`, `last_touched_session_date`
  - Optional `distance_from_latest_close_percent` for the latest point.
- `SupportResistanceIncompleteReason`
  - `NO_CANDLES = "no_candles"`
  - `INSUFFICIENT_HISTORY = "insufficient_history"`
  - `NO_SWING_LEVELS = "no_swing_levels"`
- `SupportResistanceIncompleteDetail`
  - `signal`, `reason`, `required_candles`, `available_candles`, `message`
- `SupportResistanceSnapshot`
  - `symbol`, `provider`, `adjusted`, `data_recency`
  - `start_session_date`, `end_session_date`, `available_candles`, `required_candles`
  - `latest_close`, `latest_high`, `latest_low`
  - `support_levels`, `resistance_levels`
  - `nearest_support`, `nearest_resistance`, `broken_resistance`
  - `state`, `is_complete`, `incomplete_details`

Recommended heuristic:

- Sort and validate one-symbol, one-provider, one-adjustment-basis candles using the
  same rules as `calculate_technical_indicators`.
- Use the last `lookback_period` candles.
- A support pivot is a low that is less than or equal to lows in the `pivot_left` candles
  before it and the `pivot_right` candles after it.
- A resistance pivot is a high that is greater than or equal to highs in the
  `pivot_left` candles before it and the `pivot_right` candles after it.
- Because `pivot_right` uses later completed candles to confirm a pivot, only fully
  confirmed historical pivots are eligible; do not use future data beyond the latest
  provided candle.
- Collapse nearby pivots into simple zones using `zone_percent`; keep the most recent
  or most-touched zones first, capped by `max_levels`.
- Classify latest state conservatively:
  - `BREAKOUT` when the latest close is above a prior resistance zone high plus
    `breakout_buffer_percent`, with a `broken_resistance` populated.
  - `PULLBACK_NEAR_SUPPORT` when the latest close is above/inside the nearest support
    zone and within `proximity_percent`.
  - `FAILED_RESISTANCE` when the latest high trades into/above a resistance zone but
    latest close finishes below that zone.
  - `BETWEEN_LEVELS` when both nearest support and resistance exist but no stronger
    state applies.
  - `NO_CLEAR_LEVEL` when enough candles exist but no usable support/resistance zone is
    found.

### Relative Strength

Implement in the same `app/indicators/signals.py` module.

- `RelativeStrengthConfig`
  - `benchmark_symbols: tuple[str, ...] = ("SPY", "QQQ")`
  - `lookback_periods: tuple[int, ...] = (20,)`
  - `outperformance_threshold: float = 0.0`
  - Validate benchmark symbols through `normalize_symbol`, de-duplicate them, and require
    positive lookback periods.
- `RelativeStrengthLabel`
  - `OUTPERFORMING = "outperforming"`
  - `UNDERPERFORMING = "underperforming"`
  - `MIXED = "mixed"`
  - `INCOMPLETE = "incomplete"`
- `RelativeStrengthIncompleteReason`
  - `NO_TICKER_CANDLES = "no_ticker_candles"`
  - `INSUFFICIENT_TICKER_HISTORY = "insufficient_ticker_history"`
  - `MISSING_BENCHMARK = "missing_benchmark"`
  - `INSUFFICIENT_BENCHMARK_HISTORY = "insufficient_benchmark_history"`
  - `NO_OVERLAPPING_DATES = "no_overlapping_dates"`
  - `INVALID_START_PRICE = "invalid_start_price"`
- `RelativeStrengthIncompleteDetail`
  - `benchmark_symbol`, `lookback_period`, `reason`, `required_candles`,
    `available_candles`, `message`
- `BenchmarkRelativeStrength`
  - `benchmark_symbol`, `lookback_period`, `end_session_date`, `start_session_date`
  - `ticker_return`, `benchmark_return`, `excess_return`, `label`
  - Optional incomplete detail when a comparison cannot be calculated.
- `RelativeStrengthSnapshot`
  - `symbol`, `provider`, `adjusted`, `data_recency`
  - `start_session_date`, `end_session_date`, `available_candles`
  - `benchmark_symbols`, `lookback_periods`, `comparisons`
  - `overall_label`, `is_complete`, `incomplete_details`

Function signature:

```python
def calculate_relative_strength(
    ticker_candles: Sequence[DailyCandle],
    benchmark_candles_by_symbol: Mapping[str, Sequence[DailyCandle]],
    config: RelativeStrengthConfig = _DEFAULT_RELATIVE_STRENGTH_CONFIG,
) -> RelativeStrengthSnapshot:
    ...
```

Recommended heuristic:

- Sort and validate ticker candles with the same one-symbol/provider/adjustment-basis
  expectations as core indicators.
- Normalize benchmark symbols and accept benchmark candle mappings by symbol.
- For each configured benchmark and lookback period, align by ticker end date:
  - Use the latest ticker candle as the comparison end.
  - Find ticker and benchmark closes on the same `end_session_date`; if the benchmark
    lacks that date, return `NO_OVERLAPPING_DATES` for that comparison.
  - Use the session exactly `lookback_period` rows before the end date in the ticker
    series as the start date, then require a benchmark candle on that same start date.
  - Compute returns as `(end_close / start_close) - 1`.
  - Compute excess return as `ticker_return - benchmark_return`.
  - Label the comparison `OUTPERFORMING` when excess return is greater than
    `outperformance_threshold`; otherwise `UNDERPERFORMING`.
- Overall label:
  - `INCOMPLETE` if no comparison can be calculated.
  - `OUTPERFORMING` if all complete comparisons outperform.
  - `UNDERPERFORMING` if all complete comparisons underperform.
  - `MIXED` otherwise.
- Incomplete benchmark data must never be labeled as underperformance.

Sector-relative strength remains explicitly deferred for MVP; document that only SPY/QQQ
benchmark-relative strength is in scope for this story.

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `app/indicators/signals.py` | CREATE | Provider-neutral support/resistance and relative-strength signal contracts and calculations. |
| `app/indicators/__init__.py` | UPDATE | Export the new signal configs, enums, snapshots, and calculation functions. |
| `tests/indicators/test_signals.py` | CREATE | Fixture tests for support/resistance states, benchmark relative strength, incomplete benchmark states, and invalid inputs. |
| `docs/scoring-methodology.md` | UPDATE | Document support/resistance parameters, relative-strength default benchmarks/windows, incomplete-data behavior, and sector-relative-strength deferral. |

No dependency, settings, API route, persistence model, or migration changes are planned
for this story.

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: Add Signal Models And Config Validation

- **File**: `app/indicators/signals.py`
- **Action**: CREATE
- **Implement**: Add frozen Pydantic-style config, enum, detail, zone, comparison, and
  snapshot models described above. Use `MarketDataModel`, `StrEnum`, validators, and
  finite-float guards. Normalize benchmark symbols with `normalize_symbol`.
- **Mirror**: `app/indicators/technical.py:19` - config/model naming and validators.
- **Validate**: `uv run pytest tests/indicators`

### Task 2: Implement Shared Candle Preparation Helpers

- **File**: `app/indicators/signals.py`
- **Action**: UPDATE
- **Implement**: Add private helpers to sort and validate `DailyCandle` sequences:
  one symbol, one provider, one adjustment basis, unique session dates, no duplicate
  timestamps across different sessions, finite OHLC values. Return empty tuples for
  no-candle inputs so public functions can emit incomplete snapshots.
- **Mirror**: `app/indicators/technical.py:252` - existing `_prepare_candles` behavior.
- **Validate**: `uv run pytest tests/indicators`

### Task 3: Implement Support/Resistance Calculation

- **File**: `app/indicators/signals.py`
- **Action**: UPDATE
- **Implement**: Add `calculate_support_resistance(candles, config=...)` with no-candle,
  insufficient-history, and no-clear-level states. Detect confirmed swing highs/lows,
  cluster pivots into zones, rank/cap zones, compute nearest support/resistance,
  `broken_resistance`, and classify latest state as breakout, pullback-near-support,
  failed-resistance, between-levels, no-clear-level, or incomplete.
- **Mirror**: `app/market_data/liquidity.py:138` - deterministic pure function returns
  typed domain result.
- **Validate**: `uv run pytest tests/indicators`

### Task 4: Implement Relative Strength Calculation

- **File**: `app/indicators/signals.py`
- **Action**: UPDATE
- **Implement**: Add `calculate_relative_strength(ticker_candles,
  benchmark_candles_by_symbol, config=...)`. Default to `SPY` and `QQQ`, compare
  matched-date lookback returns, calculate excess return, label complete comparisons,
  and emit benchmark-specific incomplete details for missing/insufficient/no-overlap
  data. Ensure incomplete benchmark data is separate from underperformance.
- **Mirror**: `app/market_data/base.py:51` - benchmark data should be represented by
  provider-neutral daily candles fetched through the same market-data boundary by the
  caller.
- **Validate**: `uv run pytest tests/indicators`

### Task 5: Export New Signal API

- **File**: `app/indicators/__init__.py`
- **Action**: UPDATE
- **Implement**: Import and expose the new signal configs, enums, snapshots, and
  `calculate_support_resistance` / `calculate_relative_strength` in `__all__`.
- **Mirror**: `app/indicators/__init__.py:3` - current public export pattern.
- **Validate**: `uv run mypy app tests`

### Task 6: Add Signal Fixture Tests

- **File**: `tests/indicators/test_signals.py`
- **Action**: CREATE
- **Implement**: Add compact candle builders with symbol/provider overrides. Cover:
  breakout above prior resistance, pullback near support, failed resistance, no candles,
  insufficient history, no clear swing levels, sorted input without mutation,
  invalid mixed candle basis, outperforming benchmark, underperforming benchmark,
  missing benchmark data, insufficient benchmark history, and no overlapping benchmark
  dates. Assert incomplete benchmark data is not labeled as weak relative strength.
- **Mirror**: `tests/indicators/test_technical.py:64` - candle fixture style and
  compact deterministic series.
- **Validate**: `uv run pytest tests/indicators/test_signals.py`

### Task 7: Document Methodology And Deferrals

- **File**: `docs/scoring-methodology.md`
- **Action**: UPDATE
- **Implement**: Replace the "future work" line for support/resistance and relative
  strength with implemented methodology. Document support/resistance defaults,
  pivot/zone definitions, anti-leakage behavior, relative-strength default benchmarks
  `SPY`/`QQQ`, default lookback window(s), incomplete benchmark states, provider
  indicator policy, and explicit sector-relative-strength deferral. Add a tuning policy
  note that the initial support/resistance parameters are transparent MVP heuristics, not
  optimized trading parameters. State that STORY-009 tuning is limited to deterministic
  fixture behavior for obvious chart patterns such as breakouts, pullbacks near support,
  failed resistance, no-clear-level cases, and incomplete data. Defer broader calibration
  until after the MVP has persisted setup ideas, scoring outputs, historical outcomes,
  and/or user feedback that can support larger historical sanity checks, real-example
  scoring regression sets, outcome review, and feedback-driven adjustments.
- **Mirror**: `docs/scoring-methodology.md:114` - existing implemented indicator
  methodology structure and tone.
- **Validate**: `uv run pytest tests/indicators`

### Task 8: Run Full Backend Validation

- **File**: N/A
- **Action**: VERIFY
- **Implement**: Run backend lint, format check, type check, and tests. Fix only issues
  caused by this story.
- **Mirror**: `AGENTS.md:248` - project validation expectations.
- **Validate**: `uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest`

---

## Risks And Mitigations

| Risk | Mitigation |
|------|------------|
| Support/resistance heuristics imply precision or certainty. | Model outputs as zones, document them as heuristic levels, and use conservative labels such as `NO_CLEAR_LEVEL` when signals are weak. |
| Pivot detection accidentally looks ahead beyond available candles. | Only use completed input candles and document `pivot_right` as requiring later completed candles to confirm historical pivots. Add tests for latest-state behavior. |
| Incomplete benchmark data is confused with underperformance. | Use explicit incomplete reasons and make labels `INCOMPLETE` when no comparison can be calculated. Add regression tests. |
| Benchmark date alignment becomes ambiguous around holidays or missing sessions. | Require matching start/end session dates between ticker and benchmark; emit `NO_OVERLAPPING_DATES` instead of interpolating or forward-filling. |
| The indicator module starts fetching provider data directly. | Keep functions pure and accept `DailyCandle` benchmark mappings from callers. Document provider/repository boundaries. |
| New models bloat `technical.py`. | Create `signals.py` and export from the package, preserving the existing core-indicator module. |

---

## Validation

Run these commands before reporting implementation complete:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

Focused commands during implementation:

```bash
uv run pytest tests/indicators/test_signals.py
uv run pytest tests/indicators
```

## End-to-End Verification

- [ ] `calculate_support_resistance` returns a breakout state with a populated
  `broken_resistance` for a fixture that closes above a prior resistance zone.
- [ ] `calculate_support_resistance` returns pullback-near-support and failed-resistance
  states for deterministic candle fixtures.
- [ ] `calculate_relative_strength` returns complete `SPY`/`QQQ` comparisons with
  positive excess return for outperforming fixtures and negative excess return for
  underperforming fixtures.
- [ ] Missing or insufficient benchmark candles produce incomplete benchmark details,
  not underperforming labels.
- [ ] `docs/scoring-methodology.md` documents sector-relative strength as deferred.

## Acceptance Criteria

- [ ] Support and resistance helpers identify recent swing levels or zones from daily
  candle data with documented parameters.
- [ ] Relative strength is computed versus SPY and QQQ by default.
- [ ] Sector-relative-strength open question is explicitly deferred in methodology docs.
- [ ] Outputs identify incomplete benchmark data separately from weak relative strength.
- [ ] Fixture tests cover breakout, pullback-near-support, failed-resistance,
  outperforming-benchmark, and underperforming-benchmark scenarios.
- [ ] Relevant tests added or updated.
- [ ] Validation commands pass.
- [ ] Implementation follows `AGENTS.md`.

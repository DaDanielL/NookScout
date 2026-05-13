# Plan: STORY-008 Core Technical Indicators

## Summary

Add a deterministic `app/indicators` package that computes core technical indicators
from normalized `DailyCandle` inputs. The implementation must be leak-free,
warm-up-aware, and explicit about missing data: no provider payloads, partial warm-up
values, `NaN`, `inf`, forward-fill, backfill, zero-fill, clipping, or fabricated
defaults should leave the module.

The first implementation returns a compact recent-window snapshot for scoring and
explanation. It does not add API routes, persistence models, migrations, provider calls,
or frontend behavior.

## User Story

As a developer, I want deterministic core indicator calculations, so that setup scoring
can evaluate trend, momentum, volume, and volatility consistently.

## Metadata

| Field | Value |
|-------|-------|
| Type | NEW_CAPABILITY |
| Complexity | MEDIUM |
| Systems Affected | Backend indicator layer, scoring methodology docs, backend tests |
| GitHub Issue | #8, https://github.com/DaDanielL/NookScout/issues/8 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-008` |

---

## Patterns to Follow

### Domain Models

```text
SOURCE: app/market_data/schemas.py:44
Existing market-data contracts use frozen Pydantic models through MarketDataModel.
Mirror this for indicator configuration, values, snapshots, and incomplete details.
```

### Provider-Neutral Inputs

```text
SOURCE: app/market_data/schemas.py:149
DailyCandle is the normalized input contract for daily OHLCV candles. Indicator code
must consume DailyCandle objects only and must not know Massive or provider payload
shapes.
```

### Deterministic Pure Functions

```text
SOURCE: app/market_data/liquidity.py:138
Existing backend domain calculations expose deterministic functions that return typed
domain results. Mirror this with calculate_technical_indicators(...).
```

### Cached Candle Shape

```text
SOURCE: app/persistence/repositories.py:137
DailyCandleRepository.get_range returns ordered DailyCandle contracts and defaults to
adjusted=True. Indicator code should treat mixed adjusted/unadjusted candles as invalid.
```

### Tests

```text
SOURCE: tests/market_data/test_liquidity.py:140
Existing tests use compact local fixture builders and direct assertions. Indicator tests
should use the same style with independent expected values and pytest.approx tolerances.
```

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `app/indicators/__init__.py` | CREATE | Public exports for indicator contracts and calculation entrypoint. |
| `app/indicators/technical.py` | CREATE | Deterministic core indicator calculations and typed output contracts. |
| `tests/indicators/__init__.py` | CREATE | Test package marker for indicator tests. |
| `tests/indicators/test_technical.py` | CREATE | Fixture tests for formulas, warm-up, anti-leakage, and invalid inputs. |
| `docs/scoring-methodology.md` | UPDATE | Replace future indicator language with implemented formula, warm-up, and missing-data policy. |

---

## Technical Contract

### Public Models

Implement these frozen Pydantic-style models in `app/indicators/technical.py`.

- `IndicatorConfig`
  - `sma_periods: tuple[int, ...] = (20, 50, 200)`
  - `rsi_period: int = 14`
  - `macd_fast_period: int = 12`
  - `macd_slow_period: int = 26`
  - `macd_signal_period: int = 9`
  - `relative_volume_period: int = 20`
  - `atr_period: int = 14`
  - `recent_periods: int = 5`
  - Validate all periods are positive.
  - Validate `sma_periods` is non-empty and unique after sorting.
  - Validate `macd_slow_period > macd_fast_period`.

- `IndicatorIncompleteReason`
  - `NO_CANDLES = "no_candles"`
  - `INSUFFICIENT_HISTORY = "insufficient_history"`
  - `ZERO_VOLUME_BASELINE = "zero_volume_baseline"`

- `IndicatorIncompleteDetail`
  - `indicator: str`
  - `reason: IndicatorIncompleteReason`
  - `required_candles: int`
  - `available_candles: int`
  - `message: str | None = None`

- `MacdValue`
  - `line: float | None`
  - `signal: float | None`
  - `histogram: float | None`

- `IndicatorPoint`
  - `session_date: date`
  - `close: float`
  - `volume: int`
  - `moving_averages: dict[int, float | None]`
  - `rsi: float | None`
  - `macd: MacdValue`
  - `relative_volume: float | None`
  - `atr: float | None`

- `TechnicalIndicatorSnapshot`
  - `symbol: str | None`
  - `provider: str | None`
  - `adjusted: bool | None`
  - `data_recency: DataRecency`
  - `start_session_date: date | None`
  - `end_session_date: date | None`
  - `available_candles: int`
  - `required_candles: int`
  - `is_complete: bool`
  - `latest: IndicatorPoint | None`
  - `recent_points: tuple[IndicatorPoint, ...]`
  - `incomplete_details: tuple[IndicatorIncompleteDetail, ...]`

For no-candle input, return a snapshot with `symbol=None`, `provider=None`,
`adjusted=None`, the existing `DataRecency.UNKNOWN` enum value, no dates,
`available_candles=0`, `latest=None`, `recent_points=()`, `is_complete=False`, and a
`NO_CANDLES` detail. Do not add a new data-recency enum member unless the existing
market-data schema no longer provides an unknown-style value.

### Calculation Entry Point

```python
def calculate_technical_indicators(
    candles: Sequence[DailyCandle],
    config: IndicatorConfig = IndicatorConfig(),
) -> TechnicalIndicatorSnapshot:
    ...
```

The function must not mutate the input sequence.

---

## Calculation and Robustness Rules

### Input Validation

- Accept only normalized `DailyCandle` objects.
- Sort candles ascending by `session_date` before calculation.
- Empty input is an incomplete data state, not an exception.
- Reject these inputs with `ValueError`:
  - Mixed `symbol`
  - Mixed `provider`
  - Mixed `adjusted`
  - Duplicate `session_date`
  - Duplicate timestamps for different sessions
  - Non-finite numeric conversions
- Use `session_date` as the alignment key.
- Do not infer missing exchange-calendar sessions. Without an exchange calendar, gaps are
  metadata for downstream freshness checks, not calculation errors.
- Require caller-provided candles to be completed daily bars. Do not merge quotes,
  intraday candles, or current partial-session data into these indicators.

### Missing Data Policy

- Returned unavailable indicator values must be Python `None`.
- Internal pandas/NumPy `NaN` values must be converted before constructing public models.
- Do not return `NaN`, `inf`, sentinel numbers, defaulted zeros, forward-filled values,
  backfilled values, rounded values, clipped values, or winsorized values.
- Latest unavailable required indicators each get one `IndicatorIncompleteDetail`.
- `is_complete=True` only when the latest point has all indicators required by
  `IndicatorConfig`:
  - One SMA value for every period in `config.sma_periods`
  - RSI
  - MACD line, signal, and histogram
  - Relative volume
  - ATR

### Anti-Leakage Policy

- Indicator values for session `t` may use only candles with `session_date <= t`.
- Never use centered rolling windows or future rows.
- SMA, RSI, MACD, and ATR include session `t` because they describe the completed daily
  candle for `t`.
- Relative volume for session `t` must exclude session `t` from its baseline:

```text
relative_volume[t] = volume[t] / mean(volume[t - period : t])
```

After sorting by `session_date` ascending, implement this as:

```text
volume / volume.shift(1).rolling(period, min_periods=period).mean()
```

### Formula Rules

- SMA:

```text
close.rolling(period, min_periods=period).mean()
```

- RSI:
  - Use close-to-close deltas.
  - Use Wilder smoothing.
  - Seed average gain/loss at index `period` from the first `period` deltas.
  - First valid RSI requires `period + 1` candles.
  - If average gain and average loss are both zero, return `50`.
  - If average loss is zero and average gain is positive, return `100`.
  - If average gain is zero and average loss is positive, return `0`.
  - Treat average gain/loss as zero only when exactly zero after deterministic
    calculation, or use a named `EPSILON` constant only for floating-point noise.
  - Add tests for tiny nonzero gain/loss boundary behavior so small real movement is not
    misclassified as zero.

- MACD:
  - Use custom EMA seeded by SMA, not first-price seeding.
  - This is NookScout's declared MACD convention for reproducibility. Tests should
    validate this project-defined convention, not attempt parity with every charting
    platform or provider endpoint.
  - Fast EMA first valid at `fast_period` candles.
  - Slow EMA first valid at `slow_period` candles.
  - MACD line is valid only when both EMAs are valid.
  - Signal line is an EMA seeded from the first full `macd_signal_period` window of valid
    MACD values.
  - Signal line first valid after `macd_slow_period + macd_signal_period - 1` candles.
  - Histogram is valid only when MACD line and signal line are both valid.

- ATR:
  - True range for the first candle is `high - low`.
  - Later true range is:

```text
max(high - low, abs(high - previous_close), abs(low - previous_close))
```

  - Seed ATR from the first full `atr_period` true-range window.
  - Continue with Wilder smoothing.
  - First valid ATR requires `atr_period` candles.
  - Add a test that locks the first true-range value so the implementation does not
    accidentally drop the first row or seed from candle 2.

- Relative Volume:
  - First valid relative volume requires `relative_volume_period + 1` candles.
  - Baseline is the mean of the prior completed `relative_volume_period` volumes.
  - If the prior-volume baseline is zero, return `None` and add
    `ZERO_VOLUME_BASELINE`.

### Required Candle Count

Set `required_candles` to the maximum of:

- Largest period in `config.sma_periods`
- `rsi_period + 1`
- `macd_slow_period + macd_signal_period - 1`
- `relative_volume_period + 1`
- `atr_period`

With default config, this is `200`.

---

## Tasks

### Task 1: Add Indicator Package Exports

- **File**: `app/indicators/__init__.py`
- **Action**: CREATE
- **Implement**: Export `IndicatorConfig`, `IndicatorIncompleteDetail`,
  `IndicatorIncompleteReason`, `IndicatorPoint`, `MacdValue`,
  `TechnicalIndicatorSnapshot`, and `calculate_technical_indicators`.
- **Mirror**: `app/market_data/__init__.py` - public package API through explicit
  imports and `__all__`.
- **Validate**: `uv run mypy .`

### Task 2: Add Typed Indicator Contracts

- **File**: `app/indicators/technical.py`
- **Action**: CREATE
- **Implement**: Add config, incomplete-detail, point, MACD, and snapshot models.
  Reuse `MarketDataModel` and `DataRecency` from `app.market_data.schemas`.
- **Mirror**: `app/market_data/schemas.py:44` - frozen domain contracts and validators.
- **Validate**: `uv run mypy .`

### Task 3: Implement Input Preparation

- **File**: `app/indicators/technical.py`
- **Action**: UPDATE
- **Implement**: Add candle sorting, basis validation, numeric conversion, no-candle
  snapshot creation, and metadata extraction.
- **Mirror**: `app/market_data/liquidity.py:100` - normalized domain input validation.
- **Validate**: `uv run pytest tests/indicators/test_technical.py`

### Task 4: Implement Leak-Free Indicator Calculations

- **File**: `app/indicators/technical.py`
- **Action**: UPDATE
- **Implement**: Add SMA, Wilder RSI, SMA-seeded EMA/MACD, Wilder ATR, and relative
  volume helpers according to the calculation rules above.
- **Mirror**: `app/market_data/liquidity.py:138` - deterministic pure calculation
  entrypoint.
- **Validate**: `uv run pytest tests/indicators/test_technical.py`

### Task 5: Build Snapshot Output and Incomplete Details

- **File**: `app/indicators/technical.py`
- **Action**: UPDATE
- **Implement**: Convert internal missing values to `None`, create latest and recent
  points, compute `is_complete` from `config.sma_periods` and the configured RSI, MACD,
  relative-volume, and ATR requirements, add latest incomplete details, and expose
  stable metadata.
- **Mirror**: `app/market_data/universe.py:53` - domain aggregate result with derived
  counts and metadata.
- **Validate**: `uv run pytest tests/indicators/test_technical.py`

### Task 6: Add Indicator Fixture Tests

- **File**: `tests/indicators/test_technical.py`
- **Action**: CREATE
- **Implement**: Add local candle builders and tests for formulas, warm-up, missing
  data, invalid basis inputs, and anti-leakage.
- **Mirror**: `tests/market_data/test_liquidity.py:140` - compact local builders and
  behavior-focused assertions.
- **Validate**: `uv run pytest tests/indicators/test_technical.py`

### Task 7: Document Implemented Indicator Methodology

- **File**: `docs/scoring-methodology.md`
- **Action**: UPDATE
- **Implement**: Replace the future indicator section with implemented formula,
  warm-up, missing-data, anti-leakage, completed-daily-candle, and adjusted-candle basis
  conventions.
- **Mirror**: `docs/scoring-methodology.md:103` - canonical methodology documentation.
- **Validate**: `rg -n "SMA|RSI|MACD|ATR|relative volume|warm-up|leak" docs/scoring-methodology.md`

---

## Test Scenarios

- Expected values:
  - SMA values for simple increasing close series.
  - RSI values for known mixed gain/loss series.
  - MACD line, signal, and histogram for a deterministic series.
  - ATR values for a hand-checkable OHLC series with gaps.
  - Relative volume values for known prior-volume baselines.
- Robustness:
  - No candles returns incomplete snapshot and does not raise.
  - Insufficient history returns `None` values and specific incomplete details.
  - Current-session volume spike does not affect its own relative-volume baseline.
  - MACD line, signal, and histogram remain `None` until each warm-up requirement is met.
  - Flat price series produces stable SMAs, RSI `50`, MACD line/signal/histogram equal
    to `pytest.approx(0.0)` after warm-up, ATR `0`, and relative volume near `1`.
  - Tiny nonzero RSI gain/loss values are not classified as exactly zero unless they are
    within the explicitly named floating-point-noise `EPSILON`.
  - Volatile series produces nonzero ATR and responsive RSI/MACD movement.
  - Mixed symbols, mixed providers, mixed adjusted flags, duplicate sessions, and
    duplicate timestamps for different sessions raise `ValueError`.
  - Missing volume is rejected by the existing `DailyCandle` contract.
- Test quality:
  - Expected numerical values should be independent hand/static values, not recomputed
    through production helper functions.
  - Use `pytest.approx` for floating-point assertions.

---

## Validation

Run the backend validation commands from `AGENTS.md`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

## End-to-End Verification

- [ ] Build a deterministic candle sequence in tests.
- [ ] Call `calculate_technical_indicators(...)`.
- [ ] Confirm the latest snapshot is complete only after the full default `200`-candle
      requirement is met.
- [ ] Confirm no returned value contains `NaN`, `inf`, or fabricated numeric defaults.
- [ ] Confirm docs describe the same formulas implemented in code.

## Acceptance Criteria

- [ ] `app/indicators/technical.py` computes default 20/50/200 SMA values, configurable
      SMA periods, RSI, MACD, relative volume, and ATR from normalized daily candles.
- [ ] Indicator outputs include recent values and metadata for scoring and explanation.
- [ ] Incomplete candle histories return explicit incomplete-data states.
- [ ] Fixture tests cover expected values, insufficient history, flat series, volatile
      series, and missing volume behavior.
- [ ] Implementation follows provider-neutral, deterministic, leak-free rules.
- [ ] Validation commands pass.

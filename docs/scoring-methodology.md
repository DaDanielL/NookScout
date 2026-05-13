# Scoring Methodology

Last updated: 2026-05-13

This document is the canonical MVP reference for rules that determine which tickers and
future setup ideas NookScout surfaces or suppresses. It documents educational research
filters and deterministic decision rules. It is not brokerage functionality, trade
execution guidance, personalized financial advice, or a promise of any outcome.

## Current Implementation Status

Implemented by STORY-005 and STORY-008:

- Configurable predefined universe symbols.
- Configurable liquidity filters for Scout Mode universe eligibility.
- Provider-neutral eligible and ineligible universe results with exclusion reasons.
- Deterministic core technical indicators from normalized completed daily candles:
  SMA, RSI, MACD, ATR, and relative volume.

Planned, not implemented yet:

- Support/resistance and relative-strength calculations.
- Trend and setup classification.
- Setup scoring, ranking, tie-breaking, confidence labels, no-clear-setup decisions,
  entry zone, invalidation area, target area, and risk/reward estimates.
- LLM-generated rationale.

## Ticker Eligibility and Universe Source

Scout Mode starts from `NOOKSCOUT_PREDEFINED_UNIVERSE_SYMBOLS`, a local comma-separated
setting controlled by the user. NookScout normalizes symbols to a supported U.S.
equity-style format, removes blank entries, and de-duplicates repeated symbols while
preserving the configured order.

The MVP does not hard-code one-off ticker lists in scoring or domain logic. A configured
symbol must pass the liquidity rules below before it is eligible for future setup
discovery.

## Liquidity Filter Rules

The MVP defaults are intentionally conservative for beginner-friendly swing-trading
research:

| Rule | Default |
|------|---------|
| Minimum last price | `$5` |
| Minimum average daily volume | `1,000,000` shares |
| Minimum dollar volume | `$20,000,000` |
| Minimum market cap | `$1,000,000,000` |
| Allowed listing venues | `XNAS`, `XNYS`, `NASDAQ`, `NYSE` |
| Average-volume lookback | `90` days |
| OTC securities | Excluded |
| Default asset type | Common stock only |
| Default currency | `USD` |

These thresholds are configurable through environment settings. They are filters for
research suitability, not predictions or recommendations.

## Average Volume and Dollar Volume

NookScout uses provider-neutral market-data contracts only:

- `TickerReference` for active status, OTC status, asset type, exchange, currency, market
  cap, and provider-supplied average daily volume when available.
- `Quote` for current or delayed last price.
- `DailyCandle` for fallback volume calculations.

When `TickerReference.average_daily_volume` is available, it is used directly. When it is
missing, NookScout calculates average daily volume from normalized daily candle volumes
over the configured lookback window.

Dollar volume is calculated as:

```text
last_price * average_daily_volume
```

The Massive adapter currently does not supply reliable average daily volume in normalized
reference data, so the MVP derives average volume from normalized daily candles when
reference average volume is absent.

## Missing Data and Exclusion Behavior

NookScout returns ineligible results with explicit exclusion reasons instead of silently
dropping configured symbols. Reasons include missing reference data, inactive securities,
OTC securities, unsupported asset type, unsupported currency, unsupported exchange,
missing or low price, missing or low average daily volume, missing or low market cap, and
missing or low dollar volume.

Symbol-level missing or incomplete provider data should become an ineligible result when
the rest of the universe can still be evaluated. Systemic provider failures such as
authentication, rate limits, or provider downtime should surface as API errors.

## Provider Freshness and Constraints

Provider freshness can affect whether a ticker appears eligible. The MVP provider decision
uses Massive Stocks Starter data, which is delayed rather than real time. Universe
responses include provider and data-recency metadata so downstream API consumers and UI
views can label the data context clearly.

Provider choice, licensing, freshness, and hosted-distribution constraints remain in
[market-data-providers.md](market-data-providers.md). This document owns the
recommendation-impacting rule definitions.

## Implemented Indicator Methodology

Core indicators are calculated in `app/indicators/technical.py` from normalized
`DailyCandle` contracts only. Indicator code does not call market-data providers and does
not consume provider-specific payloads. Caller-provided candles are expected to be
completed daily bars; NookScout does not merge quotes, intraday candles, or current
partial-session data into these calculations.

Inputs are sorted by `session_date` before calculation. Mixed symbols, mixed providers,
mixed adjusted/unadjusted basis, duplicate session dates, duplicate timestamps across
different sessions, and non-finite numeric values are rejected. Missing exchange-calendar
sessions are not inferred by the indicator layer.

Default indicator windows are:

| Indicator | Default |
|-----------|---------|
| SMA | `20`, `50`, `200` sessions |
| RSI | `14` sessions |
| MACD | `12` fast EMA, `26` slow EMA, `9` signal EMA |
| Relative volume | `20` prior sessions |
| ATR | `14` sessions |
| Recent snapshot window | `5` sessions |

The default complete warm-up requirement is `200` candles because the 200-session SMA is
the longest required default input. With custom periods, the required candle count is the
maximum of the longest SMA period, `RSI period + 1`, `MACD slow + signal - 1`, `relative
volume period + 1`, and the ATR period.

### Indicator Formulas

SMA uses a trailing simple moving average:

```text
close.rolling(period, min_periods=period).mean()
```

RSI uses close-to-close deltas and Wilder smoothing. The first average gain/loss is seeded
from the first full window of deltas, so the first valid RSI requires `period + 1`
completed candles. A flat average gain and loss returns `50`; a positive average gain
with zero average loss returns `100`; zero average gain with positive average loss returns
`0`.

MACD uses NookScout's reproducible SMA-seeded EMA convention, not first-price EMA
seeding. The fast EMA first appears after the fast period, the slow EMA after the slow
period, and the signal line is an EMA seeded from the first full signal-period window of
valid MACD line values. The first valid signal and histogram require:

```text
macd_slow_period + macd_signal_period - 1
```

ATR uses true range with the first candle defined as `high - low`. Later true range is:

```text
max(high - low, abs(high - previous_close), abs(low - previous_close))
```

ATR is seeded from the first full true-range window and then uses Wilder smoothing.

Relative volume compares the current completed candle volume with the prior completed
volume baseline. The current session is excluded from its own baseline:

```text
volume[t] / mean(volume[t - period : t])
```

Operationally this is equivalent to:

```text
volume / volume.shift(1).rolling(period, min_periods=period).mean()
```

### Missing Data And Anti-Leakage Policy

Unavailable indicator values are returned as `None` with explicit incomplete details on
the latest snapshot. Warm-up values are not forward-filled, backfilled, zero-filled,
clipped, rounded, or replaced with sentinel values. Internal `NaN` values are converted
before public models are constructed, and public snapshots must not contain `NaN` or
infinite values.

Indicator values for session `t` may use only candles with `session_date <= t`. SMA, RSI,
MACD, and ATR include the completed candle for session `t`; relative volume excludes
session `t` from the baseline by using only prior completed volumes.

If the latest relative-volume baseline is zero, relative volume is unavailable and the
snapshot records a `zero_volume_baseline` incomplete reason. If there are no candles, the
snapshot records `no_candles` rather than raising. Insufficient warm-up history records
`insufficient_history` details.

Support/resistance and relative-strength calculations remain future work. Provider
indicator endpoints may be used only as a documented comparison or fallback if a later
story explicitly approves that behavior.

## Future Trend and Setup Classification

Planned, not implemented in STORY-005.

Future setup classification should keep the MVP scope to bullish long swing-trading
research ideas. Weak or unclear tickers should be labeled as no-clear-setup or wait states
rather than being forced into a setup category.

## Future Scoring, Ranking, and Levels

Planned, not implemented in STORY-005.

Future scoring rules should define ranking factors, tie-breaking, confidence labels,
no-clear-setup behavior, entry zone, invalidation area, target area, risk/reward estimate,
and failure case. Confidence labels must not imply certainty.

LLM rationale may explain deterministic setup data, but it must not invent prices,
indicators, ticker metadata, chart levels, or risk/reward values.

## Versioning and Review Notes

Liquidity and future scoring rules should be versioned when persisted setup ideas are
introduced, so old outputs remain interpretable after rule changes. Any hosted,
multi-user, or redistribution use should trigger a provider licensing and compliance
review before launch.

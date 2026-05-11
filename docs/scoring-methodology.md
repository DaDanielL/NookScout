# Scoring Methodology

Last updated: 2026-05-11

This document is the canonical MVP reference for rules that determine which tickers and
future setup ideas NookScout surfaces or suppresses. It documents educational research
filters and deterministic decision rules. It is not brokerage functionality, trade
execution guidance, personalized financial advice, or a promise of any outcome.

## Current Implementation Status

Implemented by STORY-005:

- Configurable predefined universe symbols.
- Configurable liquidity filters for Scout Mode universe eligibility.
- Provider-neutral eligible and ineligible universe results with exclusion reasons.

Planned, not implemented in STORY-005:

- Technical indicator calculations.
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

## Future Indicator Methodology

Planned, not implemented in STORY-005.

Future indicator code should be deterministic and should calculate moving averages, RSI,
MACD, ATR, relative volume, support/resistance, and relative strength from normalized
market data. Provider indicator endpoints may be used only as a documented comparison or
fallback if a later story explicitly approves that behavior.

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

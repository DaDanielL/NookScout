# Market Data Providers

Research date: 2026-05-07

This note records the MVP market data provider decision for STORY-001. NookScout should consume provider data only through future adapters under `app/market_data/`; scoring, indicators, charts, and UI code should never call a provider API directly.

Provider choice, licensing, freshness, and adapter constraints are documented here. Rules
that determine whether provider data makes a ticker eligible or ineligible for NookScout
research output are documented in [scoring-methodology.md](scoring-methodology.md).

## MVP Recommendation

Use **Massive Stocks Starter** for the MVP.

Massive, formerly Polygon.io, is the best first provider for NookScout because its stock product cleanly covers the local swing-trading workflow: U.S. stock universe discovery, delayed current-market snapshots, daily OHLCV history, company reference data with exchange and market-cap fields, corporate actions, and a straightforward REST API. The Stocks Starter plan is listed at **$29/month** for individual use and includes unlimited API calls, 5 years of historical data, 100% U.S. market coverage, 15-minute delayed data, reference data, corporate actions, technical indicators, minute aggregates, WebSockets, snapshots, and second aggregates.

Budget assumption: plan for **$29/month** while the app remains a local-only personal tool. The free Stocks Basic plan is useful for experimentation but is too constrained for NookScout because it is limited to 5 API calls per minute and end-of-day data, and it does not include the snapshot endpoint needed for convenient current-price context. The $199/month Stocks Advanced plan is not needed for MVP because the product is swing-trading oriented and can tolerate 15-minute delayed data.

Data freshness assumption: use **15-minute delayed** snapshots and bars for MVP. NookScout should label data freshness in API responses and UI once those layers exist. It should not imply real-time trading precision.

Rate-limit assumption: Stocks Starter advertises unlimited API calls for individual use. The adapter should still include timeout, retry, and backoff behavior because provider outages, entitlement errors, and abuse controls can still occur.

Local-only assumption: the recommendation is for one non-professional local operator. Before hosting NookScout, adding multi-user access, redistributing data, or showing provider-derived market data to other users, revisit Massive business terms and exchange obligations. Massive market-data terms restrict redistribution and business/commercial use unless separately licensed.

## Provider Comparison

| Provider | Quotes / Current Price | Historical Daily Candles and Volume | Reference Data for Liquidity | Cost and Limits | Delayed / Real-Time Behavior | Provider Indicators | Licensing and Hosted Risk | MVP Fit |
|----------|------------------------|-------------------------------------|------------------------------|-----------------|------------------------------|---------------------|----------------------------|---------|
| **Massive / Polygon.io** | Stocks Starter includes full-market snapshots with delayed current session data. Dedicated quote objects are only returned when the plan includes quotes, so MVP should use snapshot/session fields rather than require NBBO quotes. | Custom bars endpoint supports OHLCV aggregates over date ranges, including daily bars, with split-adjusted behavior by default. Stocks Starter includes 5 years of history. | Ticker Overview includes company attributes such as active status, market, type, primary exchange, market cap, and shares fields. Reference data and corporate actions are included in stock plans. | Stocks Basic is free but limited to 5 calls/minute and end-of-day data. Stocks Starter is $29/month with unlimited API calls. Stocks Developer is $79/month; Stocks Advanced is $199/month. | Basic is end-of-day only. Starter and Developer are 15-minute delayed. Advanced is real-time. | Technical indicators are available, but NookScout should record this only as provider context and defer ownership to STORY-007. | Individual market data is for non-professional, personal, non-business use. Redistribution, external display, or multi-user hosted use needs a business/commercial review. | **Recommended**: best balance of price, U.S. coverage, snapshots, daily OHLCV, reference data, market cap, and clean adapter path. |
| **Alpaca Market Data** | Latest quote endpoints support stock symbols and feeds such as IEX, SIP, delayed SIP, and OTC depending on entitlement. Free Trading API users get limited IEX coverage; Algo Trader Plus expands to all U.S. exchanges. | Historical stock bars endpoint supports daily bars, pagination, adjustment options, feed selection, and volume. Historical equities data is available since 2016. | Assets endpoint covers tradable asset metadata such as symbol, class, exchange, status, and OTC identification. It is weaker for NookScout liquidity filtering because market cap is not part of the basic asset contract. | Basic Trading API market data is free with 200 historical API calls/minute. Algo Trader Plus is $99/month with 10,000 historical API calls/minute. | Basic provides IEX real-time coverage and has a latest-15-minutes historical limitation. Algo Trader Plus provides all-exchange SIP access without that limitation. | No provider-indicator dependency identified for MVP. Indicators should be computed internally unless STORY-007 says otherwise. | Alpaca says API data cannot be redistributed. Alpaca also brings brokerage/trading-platform context that NookScout should avoid in MVP product design. | Good fallback for free experimentation, but not recommended first because reference data is less complete for market-cap liquidity filtering and brokerage coupling is unnecessary. |
| **Twelve Data** | Basic includes real-time U.S. equities and ETFs. The API offers price and time-series endpoints with JSON/CSV support and per-endpoint credit weights. | `time_series` returns OHLC and, where applicable, volume. It supports intervals such as `1day`, with output size limits and per-symbol credit usage. | Reference/discovery endpoints include symbol search, exchange, MIC, country, instrument type, and access metadata. Fundamentals and market-cap style data are stronger on paid tiers. | Basic is free with 8 API credits/minute and 800/day. Grow is $79/month, Pro is $229/month, and higher tiers add more credits and markets. | Pricing states real-time U.S. equities and ETFs on Basic. Higher tiers add more markets, fundamentals, and no daily limits. | Twelve Data has broad technical indicator endpoints. NookScout should not rely on them before STORY-007. | Terms limit use to internal use unless the subscription or add-on grants redistribution or external display rights; free-tier data cannot be used commercially. | Viable but not recommended first because per-symbol credits and daily free limits are likely awkward for scanning a stock universe. |

## Decision Details

The selected first provider is `massive`.

Reasons:

- It provides a single U.S. stock data surface for the MVP's required universe scan, snapshots, candles, volume, and reference fields.
- The Ticker Overview endpoint includes market cap and listing metadata, which directly supports the PRD liquidity rules around price, volume, dollar volume, market cap, and OTC exclusions.
- The Full Market Snapshot endpoint can support Scout Mode current-price and volume context without making one request per ticker.
- The $29/month Starter tier is more practical than Twelve Data's per-symbol free quota and cheaper than Alpaca Algo Trader Plus when all-exchange delayed coverage is acceptable.
- It has a clean path to a future hosted review: individual use now, business plan or separate licensing later.

Known constraints:

- This decision does not approve redistribution, business use, or multi-user hosting. A hosted version must revisit provider licensing and exchange terms.
- Stocks Starter is delayed, not real-time. This is acceptable for a 3 to 20 trading day swing-trading workflow, but the app should clearly label delayed data.
- The adapter should avoid full tick-level ingestion for MVP. Prefer snapshot, ticker overview, and daily aggregate bars.
- Provider-specific payloads must be normalized before reaching indicator, scoring, persistence, or UI code.

## Provider-Supplied Indicators

Massive and Twelve Data both expose technical indicator endpoints. The presence of provider-supplied indicators is useful reference information, but NookScout should **not** depend on provider-calculated indicators before STORY-007.

For MVP architecture, deterministic NookScout code should own moving averages, RSI, MACD, ATR, relative volume, support/resistance, relative strength, setup levels, risk/reward, setup classification, and failure conditions. Provider indicators may later be used only as a comparison or fallback if STORY-007 explicitly documents that choice.

## Required Environment Variables

Use these variables for the selected provider. Values must be placeholders in `.env.example` and real secrets only in a local ignored `.env` file.

```bash
NOOKSCOUT_MARKET_DATA_PROVIDER=massive
MASSIVE_API_KEY=replace_with_your_massive_api_key
MASSIVE_API_BASE_URL=https://api.polygon.io
MASSIVE_STOCKS_PLAN=starter
MASSIVE_DATA_RECENCY=delayed
MASSIVE_REQUEST_TIMEOUT_SECONDS=30
MASSIVE_MAX_RETRIES=3
```

`MASSIVE_API_BASE_URL` uses the longstanding Polygon API base while Massive rebrand materials and docs continue to support existing Polygon integrations. The future adapter can switch this setting if Massive standardizes a different base URL in the SDK or REST docs.

## Implementation Notes for Later Stories

- STORY-003 should define provider-neutral schemas for quotes/snapshots, daily candles, reference data, provider capabilities, and data recency.
- STORY-004 should implement the concrete adapter as `app/market_data/massive.py` or another name chosen by local conventions after scaffold.
- STORY-005 should use reference metadata, snapshot prices, average volume, dollar volume, exchange/listing type, and market cap to implement configurable liquidity rules. Keep the exact recommendation-impacting rule definitions in [scoring-methodology.md](scoring-methodology.md).
- Default tests should use mocked provider responses and fixtures. Do not perform live provider calls in normal local or CI validation.
- Provider errors should map to typed unavailable, unauthorized, rate-limited, missing-symbol, and incomplete-data states once product code exists.

## Sources

- Massive Stocks pricing: https://massive.com/pricing?product=stocks
- Massive stock custom bars: https://massive.com/docs/rest/stocks/aggregates/custom-bars
- Massive stock full-market snapshot: https://massive.com/docs/rest/stocks/snapshots/full-market-snapshot
- Massive Ticker Overview reference data: https://massive.com/docs/rest/stocks/tickers/ticker-overview
- Massive Market Data Terms: https://massive.com/terms/market_data_terms.pdf
- Alpaca Market Data API overview: https://docs.alpaca.markets/docs/about-market-data-api
- Alpaca historical stock bars: https://docs.alpaca.markets/reference/stockbars
- Alpaca assets reference: https://docs.alpaca.markets/reference/get-v2-assets-1
- Alpaca redistribution support note: https://alpaca.markets/support/redistribute-alpaca-api
- Twelve Data pricing: https://twelvedata.com/pricing
- Twelve Data API documentation: https://twelvedata.com/docs
- Twelve Data Terms of Use: https://twelvedata.com/terms

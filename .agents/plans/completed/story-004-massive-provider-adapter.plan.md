# Plan: STORY-004 Massive Provider Adapter

## Summary

Implement the first concrete market data adapter as `MassiveMarketDataProvider` under `app/market_data/massive.py`. The adapter should use Massive/Polygon REST endpoints for current snapshot-derived quotes, batched snapshots, daily aggregate candles, and minimal ticker reference data while returning only the provider-neutral contracts from STORY-003. Tests should use `httpx.MockTransport` plus JSON fixtures under `tests/fixtures/market_data/`, map provider failures to existing typed exceptions, and prove logs contain ticker/operation context without leaking API keys or authorization headers.

## User Story

As a developer, I want the first provider adapter to fetch current quotes and daily historical candles, so that NookScout can build setup inputs without live-provider calls leaking into domain code.

## Metadata

| Field | Value |
|-------|-------|
| Type | NEW_CAPABILITY |
| Complexity | MEDIUM |
| Systems Affected | Backend market data layer, runtime dependencies, mocked provider tests, fixture payloads |
| GitHub Issue | #4, https://github.com/DaDanielL/NookScout/issues/4 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-004` |

---

## Feature Understanding

**Problem**: The shared market data contracts exist, but there is no concrete adapter that talks to the selected MVP provider. Without this boundary, future ingestion, liquidity filtering, indicators, scoring, and chart APIs could either stall or accidentally depend on provider-specific payload shapes.

**Scope boundary**: Implement provider access and normalization only. Do not add persistence, ingestion jobs, API routes, indicator calculations, scoring logic, UI code, live-provider tests, streaming, WebSockets, or tick-level ingestion.

**Provider docs checked**: Official Massive docs were checked on 2026-05-11 for the REST quickstart/authentication, single ticker snapshot, full market snapshot, custom aggregate bars, and ticker overview endpoints:

- https://massive.com/docs/rest/quickstart?auth=signup
- https://massive.com/docs/rest/stocks/snapshots/single-ticker-snapshot
- https://massive.com/docs/rest/stocks/snapshots/full-market-snapshot
- https://massive.com/docs/rest/stocks/aggregates/custom-bars
- https://massive.com/docs/rest/stocks/tickers/ticker-overview

---

## Patterns to Follow

### Naming

```text
SOURCE: app/market_data/base.py:35
The concrete adapter should satisfy MarketDataProvider with provider_name, capabilities(),
get_quote(), get_quotes(), get_daily_candles(), and get_ticker_reference().
```

```text
SOURCE: docs/market-data-providers.md:31
The selected first provider identifier is `massive`; name the concrete module
`app/market_data/massive.py` and class `MassiveMarketDataProvider`.
```

```text
SOURCE: .agents/stories/nookscout-technical-setup-discovery.stories.md:185
Store provider-specific code under app/market_data/{provider}.py, favor daily
candles and fresh quotes, and keep fixture payloads in tests/fixtures/.
```

### Contracts

```text
SOURCE: app/market_data/schemas.py:89
Quote is the normalized current price/snapshot contract. It requires symbol,
last_price, previous_close, as_of, provider, and data_recency, with optional
bid/ask and intraday OHLCV fields.
```

```text
SOURCE: app/market_data/schemas.py:149
DailyCandle is the normalized OHLCV contract. It requires timezone-aware
timestamps, exchange-local session_date alignment, positive OHLC values,
non-negative volume, provider, and data_recency.
```

```text
SOURCE: app/market_data/schemas.py:246
ProviderCapabilities exposes support flags, recency labels, delay metadata,
history depth, and warnings without provider-specific payloads.
```

### Settings And Secrets

```text
SOURCE: app/core/settings.py:38
MASSIVE_API_KEY is a SecretStr and must never be logged or embedded in URLs.
Use an Authorization header rather than query-string apiKey params.
```

```text
SOURCE: app/core/settings.py:39
MASSIVE_API_BASE_URL defaults to https://api.polygon.io, preserving the current
documented Massive/Polygon base URL setting.
```

### Error Handling

```text
SOURCE: app/market_data/base.py:10
Existing typed exceptions are the provider boundary: ProviderAuthenticationError,
ProviderRateLimitError, ProviderUnavailableError, SymbolNotFoundError, and
IncompleteMarketDataError.
```

```text
SOURCE: AGENTS.md:218
Provider errors should fail gracefully and log enough context to debug without
leaking API keys.
```

### Tests

```text
SOURCE: tests/market_data/test_base.py:26
Existing provider tests prove a provider through the MarketDataProvider protocol
and assert normalized contract returns rather than provider payload access.
```

```text
SOURCE: tests/market_data/test_schemas.py:21
Existing market-data tests use small helper payload builders and assert Pydantic
normalization and validation behavior directly.
```

```text
SOURCE: tests/conftest.py:13
Tests bypass local .env through deterministic settings helpers, so adapter tests
must not depend on local secrets.
```

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `pyproject.toml` | UPDATE | Move `httpx>=0.27.0` from dev-only dependencies into project dependencies because production adapter code will import it. |
| `uv.lock` | UPDATE | Refresh lockfile after dependency group change. |
| `app/market_data/massive.py` | CREATE | Implement Massive REST adapter, response normalization helpers, redacted logging, retries/status mapping, and settings factory. |
| `app/market_data/__init__.py` | UPDATE | Export `MassiveMarketDataProvider` for easy adapter discovery without exposing provider payload shapes. |
| `tests/fixtures/market_data/massive_single_snapshot_aapl.json` | CREATE | Mock single ticker snapshot response for `get_quote()`. |
| `tests/fixtures/market_data/massive_full_snapshot_batch.json` | CREATE | Mock batched snapshot response for `get_quotes()`. |
| `tests/fixtures/market_data/massive_daily_aggs_aapl.json` | CREATE | Mock aggregate daily bar response for `get_daily_candles()`. |
| `tests/fixtures/market_data/massive_ticker_overview_aapl.json` | CREATE | Mock ticker overview response for `get_ticker_reference()`. |
| `tests/market_data/test_massive.py` | CREATE | Cover adapter contract behavior, normalization, HTTP status/error mapping, missing data, fixture usage, no live calls, and log redaction. |

No database migration, API route, scheduler job, frontend file, or provider-backed integration test is needed for this story.

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: Promote HTTP Client Dependency

- **File**: `pyproject.toml`, `uv.lock`
- **Action**: UPDATE
- **Implement**: Move `httpx>=0.27.0` from `[dependency-groups].dev` into `[project].dependencies` because `app/market_data/massive.py` will import it at runtime. Refresh `uv.lock` with uv after editing.
- **Mirror**: `pyproject.toml:7` - runtime imports belong in project dependencies; dev-only tooling stays in the dev group.
- **Validate**: `uv run mypy .`

### Task 2: Create Massive Adapter Skeleton

- **File**: `app/market_data/massive.py`
- **Action**: CREATE
- **Implement**: Add `MassiveMarketDataProvider` with:
  - `provider_name = "massive"`;
  - constructor accepting `api_key`, `base_url`, `data_recency`, `timeout_seconds`, `max_retries`, optional injected `httpx.Client`, and optional sleep/backoff callable for tests;
  - `from_settings(settings: Settings)` classmethod;
  - `capabilities()` returning `ProviderCapabilities(provider="massive", supports_quotes=True, supports_snapshots=True, supports_daily_candles=True, supports_reference_data=True, supports_adjusted_daily_candles=True, supported_recency=(DataRecency.DELAYED, DataRecency.END_OF_DAY), delayed_minutes=15, max_history_years=5, warnings=(...))`;
  - no HTTP calls at import or construction time.
- **Mirror**: `app/market_data/base.py:35` - satisfy the existing synchronous protocol.
- **Validate**: `uv run mypy .`

### Task 3: Add Redacted Request Helper And Error Mapping

- **File**: `app/market_data/massive.py`
- **Action**: UPDATE
- **Implement**: Add a private `_request_json(operation, path, params, symbol_context)` helper that:
  - raises `ProviderAuthenticationError` if no API key is configured;
  - authenticates with an `Authorization` header, not `apiKey` query params;
  - logs operation, symbol or symbol count, endpoint path, attempt number, and status code only;
  - never logs API keys, authorization headers, full URLs, or query strings;
  - maps `401` and `403` to `ProviderAuthenticationError`;
  - maps `404` to `SymbolNotFoundError`;
  - maps `429` to `ProviderRateLimitError`;
  - maps `5xx`, `httpx.TimeoutException`, and other `httpx.TransportError` failures to `ProviderUnavailableError`;
  - maps JSON decode failures, unexpected root status, missing required provider fields, and downstream Pydantic `ValidationError` to `IncompleteMarketDataError`;
  - retries only transient transport/5xx failures up to `max_retries`, with injected no-op sleep in tests.
- **Mirror**: `app/market_data/base.py:10` - use the existing typed provider exceptions.
- **Validate**: `uv run pytest tests/market_data/test_massive.py`

### Task 4: Implement Quote And Batched Snapshot Normalization

- **File**: `app/market_data/massive.py`
- **Action**: UPDATE
- **Implement**:
  - `get_quote(symbol)` should normalize the input symbol, call `/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}`, and map the returned snapshot object to `Quote`.
  - `get_quotes(symbols)` should normalize symbols, call `/v2/snapshot/locale/us/markets/stocks/tickers` with comma-separated `tickers` and `include_otc=false`, preserve requested order, and raise `SymbolNotFoundError` if any requested symbol is absent.
  - Snapshot-to-Quote mapping should prefer `lastTrade.p`, then most recent minute close, then current day close for `last_price`; use `prevDay.c` for `previous_close`; use current `day.o/h/l/v` when present; and derive `as_of` from the most specific provider timestamp available.
  - Leave `bid_price` and `ask_price` unset unless `lastQuote` fields are confidently present in fixtures and validated without assuming an entitlement unavailable on Stocks Starter.
- **Mirror**: `app/market_data/schemas.py:89` - return provider-neutral `Quote` objects only.
- **Validate**: `uv run pytest tests/market_data/test_massive.py tests/market_data/test_base.py`

### Task 5: Implement Daily Candle Normalization

- **File**: `app/market_data/massive.py`
- **Action**: UPDATE
- **Implement**:
  - `get_daily_candles(symbol, start_date, end_date)` should validate `start_date <= end_date`, normalize the symbol, and call `/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}` with `adjusted=true`, `sort=asc`, and `limit=50000`.
  - Map aggregate results `o`, `h`, `l`, `c`, `v`, `vw`, `n`, and `t` into `DailyCandle`, converting provider numeric values through `Decimal(str(value))`.
  - Convert provider Unix timestamps into timezone-aware datetimes, compute exchange-local `session_date`, preserve the response-level `adjusted` flag, and return an empty tuple for valid empty result sets.
- **Mirror**: `app/market_data/schemas.py:149` - enforce timezone-aware daily candle validation through the schema.
- **Validate**: `uv run pytest tests/market_data/test_massive.py tests/market_data/test_schemas.py`

### Task 6: Implement Ticker Reference Method Required By Protocol

- **File**: `app/market_data/massive.py`
- **Action**: UPDATE
- **Implement**:
  - `get_ticker_reference(symbol)` should call `/v3/reference/tickers/{symbol}` and map the `results` object to `TickerReference`.
  - Map Massive `market`/`type` values into `AssetType` conservatively, using `UNKNOWN` when uncertain.
  - Use `active`, `market == "otc"`, `primary_exchange`, `market_cap`, `ticker`, and `name` from the provider result.
  - Set `average_daily_volume=None` unless the provider result includes a reliable average-volume field; later liquidity stories can combine reference data with candles/snapshots.
  - Normalize common currency values such as `usd` to `USD`, and treat missing required reference fields as `IncompleteMarketDataError`.
- **Mirror**: `app/market_data/base.py:59` - a concrete provider must implement the full protocol, even though STORY-004 focuses on quote and candle fetching.
- **Validate**: `uv run pytest tests/market_data/test_massive.py`

### Task 7: Export The Adapter

- **File**: `app/market_data/__init__.py`
- **Action**: UPDATE
- **Implement**: Export `MassiveMarketDataProvider` in `__all__`. Keep shared schemas and exceptions provider-neutral; do not export provider payload helper functions.
- **Mirror**: `app/market_data/__init__.py:3` - package exports currently gather public market-data contracts in one place.
- **Validate**: `uv run mypy .`

### Task 8: Add Fixture Payloads

- **File**: `tests/fixtures/market_data/*.json`
- **Action**: CREATE
- **Implement**: Add compact Massive-shaped JSON fixtures for:
  - single ticker snapshot with `ticker`, `day`, `prevDay`, optional `min`, optional `lastTrade`, and `updated`;
  - full market snapshot with a `tickers` array for `AAPL` and `MSFT`;
  - daily aggregates with response-level `adjusted=true` and at least two `results` bars;
  - ticker overview with `results.active`, `results.market`, `results.market_cap`, `results.name`, `results.primary_exchange`, `results.ticker`, and `results.currency_name`.
- **Mirror**: `.agents/stories/nookscout-technical-setup-discovery.stories.md:189` - fixture payloads belong in `tests/fixtures/`.
- **Validate**: `uv run pytest tests/market_data/test_massive.py`

### Task 9: Add Adapter Tests With Mocked HTTP

- **File**: `tests/market_data/test_massive.py`
- **Action**: CREATE
- **Implement**: Use `httpx.MockTransport` and fixture loaders to cover:
  - `MassiveMarketDataProvider` satisfies `MarketDataProvider`;
  - `capabilities()` reports delayed snapshot/candle/reference support;
  - `get_quote()` returns a normalized `Quote`;
  - `get_quotes()` returns quotes in requested order and reports missing symbols;
  - `get_daily_candles()` returns normalized daily candles and empty tuples for valid no-result responses;
  - `get_ticker_reference()` returns normalized reference data;
  - missing API key maps to `ProviderAuthenticationError` before any request;
  - `401/403`, `404`, `429`, `5xx`, transport failures, malformed JSON, and missing required provider fields map to the intended typed exceptions;
  - logs include operation and symbol context but do not include the fake API key, `Authorization`, `apiKey`, or full secret-bearing URLs;
  - no test performs a live network request.
- **Mirror**: `tests/market_data/test_base.py:122` - prove protocol behavior with deterministic provider tests.
- **Validate**: `uv run pytest tests/market_data/test_massive.py`

### Task 10: Final Backend Validation

- **File**: N/A
- **Action**: VERIFY
- **Implement**: Run the full backend validation suite and inspect failures before reporting completion.
- **Mirror**: `README.md:37` - backend validation command list.
- **Validate**:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

---

## Provider Endpoint Mapping

| Provider Method | Massive Endpoint | Normalized Return |
|-----------------|------------------|-------------------|
| `get_quote(symbol)` | `GET /v2/snapshot/locale/us/markets/stocks/tickers/{stocksTicker}` | `Quote` |
| `get_quotes(symbols)` | `GET /v2/snapshot/locale/us/markets/stocks/tickers?tickers=AAPL,MSFT&include_otc=false` | `tuple[Quote, ...]` |
| `get_daily_candles(symbol, start_date, end_date)` | `GET /v2/aggs/ticker/{stocksTicker}/range/1/day/{from}/{to}` | `tuple[DailyCandle, ...]` |
| `get_ticker_reference(symbol)` | `GET /v3/reference/tickers/{ticker}` | `TickerReference` |

---

## Risks And Mitigations

| Risk | Mitigation |
|------|------------|
| Runtime code imports `httpx` while it remains dev-only. | Move `httpx` into project dependencies and refresh `uv.lock`. |
| API keys leak through query params, logs, exception messages, or test failures. | Authenticate with `Authorization`, log only endpoint paths and status/context, and add caplog assertions for redaction. |
| Snapshot fields vary by plan entitlement, especially `lastQuote` and `lastTrade`. | Build quote mapping from fields expected on Stocks Starter snapshots (`day`, `prevDay`, `min`) and treat trade/quote fields as optional enhancements. |
| Provider timestamp units are inconsistent across snapshot and aggregate payloads. | Add a small timestamp parsing helper with tests for millisecond aggregate times and snapshot `updated`/bar timestamps. |
| Massive response shapes leak into scoring, persistence, or API modules. | Keep all raw payload parsing in `app/market_data/massive.py` and test only normalized `Quote`, `DailyCandle`, and `TickerReference` outputs outside fixtures. |
| Retries make tests slow or flaky. | Inject sleep/backoff and use `max_retries=0` or no-op sleep in tests. |
| Batch quote behavior becomes ambiguous on partial provider results. | Preserve requested order and raise `SymbolNotFoundError` when any requested symbol is missing; leave partial-result semantics for a future ingestion service if needed. |

---

## Validation

Run exact backend commands from `AGENTS.md` / `README.md`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

Focused commands while implementing:

```bash
uv run pytest tests/market_data/test_massive.py
uv run pytest tests/market_data/test_massive.py tests/market_data/test_base.py tests/market_data/test_schemas.py
```

## End-to-End Verification

- [ ] Instantiate `MassiveMarketDataProvider.from_settings(test_settings_with_fake_key)` with a mocked `httpx.Client`.
- [ ] Call `get_quote("aapl")`, `get_quotes(["aapl", "msft"])`, `get_daily_candles("aapl", start, end)`, and `get_ticker_reference("aapl")`.
- [ ] Confirm every method returns provider-neutral Pydantic models and no raw Massive payloads escape the adapter.
- [ ] Confirm failing mocked provider responses raise typed market-data exceptions.
- [ ] Confirm captured logs contain operation/symbol context and no fake secret value, `Authorization`, `apiKey`, or full URL.

## Acceptance Criteria

- [ ] `app/market_data/massive.py` implements a concrete provider adapter using STORY-003 contracts.
- [ ] Quote, batched quote, daily candle, capabilities, and protocol-required ticker reference methods are implemented.
- [ ] Provider authentication failures, missing tickers, rate limits, provider unavailability, malformed payloads, and incomplete data map to typed exceptions.
- [ ] Tests use mocked provider payloads and perform no live-provider requests by default.
- [ ] Provider logs include ticker and operation context without API keys, authorization headers, or full secret-bearing URLs.
- [ ] Relevant fixture payloads live under `tests/fixtures/market_data/`.
- [ ] Runtime dependencies and lockfile are consistent.
- [ ] Validation commands pass.
- [ ] Implementation follows `AGENTS.md`.

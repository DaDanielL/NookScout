# Plan: STORY-003 Market Data Contracts and Normalized Schemas

## Summary

Define the provider-neutral market data boundary that later provider adapters, ingestion, indicators, scoring, persistence, and UI code will consume. The implementation should add a dedicated `app/market_data/` package with frozen Pydantic schemas for normalized quotes, daily candles, ticker reference data, data recency, and provider capabilities, plus a typed provider interface in `app/market_data/base.py` that future adapters can implement without leaking Massive/Polygon response shapes into shared modules. Tests should focus on validation behavior and a fake provider that proves downstream code can depend on normalized contracts without live provider calls.

## User Story

As a developer, I want provider-neutral market data contracts, so that provider payloads can be normalized before ingestion, indicators, scoring, or UI code use them.

## Metadata

| Field | Value |
|-------|-------|
| Type | NEW_CAPABILITY |
| Complexity | LOW |
| Systems Affected | Backend market data layer, Pydantic contracts, provider adapter boundary, backend tests |
| GitHub Issue | #3, https://github.com/DaDanielL/NookScout/issues/3 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-003` |

---

## Feature Understanding

**Problem**: Later ingestion, indicator, scoring, persistence, and API code need stable market data inputs, but provider payloads differ and Massive/Polygon should not become the shape of the domain.

**Implementation type**: NEW_CAPABILITY.

**Scope boundary**: Define contracts, validation, and tests only. Do not implement a live provider adapter, scheduler ingestion, persistence models, migrations, scoring logic, indicator calculations, or API endpoints in this story.

---

## Patterns to Follow

### Naming

```text
SOURCE: AGENTS.md:181
Use clear domain names such as Ticker, Candle, IndicatorSnapshot, SetupRun, SetupIdea, SetupScore, and Rationale.
```

```text
SOURCE: AGENTS.md:182
Name provider-specific code after the provider, but keep shared contracts provider-neutral.
```

```text
SOURCE: AGENTS.md:159
app/market_data/base.py is the provider interface for quotes, candles, reference data, and provider capabilities.
```

### Architecture Boundaries

```text
SOURCE: AGENTS.md:101
Market data adapters fetch quotes, daily candles, reference data, and liquidity inputs. Scoring and UI code must not call providers directly.
```

```text
SOURCE: AGENTS.md:201
Access market data only through adapter interfaces.
```

```text
SOURCE: docs/market-data-providers.md:45
The adapter should avoid full tick-level ingestion for MVP. Prefer snapshot, ticker overview, and daily aggregate bars.
```

```text
SOURCE: docs/market-data-providers.md:72
STORY-003 should define provider-neutral schemas for quotes/snapshots, daily candles, reference data, provider capabilities, and data recency.
```

### Types and Validation

```text
SOURCE: app/api/schemas.py:9
Existing API DTOs use Pydantic BaseModel schemas with ConfigDict(frozen=True).
```

```text
SOURCE: app/core/settings.py:52
Validators are explicit class methods and raise ValueError for invalid environment/domain values.
```

```text
SOURCE: AGENTS.md:197
Use timezone-aware datetimes. Market-facing timestamps should preserve exchange context, generally America/New_York for U.S. equities.
```

### Error Handling

```text
SOURCE: AGENTS.md:223
Provider failures should fail gracefully for unavailable providers, rate limits, missing tickers, and incomplete data.
```

```text
SOURCE: docs/market-data-providers.md:76
Provider errors should map to typed unavailable, unauthorized, rate-limited, missing-symbol, and incomplete-data states once product code exists.
```

For this story, keep error handling light: define interface-level exception types or documented failure classes only if they make the provider boundary clearer. Do not implement retry/backoff or HTTP behavior until STORY-004.

### Tests

```text
SOURCE: tests/core/test_settings.py:32
Tests assert valid defaults and explicit invalid cases with pytest and Pydantic ValidationError.
```

```text
SOURCE: tests/api/test_health.py:22
Existing tests check timezone awareness by parsing the response datetime and asserting tzinfo is present.
```

```text
SOURCE: AGENTS.md:241
No live-provider tests in default CI/local validation. Mock provider calls by default to avoid cost, rate limits, and flaky tests.
```

---

## Contracts to Define

Use provider-neutral names and import them from `app.market_data.schemas`.

Recommended model set:

- `DataRecency`: enum or literal values for `real_time`, `delayed`, `end_of_day`, and `unknown`.
- `TickerReference`: normalized ticker metadata for liquidity filtering, including `symbol`, `name`, `asset_type`, `primary_exchange`, `currency`, `is_active`, `is_otc`, `market_cap`, `average_daily_volume`, and provider metadata such as `provider` and `as_of`.
- `Quote`: normalized current-price/snapshot data, including `symbol`, `last_price`, optional `bid_price`, optional `ask_price`, optional `day_open`, `day_high`, `day_low`, `previous_close`, optional `day_volume`, `as_of`, `provider`, and `data_recency`.
- `DailyCandle`: normalized daily OHLCV candle, including `symbol`, `session_date`, timezone-aware `timestamp`, `open`, `high`, `low`, `close`, `volume`, optional `vwap`, optional `trade_count`, `adjusted`, `provider`, and `data_recency`.
- `ProviderCapabilities`: provider-neutral capability metadata such as provider name, support for quotes, snapshots, daily candles, reference data, adjusted bars, supported recency, delayed minutes, max history years, and warnings.
- Shared ticker and timestamp validators that normalize symbols to uppercase, reject invalid symbols, and reject or normalize naive timestamps.

Recommended interface in `app.market_data.base`:

- `MarketDataProvider` protocol or abstract base with `provider_name`, `capabilities()`, `get_quote(symbol)`, `get_quotes(symbols)`, `get_daily_candles(symbol, start_date, end_date)`, and `get_ticker_reference(symbol)`.
- Prefer `collections.abc.Sequence` for multi-symbol inputs and standard `datetime.date` for date ranges.
- Keep the interface synchronous unless implementation discovers a strong reason to make all future adapters async. The existing scheduler and tests are synchronous, and STORY-004 can wrap HTTP client details behind this interface.

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `app/market_data/__init__.py` | CREATE | Mark the market data package and optionally re-export stable contracts. |
| `app/market_data/schemas.py` | CREATE | Define provider-neutral Pydantic schemas, enums/literals, and validators for symbols, quotes, candles, reference data, and capabilities. |
| `app/market_data/base.py` | CREATE | Define the provider interface and, if useful, typed market-data exception classes for future adapters. |
| `tests/market_data/test_schemas.py` | CREATE | Cover valid payloads, missing required fields, invalid symbols, numeric constraints, OHLC consistency, and timezone-aware candle timestamps. |
| `tests/market_data/test_base.py` | CREATE | Use a fake provider to verify the interface returns normalized schemas and capabilities without live-provider calls. |

No database migration, API route, settings, provider adapter, or frontend file is needed for this story.

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: Create the Market Data Package

- **File**: `app/market_data/__init__.py`
- **Action**: CREATE
- **Implement**: Add a minimal package initializer. Re-export only stable public contracts if doing so stays tidy; avoid importing provider-specific modules because none should exist in this story.
- **Mirror**: `app/persistence/base.py:1` - keep package/module skeletons small and purpose-specific.
- **Validate**: `uv run pytest tests/market_data`

### Task 2: Define Provider-Neutral Schemas and Validators

- **File**: `app/market_data/schemas.py`
- **Action**: CREATE
- **Implement**: Add frozen Pydantic models for `Quote`, `DailyCandle`, `TickerReference`, and `ProviderCapabilities`. Add `DataRecency` and asset/type/market enums or literals as needed. Use `Decimal` for price-like fields, `int` for volumes/counts, `date` for market sessions, and timezone-aware `datetime` for provider/exchange timestamps. Add validators that:
  - strip and uppercase ticker symbols;
  - allow common U.S. ticker forms such as `AAPL`, `SPY`, `BRK.B`, and `BRK-B`;
  - reject empty symbols, symbols with spaces, unsupported punctuation, or excessive length;
  - reject missing required quote/candle/reference fields through Pydantic required fields;
  - require non-negative volume and positive prices where appropriate;
  - require `high >= open/close/low` and `low <= open/close/high` for candles;
  - reject naive datetimes and normalize aware market-facing timestamps to `America/New_York` unless preserving the incoming timezone is intentionally documented.
- **Mirror**: `app/api/schemas.py:9` - use Pydantic `BaseModel` contracts with `ConfigDict(frozen=True)`.
- **Validate**: `uv run pytest tests/market_data/test_schemas.py`

### Task 3: Define the Provider Interface

- **File**: `app/market_data/base.py`
- **Action**: CREATE
- **Implement**: Define a provider-neutral `MarketDataProvider` protocol or abstract base class that returns only the schemas from `app.market_data.schemas`. Include methods for one quote, multiple quotes, daily candles by symbol/date range, ticker reference data, and capabilities. Add lightweight typed exceptions such as `MarketDataError`, `ProviderUnavailableError`, `ProviderAuthenticationError`, `ProviderRateLimitError`, `SymbolNotFoundError`, and `IncompleteMarketDataError` only if they are used by the interface/tests or clearly documented for STORY-004. Keep provider payload parsing, HTTP clients, API keys, retries, and provider-specific naming out of this file.
- **Mirror**: `AGENTS.md:201` - all market data access should go through adapter interfaces.
- **Validate**: `uv run pytest tests/market_data/test_base.py`

### Task 4: Add Schema Validation Tests

- **File**: `tests/market_data/test_schemas.py`
- **Action**: CREATE
- **Implement**: Add pytest coverage for:
  - valid quote, daily candle, ticker reference, and capability payloads;
  - symbol normalization from lowercase to uppercase;
  - valid symbols containing dot or hyphen share-class separators;
  - invalid empty symbols, symbols with spaces, unsupported punctuation, and too-long symbols;
  - missing required fields raising `pydantic.ValidationError`;
  - naive candle timestamps raising `ValidationError`;
  - aware UTC candle timestamps normalizing to `America/New_York` or preserving explicit documented exchange context;
  - invalid OHLC relationships raising `ValidationError`;
  - negative volume, zero/negative prices, and invalid delayed-minute metadata raising `ValidationError`.
- **Mirror**: `tests/core/test_settings.py:72` - invalid domain values should raise `ValidationError`.
- **Validate**: `uv run pytest tests/market_data/test_schemas.py`

### Task 5: Add Provider Boundary Tests with a Fake Provider

- **File**: `tests/market_data/test_base.py`
- **Action**: CREATE
- **Implement**: Add a small fake provider that implements the interface and returns normalized Pydantic objects. Assert that capabilities, quote retrieval, daily candle retrieval, and reference retrieval work without provider-specific payload shapes or network calls. If using `Protocol`, make it `@runtime_checkable` only if runtime `isinstance` coverage is valuable; otherwise test the fake through normal method calls and let mypy verify structural typing.
- **Mirror**: `tests/conftest.py:13` - keep tests deterministic and independent of local `.env` or provider credentials.
- **Validate**: `uv run pytest tests/market_data/test_base.py`

### Task 6: Run Backend Validation and Adjust the Plan Only if Needed

- **File**: planned files
- **Action**: VERIFY
- **Implement**: After implementation, run focused tests first, then full backend validation. Fix any lint, format, type, or test failures in the implementation. Do not add live-provider tests or network-dependent checks.
- **Mirror**: `AGENTS.md:243` - backend validation commands must pass before reporting work complete once the scaffold exists.
- **Validate**: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, `uv run pytest`

---

## Existing Behavior to Preserve

- `create_app()` must continue to avoid external provider calls or database connections on import, following `app/main.py:9`.
- `/health` must keep returning only non-secret operational metadata, following `app/api/routes/health.py:15`.
- Settings must remain local-first and optional-provider-key friendly, following `app/core/settings.py:14`.
- Tests must remain deterministic and independent of local `.env` files, following `tests/conftest.py:13`.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Market data schemas accidentally mirror Massive/Polygon payload names. | Use domain names such as `Quote`, `DailyCandle`, `TickerReference`, and `ProviderCapabilities`; keep provider-specific response shapes for STORY-004 adapter modules. |
| Ticker validation is too strict for common U.S. share-class symbols. | Include tests for `BRK.B` and `BRK-B`, document accepted symbols, and avoid overfitting to one provider. |
| Timezone normalization becomes ambiguous for daily candles. | Require timezone-aware timestamps, include `session_date`, and normalize market-facing timestamps to `America/New_York` unless the implementation explicitly documents preserving the original exchange timezone. |
| Interfaces over-specify future adapter behavior. | Keep methods to the story acceptance criteria: quotes, daily candles, reference data, and capabilities. Leave pagination, retries, authentication, and batching strategies to STORY-004. |
| Decimal validation adds Pydantic/mypy friction. | Keep models simple, write tests around parsed values, and prefer Pydantic-supported `Field(gt=0)`/`Field(ge=0)` constraints. |

---

## Validation

Run focused checks while implementing:

```bash
uv run pytest tests/market_data
```

Run full backend validation before reporting completion:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

Frontend validation is not applicable because this story does not scaffold or modify the frontend.

## End-to-End Verification

- [ ] A fake provider can return a `Quote`, `DailyCandle` list, `TickerReference`, and `ProviderCapabilities` through `MarketDataProvider` without any live provider calls.
- [ ] Invalid provider-normalized data fails fast with Pydantic `ValidationError`.
- [ ] Naive market timestamps are rejected and aware candle timestamps preserve or normalize exchange context as documented.
- [ ] No Massive/Polygon payload field names are required by shared schemas, indicator code, scoring code, persistence code, or API modules.

## Acceptance Criteria

- [ ] `app/market_data/base.py` defines provider interfaces for quotes, daily candles, reference data, and provider capabilities.
- [ ] Pydantic schemas validate ticker symbols, quote fields, daily OHLCV candles, exchange timestamps, and reference-data attributes needed for liquidity filtering.
- [ ] Provider-specific response shapes are isolated outside shared scoring, indicator, persistence, and API modules.
- [ ] Unit tests cover schema validation for valid payloads, missing required fields, invalid ticker symbols, and timezone-aware candle timestamps.
- [ ] Relevant tests are added and pass without live-provider calls.
- [ ] Full backend validation passes.
- [ ] Implementation follows `AGENTS.md`.

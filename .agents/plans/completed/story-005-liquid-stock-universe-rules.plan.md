# Plan: Liquid Stock Universe Rules

## Summary

Implement configurable liquid-stock universe filtering for Scout Mode by adding a provider-neutral liquidity evaluator, a small universe service that gathers normalized market-data contracts, and an API endpoint that returns eligible and ineligible configured universe symbols with exclusion reasons. The evaluator will use `Quote`, `TickerReference`, and `DailyCandle` inputs only, keeping provider JSON isolated in adapters. The story also creates `docs/scoring-methodology.md` as the canonical MVP documentation for recommendation decision rules, including liquidity filtering and the future scoring/setup rules that directly determine what is recommended to users. Persistence of universe snapshots is intentionally deferred until the market-data cache story exists; reproducibility for this story comes from response metadata, rule values, candidate symbols, documentation, and deterministic tests.

## User Story

As a beginner swing trader, I want Scout Mode to scan only liquid U.S.-listed stocks, so that the setup list avoids beginner-unfriendly illiquid or OTC names.

## Metadata

| Field | Value |
|-------|-------|
| Type | NEW_CAPABILITY |
| Complexity | MEDIUM |
| Systems Affected | Settings, market data domain, API routes, documentation, tests, environment template |
| GitHub Issue | #5, https://github.com/DaDanielL/NookScout/issues/5 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-005` |

---

## Patterns to Follow

### Naming

```text
SOURCE: app/market_data/schemas.py:89
Market-data contracts use clear domain names like Quote, DailyCandle, TickerReference,
and ProviderCapabilities. Use similarly explicit names such as LiquidityRules,
LiquidityEvaluation, UniverseSymbolResult, and UniverseEvaluation.
```

```text
SOURCE: AGENTS.md:182
Use clear domain names: Watchlist, Ticker, Candle, IndicatorSnapshot, SetupRun,
SetupIdea, SetupScore, Rationale.
```

### Settings

```text
SOURCE: app/core/settings.py:14
Settings are Pydantic Settings fields with explicit validation_alias names and
safe defaults. Add universe/liquidity settings here and test them with _env_file=None.
```

```text
SOURCE: tests/conftest.py:13
Tests construct deterministic Settings via build_test_settings and avoid reading local .env.
Update this fixture for new required settings.
```

### API

```text
SOURCE: app/main.py:9
create_app accepts optional Settings, stores them on application.state, and includes api_router.
```

```text
SOURCE: app/api/routes/health.py:15
Routes use FastAPI response_model DTOs, Annotated dependencies, and return frozen Pydantic responses.
```

```text
SOURCE: app/api/router.py:7
New route modules are included through api_router.include_router(...).
```

### Market Data Boundary

```text
SOURCE: app/market_data/base.py:35
MarketDataProvider is the protocol boundary. Universe filtering should depend on
get_quote(s), get_daily_candles, and get_ticker_reference, not Massive payloads.
```

```text
SOURCE: app/market_data/schemas.py:205
TickerReference already carries symbol, name, asset_type, primary_exchange,
currency, active/OTC flags, market_cap, and optional average_daily_volume.
```

```text
SOURCE: app/market_data/massive.py:377
Massive adapter currently sets average_daily_volume=None. The universe service must
fall back to normalized daily candles for average-volume calculations when reference
average volume is absent.
```

### Error Handling

```text
SOURCE: app/market_data/base.py:10
Provider failures use typed exceptions: ProviderUnavailableError, ProviderAuthenticationError,
ProviderRateLimitError, SymbolNotFoundError, and IncompleteMarketDataError.
```

```text
SOURCE: app/market_data/massive.py:258
Provider unavailable/auth/rate-limit responses are mapped to typed exceptions.
The API endpoint should translate systemic provider errors to HTTP errors, while
symbol-level missing or incomplete data can become ineligible results with reasons.
```

### Tests

```text
SOURCE: tests/market_data/test_schemas.py:21
Tests use payload helper functions with overrides for focused validation cases.
Mirror this style for liquidity inputs and rule variations.
```

```text
SOURCE: tests/market_data/test_base.py:26
FakeMarketDataProvider proves behavior without live provider calls. Add fake providers
for universe service tests instead of using Massive or network access.
```

```text
SOURCE: tests/api/test_health.py:11
API tests use TestClient against create_app(test_settings) and assert response fields
without secrets.
```

### Documentation

```text
SOURCE: AGENTS.md:171
docs/scoring-methodology.md is the human-readable explanation of scoring rules
and indicator interpretation. Use it as the canonical document for recommendation
decision rules that determine ticker/setup recommendations.
```

```text
SOURCE: docs/market-data-providers.md:41
Provider docs should retain provider constraints, data freshness, licensing, and
adapter notes. Cross-reference scoring-methodology.md only when provider constraints
affect recommendation rules.
```

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `app/core/settings.py` | UPDATE | Add configurable predefined universe symbols and liquidity thresholds. |
| `.env.example` | UPDATE | Document new non-secret universe and liquidity settings. |
| `docs/scoring-methodology.md` | CREATE | Document MVP recommendation decision rules, starting with ticker eligibility and liquidity filtering. |
| `docs/market-data-providers.md` | UPDATE | Cross-reference scoring methodology for recommendation-impacting provider constraints. |
| `README.md` | UPDATE | Point users/developers to scoring methodology as the canonical recommendation-rules document. |
| `app/market_data/liquidity.py` | CREATE | Define liquidity rule models, exclusion reasons, and pure evaluator logic. |
| `app/market_data/universe.py` | CREATE | Add service that fetches normalized contracts from `MarketDataProvider` and evaluates configured symbols. |
| `app/market_data/__init__.py` | UPDATE | Export new liquidity/universe models used by API/tests. |
| `app/api/dependencies.py` | UPDATE | Add market-data provider dependency with settings-based Massive factory and test override support. |
| `app/api/schemas.py` | UPDATE | Add API DTOs for liquidity rules, symbol results, and universe response. |
| `app/api/routes/universe.py` | CREATE | Add predefined universe endpoint returning eligible and ineligible results. |
| `app/api/router.py` | UPDATE | Include the universe route. |
| `tests/core/test_settings.py` | UPDATE | Cover parsing and defaults for new settings. |
| `tests/conftest.py` | UPDATE | Add deterministic universe/liquidity settings to fixtures. |
| `tests/market_data/test_liquidity.py` | CREATE | Unit test rule evaluation and exclusion reasons. |
| `tests/market_data/test_universe.py` | CREATE | Unit test universe service provider interactions and missing-data handling. |
| `tests/api/test_universe.py` | CREATE | API tests for response shape and provider dependency override. |

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: Add Universe and Liquidity Configuration

- **File**: `app/core/settings.py`
- **Action**: UPDATE
- **Implement**:
  - Add `predefined_universe_symbols: tuple[str, ...]` with validation alias `NOOKSCOUT_PREDEFINED_UNIVERSE_SYMBOLS`.
  - Add liquidity threshold settings:
    - `NOOKSCOUT_LIQUIDITY_MIN_PRICE`, default `5`
    - `NOOKSCOUT_LIQUIDITY_MIN_AVERAGE_DAILY_VOLUME`, default `1000000`
    - `NOOKSCOUT_LIQUIDITY_MIN_DOLLAR_VOLUME`, default `20000000`
    - `NOOKSCOUT_LIQUIDITY_MIN_MARKET_CAP`, default `1000000000`
    - `NOOKSCOUT_LIQUIDITY_ALLOWED_EXCHANGES`, default covering common U.S. primary exchange labels/MICs used by fixtures and Massive, e.g. `XNAS`, `XNYS`, `NASDAQ`, `NYSE`
    - `NOOKSCOUT_LIQUIDITY_AVERAGE_VOLUME_LOOKBACK_DAYS`, default `90`
  - Use `Decimal` for money/price thresholds and positive integer constraints for volume/lookback.
  - Add validators to parse comma-separated symbol and exchange env vars, normalize symbols via `normalize_symbol`, strip blanks, and de-duplicate while preserving order.
  - Prefer an empty tuple default for symbols so the user controls the local predefined universe without hard-coding one-off ticker lists into scoring/domain code.
- **Mirror**: `app/core/settings.py:14` - settings field style and validators.
- **Validate**: `uv run pytest tests/core/test_settings.py`

### Task 2: Document New Environment Settings

- **File**: `.env.example`
- **Action**: UPDATE
- **Implement**:
  - Add placeholders for predefined universe symbols and liquidity rule thresholds.
  - Keep values non-secret.
  - Note delayed Massive provider settings remain separate from liquidity configuration.
- **Mirror**: `.env.example` existing provider and runtime variable sections.
- **Validate**: `uv run ruff format --check .`

### Task 3: Create Recommendation Decision Rules Documentation

- **File**: `docs/scoring-methodology.md`
- **Action**: CREATE
- **Implement**:
  - Create this as the canonical MVP document for rules that determine what NookScout recommends or suppresses.
  - Add sections for:
    - purpose and scope: documents recommendation decision rules, not brokerage/trading advice
    - current MVP implementation status
    - ticker eligibility and predefined universe source
    - liquidity filter rules and defaults
    - average-volume and dollar-volume calculations
    - missing-data and exclusion behavior
    - provider freshness and provider constraints that affect recommendations
    - future indicator methodology
    - future trend/setup classification
    - future scoring, ranking, tie-breaking, confidence, no-clear-setup, entry, invalidation, target, and risk/reward rules
    - versioning/review notes
  - Mark liquidity/universe filtering as implemented by STORY-005 once this story is complete.
  - Mark later setup recommendation sections as "planned, not implemented in STORY-005" so the document is useful now without pretending future scoring exists.
  - Include the MVP default liquidity rules from the PRD: price above `$5`, average volume above `1M`, dollar volume default `$20M`, market cap above `$1B`, allowed U.S. listing venues, and OTC exclusion.
  - Document that the Massive adapter currently does not supply reliable average daily volume, so MVP derives average volume from normalized daily candles when reference data is absent.
  - Avoid direct buy/sell language and any claim that confidence implies certainty.
- **Mirror**: `AGENTS.md:171` - scoring methodology is the human-readable scoring/rules documentation.
- **Validate**: `uv run ruff format --check .`

### Task 4: Cross-Reference Recommendation Rule Documentation

- **File**: `docs/market-data-providers.md`, `README.md`
- **Action**: UPDATE
- **Implement**:
  - In `docs/market-data-providers.md`, keep provider choice/licensing/freshness details there, but link to `docs/scoring-methodology.md` for how provider data affects recommendation decisions.
  - In `README.md`, add a short documentation pointer that `docs/scoring-methodology.md` is the canonical place to review MVP recommendation decision rules.
  - Do not duplicate liquidity thresholds in multiple documents except where needed as a brief pointer; avoid rule drift.
- **Mirror**: `docs/market-data-providers.md:70` - implementation notes for later stories.
- **Validate**: `uv run ruff format --check .`

### Task 5: Create Pure Liquidity Evaluator

- **File**: `app/market_data/liquidity.py`
- **Action**: CREATE
- **Implement**:
  - Add frozen Pydantic models:
    - `LiquidityRules`
    - `LiquidityInputs`
    - `LiquidityExclusionReason` as `StrEnum`
    - `LiquidityEvaluation`
  - Include exclusion reasons for at least:
    - `missing_reference_data`
    - `inactive_security`
    - `otc_security`
    - `unsupported_asset_type`
    - `unsupported_currency`
    - `unsupported_exchange`
    - `missing_price`
    - `low_price`
    - `missing_average_daily_volume`
    - `low_average_daily_volume`
    - `missing_market_cap`
    - `low_market_cap`
    - `missing_dollar_volume`
    - `low_dollar_volume`
  - Add `LiquidityRules.from_settings(settings: Settings) -> LiquidityRules`.
  - Add `evaluate_liquidity(inputs: LiquidityInputs, rules: LiquidityRules) -> LiquidityEvaluation`.
  - Use `reference.average_daily_volume` when present; otherwise calculate average volume from supplied normalized `DailyCandle.volume` values.
  - Calculate dollar volume as `quote.last_price * average_daily_volume`.
  - Default accepted asset type should be `AssetType.STOCK`; ETFs/ADRs can be added later if product scope changes.
  - Return all applicable exclusion reasons instead of stopping at the first failure.
- **Mirror**: `app/market_data/schemas.py:44` - frozen Pydantic model style and `StrEnum` use.
- **Validate**: `uv run pytest tests/market_data/test_liquidity.py`

### Task 6: Add Liquidity Unit Tests

- **File**: `tests/market_data/test_liquidity.py`
- **Action**: CREATE
- **Implement**:
  - Build helper factories for `Quote`, `TickerReference`, `DailyCandle`, and `LiquidityRules`.
  - Cover accepted liquid stock.
  - Cover low-price exclusion.
  - Cover low-average-volume exclusion using reference average volume.
  - Cover average-volume fallback from candles when reference average is missing.
  - Cover low-dollar-volume exclusion.
  - Cover missing-reference-data behavior.
  - Cover OTC exclusion.
  - Cover unsupported exchange and inactive security if rule/model surface includes them.
- **Mirror**: `tests/market_data/test_schemas.py:21` - payload helpers with overrides and focused assertions.
- **Validate**: `uv run pytest tests/market_data/test_liquidity.py`

### Task 7: Create Universe Evaluation Service

- **File**: `app/market_data/universe.py`
- **Action**: CREATE
- **Implement**:
  - Add frozen Pydantic models:
    - `UniverseSymbolResult`
    - `UniverseEvaluation`
  - Add `evaluate_predefined_universe(provider, symbols, rules, *, as_of, average_volume_lookback_days)`.
  - Normalize and de-duplicate input symbols while preserving configured order.
  - For each symbol:
    - fetch `TickerReference`
    - fetch `Quote`
    - fetch recent daily candles only when reference average volume is missing or when tests explicitly exercise candle fallback
    - evaluate with `evaluate_liquidity`
  - Return eligible and ineligible lists with symbol, name when available, price, average volume, dollar volume, market cap, exchange, provider, data recency, and exclusion reasons.
  - Convert `SymbolNotFoundError` and `IncompleteMarketDataError` during reference/quote fetches into ineligible symbol results with `missing_reference_data` or `missing_price`/`missing_reference_data` as appropriate.
  - Let systemic provider failures such as authentication, rate-limit, and provider-unavailable errors propagate for the API layer to translate into HTTP responses.
- **Mirror**: `app/market_data/base.py:35` - depend on `MarketDataProvider` protocol only.
- **Validate**: `uv run pytest tests/market_data/test_universe.py`

### Task 8: Add Universe Service Tests

- **File**: `tests/market_data/test_universe.py`
- **Action**: CREATE
- **Implement**:
  - Add deterministic fake providers returning normalized contracts.
  - Test that accepted and rejected symbols are both returned with reasons.
  - Test requested/configured order is preserved and duplicate symbols are de-duplicated.
  - Test low-volume, low-dollar-volume, low-price, OTC, and missing-reference-data outcomes at service level.
  - Test candle fallback is used when `TickerReference.average_daily_volume` is `None`.
  - Test systemic provider errors are not swallowed.
- **Mirror**: `tests/market_data/test_base.py:26` - fake provider pattern with normalized contracts.
- **Validate**: `uv run pytest tests/market_data/test_universe.py`

### Task 9: Add Market Data Provider API Dependency

- **File**: `app/api/dependencies.py`
- **Action**: UPDATE
- **Implement**:
  - Add `get_market_data_provider(...)` dependency.
  - Build `MassiveMarketDataProvider.from_settings(settings)` when `settings.market_data_provider == "massive"`.
  - Raise an HTTP 500 or typed configuration error for unsupported provider names.
  - Use a yield dependency or equivalent cleanup so owned Massive clients are closed after the request.
  - Preserve simple test override support through FastAPI dependency overrides.
- **Mirror**: `app/api/dependencies.py:10` - dependency style and settings lookup.
- **Validate**: `uv run pytest tests/api/test_universe.py`

### Task 10: Add Universe API Response DTOs

- **File**: `app/api/schemas.py`
- **Action**: UPDATE
- **Implement**:
  - Add frozen Pydantic DTOs that serialize:
    - applied liquidity rules
    - eligible symbol results
    - ineligible symbol results with exclusion reasons
    - candidate/eligible/ineligible counts
    - `evaluated_at`
  - Use JSON-friendly strings for `Decimal`, enum, and datetime values where FastAPI/Pydantic defaults need help.
  - Do not include secrets, API keys, database URLs, or raw provider payloads.
- **Mirror**: `app/api/schemas.py:9` - frozen response model style.
- **Validate**: `uv run pytest tests/api/test_universe.py`

### Task 11: Add Predefined Universe API Route

- **File**: `app/api/routes/universe.py`
- **Action**: CREATE
- **Implement**:
  - Add `GET /universe/predefined` with `response_model=UniverseResponse`.
  - Read `settings.predefined_universe_symbols` and liquidity rules from settings.
  - Call the universe service with the injected market-data provider.
  - If no symbols are configured, return an empty evaluation with applied rules and zero counts rather than making provider calls.
  - Translate `ProviderAuthenticationError` to HTTP 401, `ProviderRateLimitError` to HTTP 429, and `ProviderUnavailableError` to HTTP 503.
  - Keep response language operational and educational; do not add trading instructions.
- **Mirror**: `app/api/routes/health.py:15` - route decorator, dependency injection, and response construction.
- **Validate**: `uv run pytest tests/api/test_universe.py`

### Task 12: Register Universe Route

- **File**: `app/api/router.py`
- **Action**: UPDATE
- **Implement**:
  - Import `app.api.routes.universe.router`.
  - Include it in `api_router`.
- **Mirror**: `app/api/router.py:7` - router assembly style.
- **Validate**: `uv run pytest tests/api/test_universe.py tests/api/test_health.py`

### Task 13: Add API Tests

- **File**: `tests/api/test_universe.py`
- **Action**: CREATE
- **Implement**:
  - Override the market-data provider dependency with a fake provider.
  - Build settings with configured symbols and thresholds.
  - Assert endpoint returns eligible and ineligible arrays, applied rule values, counts, provider/data recency metadata, and exclusion reasons.
  - Assert empty configured symbols return empty response without provider calls.
  - Assert provider unavailable/rate-limit/auth errors map to expected HTTP statuses.
  - Assert response field names do not expose secret-like fields.
- **Mirror**: `tests/api/test_health.py:11` - TestClient response assertions and secret-field guard.
- **Validate**: `uv run pytest tests/api/test_universe.py`

### Task 14: Export New Market Data Symbols

- **File**: `app/market_data/__init__.py`
- **Action**: UPDATE
- **Implement**:
  - Export public liquidity and universe models/functions that tests and API code import.
  - Keep provider-specific exports separate from provider-neutral exports.
- **Mirror**: existing `app/market_data/__init__.py` export style.
- **Validate**: `uv run mypy .`

### Task 15: Run Full Backend Validation

- **File**: N/A
- **Action**: VALIDATE
- **Implement**:
  - Run focused tests first, then full validation.
  - Fix any lint/type/test failures within the planned scope.
- **Mirror**: `AGENTS.md:248` - backend validation commands.
- **Validate**:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run mypy .`
  - `uv run pytest`

---

## Validation

Run these exact backend commands before reporting implementation complete:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

Useful focused checks during implementation:

```bash
uv run pytest tests/core/test_settings.py
uv run pytest tests/market_data/test_liquidity.py
uv run pytest tests/market_data/test_universe.py
uv run pytest tests/api/test_universe.py
```

## End-to-End Verification

- [ ] Configure `NOOKSCOUT_PREDEFINED_UNIVERSE_SYMBOLS` in test settings or `.env`.
- [ ] Call `GET /universe/predefined` with a fake provider in tests.
- [ ] Confirm response includes applied rules, eligible symbols, ineligible symbols, exclusion reasons, and counts.
- [ ] Confirm `docs/scoring-methodology.md` documents the exact MVP liquidity/universe rules used by the implementation.
- [ ] Confirm README and provider docs link to scoring methodology without duplicating full rule definitions.
- [ ] Confirm no raw provider payloads, API keys, tokens, database URLs, or direct buy/sell language appears in the response.

## Acceptance Criteria

- [ ] Liquidity rules are configurable and cover price, average volume, dollar volume, market cap, listing venue, and OTC/illiquid exclusions.
- [ ] Default rules reflect the PRD ranges: price above `$5`, average volume above `1M`, dollar volume default `$20M`, market cap above `$1B`, and OTC exclusion.
- [ ] API/internal service returns the eligible predefined universe plus exclusion reasons for ineligible tickers.
- [ ] Tests cover accepted names, low-price exclusions, low-volume exclusions, low-dollar-volume exclusions, missing-reference-data behavior, and OTC exclusions.
- [ ] Provider-specific payload shapes remain isolated in provider modules.
- [ ] `docs/scoring-methodology.md` documents recommendation-impacting MVP decision rules and clearly marks future scoring/setup sections as planned.
- [ ] README and provider docs cross-reference `docs/scoring-methodology.md` as the canonical recommendation-rules document.
- [ ] No live-provider tests are added to default validation.
- [ ] Full backend validation passes.

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Massive reference data does not provide average daily volume. | Fall back to normalized daily candles, as already anticipated by the STORY-004 plan. |
| Universe source is not yet persisted. | Configure symbols through settings and return rule/symbol metadata; defer storage to STORY-006. |
| API route could accidentally instantiate live provider in tests. | Use FastAPI dependency overrides and fake providers in all API tests. |
| Hard-coded ticker lists could leak into scoring later. | Keep candidate symbols in settings, not scoring code. |
| Dollar-volume calculation may use stale delayed price. | Include provider/data-recency metadata in results and keep thresholds configurable. |
| Decision-rule docs can drift from code. | Add documentation updates to the same story tasks as rule implementation and keep detailed rule values in `docs/scoring-methodology.md`, with other docs linking back to it. |

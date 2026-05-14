# Plan: Persist Indicator Snapshots and Refresh Pipeline

## Summary

Add the first persisted indicator snapshot pipeline by introducing versioned indicator snapshot contracts, a SQLAlchemy table/repository, and a provider-free refresh service that reads cached daily candles, computes the existing deterministic indicator outputs, and writes reproducible snapshot records. The implementation should keep indicators provider-neutral, store complete and incomplete calculation states, and make the refresh service callable by future Scout Mode and Watchlist Mode setup generation without requiring API or frontend work.

## User Story

As a developer, I want indicator snapshots persisted and refreshed from cached candle data, so that setup runs can be reproduced and old ideas can be interpreted later.

## Metadata

| Field | Value |
|-------|-------|
| Type | NEW_CAPABILITY |
| Complexity | MEDIUM |
| Systems Affected | Backend indicator layer, persistence, Alembic migrations, local job/service layer, backend tests, scoring methodology docs |
| GitHub Issue | #10, https://github.com/DaDanielL/NookScout/issues/10 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-010` |

---

## Patterns to Follow

### Naming

```text
SOURCE: AGENTS.md:194
Project state explicitly includes indicator snapshots. Use the domain name
IndicatorSnapshot consistently, matching existing names like DailyCandleRecord,
QuoteSnapshotRecord, and IngestionRunRecord.
```

```text
SOURCE: app/persistence/models.py:76
Persistence models use explicit Record suffixes, SQLAlchemy 2 Mapped annotations,
table-level indexes/constraints, and created_at/updated_at timestamps where records can
change. Add IndicatorSnapshotRecord in the same style.
```

```text
SOURCE: app/persistence/repositories.py:35
Repository classes are named by domain responsibility and are initialized with a
Session. Add IndicatorSnapshotRepository beside TickerRepository, DailyCandleRepository,
QuoteSnapshotRepository, and IngestionRunRepository.
```

### Boundaries

```text
SOURCE: AGENTS.md:199
Market data access must go through adapter interfaces; indicators, scoring, persistence,
and UI code must not call providers directly. The refresh pipeline must read cached
DailyCandle contracts through repositories only.
```

```text
SOURCE: docs/scoring-methodology.md:353
The indicator layer consumes provider-neutral DailyCandle, Quote, cached benchmark
candles, and future persisted indicator snapshots. Indicator code should not depend on
provider payloads or provider APIs.
```

```text
SOURCE: app/indicators/technical.py:177
Core technical indicators already expose calculate_technical_indicators(candles,
config). The refresh service should compose existing calculation functions rather than
duplicating formula logic.
```

```text
SOURCE: app/indicators/signals.py:336
Support/resistance and relative strength are separate deterministic functions. Persist
their outputs with the core technical snapshot so downstream scoring can reproduce the
full indicator context from one snapshot record.
```

### Types and Serialization

```text
SOURCE: app/market_data/schemas.py:44
Provider-neutral contracts inherit from frozen MarketDataModel. Any new snapshot input,
output, refresh result, or failure contract should use this same Pydantic style.
```

```text
SOURCE: app/market_data/schemas.py:149
DailyCandle is the normalized input contract for daily OHLCV data. The refresh service
should preserve symbol, provider, adjusted status, data_recency, and input date range
from these cached candles.
```

```text
SOURCE: app/indicators/technical.py:157
TechnicalIndicatorSnapshot already contains symbol/provider/adjusted, input range,
available and required candle counts, latest values, recent points, completeness, and
incomplete details. Store this payload directly as versioned JSON instead of re-modeling
every value into separate SQL columns.
```

```text
SOURCE: docs/scoring-methodology.md:392
Persisted indicator snapshots should record calculation version, ticker, provider,
input candle range, adjusted status, benchmark symbols/windows, incomplete-data flags,
and the scoring version that later consumes the snapshot.
```

### Error Handling and Logging

```text
SOURCE: AGENTS.md:221
Prefer typed exceptions for provider, scoring, persistence, and LLM failures. Use
PersistenceError for repository-level invalid operations and small refresh-domain
contracts for per-symbol failures.
```

```text
SOURCE: app/persistence/repositories.py:236
Existing repositories return None or empty tuples for misses and use explicit typed
errors only when updating missing records. Snapshot lookups should follow the same
cache-miss behavior.
```

```text
SOURCE: app/market_data/massive.py:392
Existing logging includes operation, symbol context, path/status, and attempt while
avoiding headers, API keys, and full URLs. Indicator refresh failure logs should include
symbol, provider, calculation date, and calculation version, but no secrets or DB URLs.
```

```text
SOURCE: tests/market_data/test_massive.py:348
No-secret logging has caplog coverage. Add a refresh failure test that asserts useful
calculation context appears while forbidden fragments such as key, token, secret,
password, Authorization, apiKey, and database_url do not.
```

### Tests

```text
SOURCE: tests/persistence/test_repositories.py:33
Persistence tests use an in-memory SQLite engine, Base.metadata.create_all, and a fresh
Session per test. Mirror this for IndicatorSnapshotRepository tests.
```

```text
SOURCE: tests/persistence/test_repositories.py:153
Repository tests build normalized domain contracts, write through repositories, read
through repository APIs, and assert record counts with SQLAlchemy select(func.count()).
```

```text
SOURCE: tests/indicators/test_technical.py:104
Indicator tests assert incomplete states explicitly. Snapshot persistence and refresh
tests should cover incomplete-data details instead of treating incomplete calculations as
errors.
```

```text
SOURCE: tests/jobs/test_scheduler.py:8
The local scheduler currently has only a placeholder smoke test. Do not overbuild
APScheduler registration in this story; keep the refresh service independently callable
and leave scheduler orchestration small unless needed for acceptance criteria.
```

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `app/indicators/snapshots.py` | CREATE | Add version constant and frozen Pydantic contracts for persisted indicator snapshots, snapshot creation input, refresh summaries, and refresh failures. |
| `app/indicators/refresh.py` | CREATE | Add provider-free refresh service/functions that load cached ticker and benchmark candles, compute indicators, persist snapshots, and log per-symbol failures. |
| `app/indicators/__init__.py` | UPDATE | Export snapshot contracts, calculation version, and refresh entrypoints. |
| `app/persistence/models.py` | UPDATE | Add `IndicatorSnapshotRecord` with query indexes, JSON payload columns, input range metadata, completeness flags, and calculation version. |
| `app/persistence/repositories.py` | UPDATE | Add `IndicatorSnapshotRepository`; add a cached-candle recent lookup helper if refresh needs latest-N candles instead of date ranges. |
| `app/persistence/__init__.py` | UPDATE | Export `IndicatorSnapshotRecord` and `IndicatorSnapshotRepository`. |
| `migrations/versions/20260514_0002_indicator_snapshots.py` | CREATE | Add the `indicator_snapshots` table, indexes, and downgrade logic. |
| `tests/persistence/test_indicator_snapshots.py` | CREATE | Cover snapshot creation, latest lookup, versioned lookup, and incomplete-data persistence. |
| `tests/indicators/test_refresh.py` | CREATE | Cover refresh-from-cache behavior, benchmark candle loading, persisted snapshot contents, per-symbol failure summary, and no-secret failure logging. |
| `docs/scoring-methodology.md` | UPDATE | Replace future snapshot wording with implemented persistence/versioning behavior and refresh-pipeline notes. |

---

## Data Model Design

Add `IndicatorSnapshotRecord` in `app/persistence/models.py`.

Recommended table: `indicator_snapshots`

Columns:

- `id: Integer primary key`
- `symbol: String(10), nullable=False`
- `provider: String(50), nullable=False`
- `calculation_date: Date, nullable=False`
- `calculated_at: AwareDateTime, nullable=False`
- `calculation_version: String(80), nullable=False`
- `adjusted: Boolean, nullable=False`
- `data_recency: String(30), nullable=False`
- `input_start_session_date: Date, nullable=True`
- `input_end_session_date: Date, nullable=True`
- `available_candles: Integer, nullable=False`
- `required_candles: Integer, nullable=False`
- `is_complete: Boolean, nullable=False`
- `technical_is_complete: Boolean, nullable=False`
- `support_resistance_is_complete: Boolean, nullable=False`
- `relative_strength_is_complete: Boolean, nullable=False`
- `benchmark_symbols: JSON, nullable=True`
- `relative_strength_lookback_periods: JSON, nullable=True`
- `technical_snapshot: JSON, nullable=False`
- `support_resistance_snapshot: JSON, nullable=False`
- `relative_strength_snapshot: JSON, nullable=False`
- `incomplete_details: JSON, nullable=False`
- `created_at: AwareDateTime default utc_now, nullable=False`

Indexes:

- `ix_indicator_snapshots_symbol_provider_calculation_date` on `(symbol, provider, calculation_date)`
- `ix_indicator_snapshots_symbol_provider_version_date` on `(symbol, provider, calculation_version, calculation_date)`
- `ix_indicator_snapshots_version_calculated_at` on `(calculation_version, calculated_at)`

Do not add a uniqueness constraint for the first implementation. Re-running a refresh with corrected cached candles should create a new snapshot row; repository latest lookup can choose the newest `calculation_date`, then `calculated_at`, then `id`.

Use JSON columns for indicator payloads because the deterministic snapshot contracts already carry nested values, recent windows, support/resistance zones, benchmark comparisons, and incomplete details. Persist with `model_dump(mode="json")` to avoid database-specific Decimal/date serialization issues.

---

## Repository Contract

Add `IndicatorSnapshotRepository` in `app/persistence/repositories.py`.

Suggested methods:

```python
class IndicatorSnapshotRepository:
    def __init__(self, session: Session) -> None: ...

    def create(self, snapshot: IndicatorSnapshotCreate) -> IndicatorSnapshotRecord: ...

    def get_latest(
        self,
        symbol: str,
        *,
        provider: str | None = None,
        adjusted: bool | None = True,
        calculation_version: str | None = None,
    ) -> IndicatorSnapshotRecord | None: ...

    def get_latest_for_version(
        self,
        symbol: str,
        calculation_version: str,
        *,
        provider: str | None = None,
        adjusted: bool | None = True,
    ) -> IndicatorSnapshotRecord | None: ...
```

If the refresh service needs latest-N candles rather than a caller-supplied date range, add this helper to `DailyCandleRepository`:

```python
def get_recent(
    self,
    symbol: str,
    *,
    limit: int,
    provider: str | None = None,
    adjusted: bool = True,
    end_date: date | None = None,
) -> tuple[DailyCandle, ...]: ...
```

Implementation note: query rows descending by `session_date`, limit the result, then return domain `DailyCandle` objects sorted ascending so existing indicator functions receive the same shape as `get_range`.

---

## Refresh Service Design

Create `app/indicators/refresh.py` with a provider-free service. It should depend on repositories, not market-data providers.

Suggested public entrypoint:

```python
def refresh_indicator_snapshots(
    *,
    symbols: Sequence[str],
    candle_repository: DailyCandleRepository,
    snapshot_repository: IndicatorSnapshotRepository,
    calculated_at: datetime,
    provider: str | None = None,
    adjusted: bool = True,
    candle_limit: int = 260,
    calculation_version: str = INDICATOR_CALCULATION_VERSION,
    indicator_config: IndicatorConfig = _DEFAULT_INDICATOR_CONFIG,
    support_resistance_config: SupportResistanceConfig = _DEFAULT_SUPPORT_RESISTANCE_CONFIG,
    relative_strength_config: RelativeStrengthConfig = _DEFAULT_RELATIVE_STRENGTH_CONFIG,
) -> IndicatorRefreshSummary:
    ...
```

Expected behavior:

- Normalize and de-duplicate requested symbols while preserving order.
- Load recent cached candles for each requested ticker via `DailyCandleRepository`.
- Load recent cached benchmark candles for `RelativeStrengthConfig.benchmark_symbols`.
- Call `calculate_technical_indicators`, `calculate_support_resistance`, and `calculate_relative_strength`.
- Build one `IndicatorSnapshotCreate` per symbol and persist it with `IndicatorSnapshotRepository.create`.
- Return a typed `IndicatorRefreshSummary` with requested symbols, succeeded count, failed count, created snapshot ids, and failure details.
- Catch per-symbol calculation or persistence failures, log them with ticker/calculation context, and continue with the next symbol.
- Do not call `session.commit()` inside the service; match repository patterns where callers own transaction boundaries.
- Do not call any `MarketDataProvider` methods.

Relative strength note: when benchmark candles are missing, call `calculate_relative_strength` with an empty or partial benchmark mapping so the snapshot records explicit incomplete benchmark details rather than failing the whole ticker.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| JSON payloads drift from Pydantic snapshot contracts | Always serialize with `model_dump(mode="json")`; add tests that read back nested latest values and incomplete details. |
| Refresh service accidentally becomes a provider boundary | Constructor/function accepts repositories only; tests use cached DB candles and assert no fake provider object is involved. |
| Relative strength requires benchmark data that may not exist locally | Treat missing benchmarks as an incomplete snapshot state through `calculate_relative_strength`, not as a refresh failure. |
| Re-running refresh overwrites reproducibility evidence | Insert a new snapshot record instead of upserting; latest lookup resolves the newest row deterministically. |
| Too many candles or too few candles affect indicator completeness | Default `candle_limit` to a conservative value such as 260 and preserve `available_candles`, `required_candles`, and incomplete details in the record. |
| Logs leak secrets or connection details | Log only symbol, provider, calculation date/version, and exception class/message; add caplog assertions for forbidden fragments. |
| SQLite JSON behavior differs from PostgreSQL | Keep JSON payload assertions simple and use SQLAlchemy JSON columns already used by ingestion runs; avoid dialect-specific JSON queries. |

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: Add Persisted Snapshot Domain Contracts

- **File**: `app/indicators/snapshots.py`
- **Action**: CREATE
- **Implement**: Add `INDICATOR_CALCULATION_VERSION`, `IndicatorSnapshotCreate`, `IndicatorSnapshot`, `IndicatorRefreshFailure`, and `IndicatorRefreshSummary` as frozen Pydantic/`MarketDataModel` contracts. Include validators for symbol normalization, non-empty calculation version, non-negative counts, and timezone-aware `calculated_at`.
- **Mirror**: `app/market_data/schemas.py:44` - frozen provider-neutral Pydantic contracts.
- **Validate**: `uv run mypy .`

### Task 2: Add Indicator Snapshot Persistence Model

- **File**: `app/persistence/models.py`
- **Action**: UPDATE
- **Implement**: Add `IndicatorSnapshotRecord` with the data model above. Use `AwareDateTime`, `JSON`, `Date`, `String`, `Integer`, `Boolean`, indexes, and `created_at`. Export it in `__all__`.
- **Mirror**: `app/persistence/models.py:121` - snapshot-style record with symbol/provider metadata and indexed lookup fields.
- **Validate**: `uv run ruff check .`

### Task 3: Add Indicator Snapshot Migration

- **File**: `migrations/versions/20260514_0002_indicator_snapshots.py`
- **Action**: CREATE
- **Implement**: Create the `indicator_snapshots` table and indexes in `upgrade()`. Drop indexes and the table in reverse order in `downgrade()`. Set `down_revision = "20260512_0001"`.
- **Mirror**: `migrations/versions/20260512_0001_market_data_cache_ingestion_runs.py:19` - explicit Alembic table/index creation and downgrade logic.
- **Validate**: `uv run ruff check .`

### Task 4: Add Repository Methods

- **File**: `app/persistence/repositories.py`
- **Action**: UPDATE
- **Implement**: Add `IndicatorSnapshotRepository.create`, `get_latest`, and `get_latest_for_version`. Add `DailyCandleRepository.get_recent` if needed by the refresh service. Normalize symbols/providers, flush after create, return `None` for cache misses, and sort latest records by `calculation_date`, `calculated_at`, and `id` descending.
- **Mirror**: `app/persistence/repositories.py:137` - cached candle reads return ordered domain contracts; `app/persistence/repositories.py:210` - latest snapshot lookup ordering.
- **Validate**: `uv run mypy .`

### Task 5: Export New Persistence and Indicator APIs

- **File**: `app/persistence/__init__.py`, `app/indicators/__init__.py`
- **Action**: UPDATE
- **Implement**: Export `IndicatorSnapshotRecord`, `IndicatorSnapshotRepository`, snapshot contracts, calculation version, and refresh entrypoint so future setup generation can import them through package public APIs.
- **Mirror**: `app/indicators/__init__.py:1` and `app/persistence/__init__.py:1` - explicit package exports.
- **Validate**: `uv run ruff check .`

### Task 6: Add Snapshot Repository Tests

- **File**: `tests/persistence/test_indicator_snapshots.py`
- **Action**: CREATE
- **Implement**: Add in-memory SQLite tests for snapshot creation, latest lookup across dates/runs, version-filtered latest lookup, provider/adjusted filters, and incomplete-data JSON persistence. Use compact helper builders for `IndicatorSnapshotCreate`.
- **Mirror**: `tests/persistence/test_repositories.py:33` - fresh SQLite metadata/session fixture; `tests/persistence/test_repositories.py:198` - latest lookup assertions.
- **Validate**: `uv run pytest tests/persistence/test_indicator_snapshots.py`

### Task 7: Add Refresh Service

- **File**: `app/indicators/refresh.py`
- **Action**: CREATE
- **Implement**: Add `refresh_indicator_snapshots(...)` that composes cached candle reads, existing indicator calculations, snapshot contract construction, repository persistence, and per-symbol failure logging. Keep transaction ownership outside the service and make missing benchmark candles an incomplete relative-strength state.
- **Mirror**: `app/market_data/universe.py:98` - service-style orchestration over normalized inputs; `app/indicators/technical.py:177` and `app/indicators/signals.py:336` - deterministic calculation entrypoints.
- **Validate**: `uv run mypy .`

### Task 8: Add Refresh Service Tests

- **File**: `tests/indicators/test_refresh.py`
- **Action**: CREATE
- **Implement**: Seed cached ticker and benchmark candles through `DailyCandleRepository`, run refresh with compact configs, assert one snapshot record is created with expected calculation version/range/completeness/payload sections, assert missing benchmark data becomes incomplete state, and assert per-symbol failures are logged without secrets.
- **Mirror**: `tests/indicators/test_technical.py:104` - explicit incomplete-state assertions; `tests/market_data/test_massive.py:348` - caplog no-secret logging assertions.
- **Validate**: `uv run pytest tests/indicators/test_refresh.py`

### Task 9: Update Scoring Methodology Documentation

- **File**: `docs/scoring-methodology.md`
- **Action**: UPDATE
- **Implement**: Change future snapshot wording to current implemented behavior. Document the calculation version string, persisted metadata, payload sections, incomplete-state behavior, and provider-free refresh boundary.
- **Mirror**: `docs/scoring-methodology.md:392` - existing future snapshot requirements.
- **Validate**: `rg -n "indicator snapshot|calculation version|provider-free|incomplete" docs/scoring-methodology.md`

### Task 10: Run Full Backend Validation

- **File**: N/A
- **Action**: VERIFY
- **Implement**: Run the full backend validation suite and fix only issues directly related to this implementation.
- **Mirror**: `AGENTS.md:243` - project validation commands.
- **Validate**:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

---

## Validation

Run these exact commands before reporting implementation complete:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

Focused checks during implementation:

```bash
uv run pytest tests/persistence/test_indicator_snapshots.py
uv run pytest tests/indicators/test_refresh.py
rg -n "indicator snapshot|calculation version|provider-free|incomplete" docs/scoring-methodology.md
```

## End-to-End Verification

- [ ] Seed cached daily candles for a ticker plus `SPY`/`QQQ` benchmark symbols through `DailyCandleRepository`.
- [ ] Run `refresh_indicator_snapshots(...)` with compact configs and a deterministic `calculated_at`.
- [ ] Confirm an `indicator_snapshots` row is created with the expected symbol, provider, calculation date, input range, calculation version, JSON payload sections, and complete/incomplete flags.
- [ ] Confirm a missing benchmark path persists a relative-strength incomplete detail rather than failing the ticker refresh.
- [ ] Confirm a deliberately malformed cached candle path logs ticker/calculation context and omits secrets, authorization headers, API keys, and database URLs.

## Acceptance Criteria

- [ ] Indicator snapshot models store ticker, calculation date, input candle range, indicator values, incomplete-data flags, and calculation version.
- [ ] A service recomputes indicators from cached candles for a ticker set without calling providers directly from indicator code.
- [ ] Repository tests cover snapshot creation, latest snapshot lookup, versioned snapshot lookup, and incomplete-data persistence.
- [ ] Refresh failures are logged with ticker and calculation context without secrets.
- [ ] All planned tasks completed.
- [ ] Relevant tests added or updated.
- [ ] Validation commands pass.
- [ ] End-to-end verification passes.
- [ ] Implementation follows `AGENTS.md`.

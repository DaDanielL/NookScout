# Plan: Persist Market Data Cache and Ingestion Runs

## Summary

Implement the first persistence slice for normalized market data by adding SQLAlchemy ORM models, typed repository classes, and an Alembic migration for ticker reference data, daily candles, quote snapshots, and ingestion run metadata. The implementation should keep provider payloads outside domain consumers, expose cached reads as existing market-data domain contracts (`TickerReference`, `DailyCandle`, and `Quote`), and use SQLite-backed repository tests while preserving PostgreSQL as the target database.

## User Story

As a developer, I want quotes, candles, ticker metadata, and ingestion run metadata persisted, so that NookScout can control provider cost, reproduce setup ideas, and support later hosted operation.

## Metadata

| Field | Value |
|-------|-------|
| Type | NEW_CAPABILITY |
| Complexity | MEDIUM |
| Systems Affected | Persistence, market data cache contracts, Alembic migrations, repository tests |
| GitHub Issue | #6, https://github.com/DaDanielL/NookScout/issues/6 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-006` |

---

## Patterns to Follow

### Naming

```text
SOURCE: AGENTS.md:181
Use clear domain names: Watchlist, Ticker, Candle, IndicatorSnapshot, SetupRun,
SetupIdea, SetupScore, Rationale. Persistence names should stay explicit:
TickerRecord, DailyCandleRecord, QuoteSnapshotRecord, and IngestionRunRecord.
```

```text
SOURCE: app/market_data/schemas.py:89
Normalized market-data contracts already use Quote, DailyCandle, and
TickerReference. Repository read APIs should return these domain contracts rather
than ORM rows when serving cached data to future indicators or chart code.
```

### Boundaries

```text
SOURCE: AGENTS.md:101
Market data providers fetch quotes, daily candles, reference data, and liquidity
inputs. Persistence must cache normalized outputs and must not introduce provider
API calls into repositories, indicators, scoring, or UI/chart consumers.
```

```text
SOURCE: app/market_data/base.py:34
MarketDataProvider is the provider boundary. Repositories should consume and
return provider-neutral schemas, not Massive response shapes.
```

```text
SOURCE: app/persistence/base.py:1
The persistence layer currently exposes only the SQLAlchemy DeclarativeBase.
Add concrete models under app/persistence/models.py and repository classes under
app/persistence/repositories.py, matching AGENTS.md key-file expectations.
```

### Types and Timestamps

```text
SOURCE: app/market_data/schemas.py:25
DataRecency and AssetType are StrEnum values. Store enum values as strings in DB
rows and convert back through Pydantic domain models at repository boundaries.
```

```text
SOURCE: app/market_data/schemas.py:82
Market timestamps must be timezone-aware and are normalized to exchange context.
Persistence should validate aware datetimes on write, store UTC instants, and
return domain objects that normalize back through existing Pydantic validators.
```

```text
SOURCE: app/market_data/schemas.py:149
DailyCandle includes session_date, timestamp, OHLCV fields, optional vwap and
trade_count, adjusted flag, provider, and data_recency. Preserve all of these in
the candle cache table.
```

```text
SOURCE: app/market_data/schemas.py:205
TickerReference includes symbol, name, asset_type, exchange, currency, active/OTC
flags, market cap, optional average daily volume, provider, as_of, and recency.
Persist this as the current normalized ticker metadata per symbol/provider.
```

### Error Handling

```text
SOURCE: AGENTS.md:221
Prefer typed exceptions for provider, scoring, persistence, and LLM failures.
Add a small persistence exception hierarchy only where repository failures need
domain-specific meaning; otherwise let SQLAlchemy integrity errors surface in tests.
```

```text
SOURCE: app/api/routes/universe.py:45
Systemic provider errors are translated at the API boundary. Repositories should
not raise HTTPException; they should return None or empty tuples for cache misses
and use typed persistence errors for invalid repository operations.
```

### Migrations

```text
SOURCE: migrations/env.py:16
Alembic uses Base.metadata as target_metadata. Import the model module in env.py
so newly declared tables are registered before migrations/autogeneration run.
```

### Tests

```text
SOURCE: tests/conftest.py:13
Tests construct deterministic settings with _env_file=None and SQLite database
URLs. Repository tests should use an in-memory SQLite engine and create metadata
fresh for each test.
```

```text
SOURCE: tests/api/test_universe.py:30
Tests use fake provider/data objects instead of live provider calls. Repository
tests should build normalized Quote, DailyCandle, and TickerReference objects
directly and verify cached reads return equivalent domain contracts.
```

```text
SOURCE: tests/market_data/test_massive.py:47
Existing tests use compact helpers for fixtures and assertions. Mirror that style
with quote_payload, candle_payload, reference_payload, and repository helpers.
```

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `app/persistence/types.py` | CREATE | Add an aware datetime SQLAlchemy type/helper so SQLite tests and PostgreSQL target preserve timestamp instants consistently. |
| `app/persistence/models.py` | CREATE | Define SQLAlchemy models for ticker references, daily candles, quote snapshots, and ingestion runs with constraints and indexes. |
| `app/persistence/repositories.py` | CREATE | Add repository classes that upsert/write normalized market-data contracts and read cached contracts without provider calls. |
| `app/persistence/__init__.py` | UPDATE | Export persistence models/repositories that are safe for application imports. |
| `migrations/env.py` | UPDATE | Import persistence models before setting/running metadata so Alembic sees new tables. |
| `migrations/versions/20260512_0001_market_data_cache_ingestion_runs.py` | CREATE | Create database tables, indexes, uniqueness constraints, and downgrade logic. |
| `tests/persistence/__init__.py` | CREATE | Keep test package structure consistent with existing test directories. |
| `tests/persistence/test_repositories.py` | CREATE | Cover repository insert/upsert, date-range retrieval, cache misses, uniqueness behavior, and ingestion failure status. |

---

## Data Model Design

Use SQLAlchemy 2 typed declarative mapping with `Mapped[...]` and `mapped_column(...)`.

### TickerRecord

- Table: `tickers`
- Fields:
  - `id` integer primary key
  - `symbol` string, normalized uppercase
  - `provider` string
  - `name` string
  - `asset_type` string enum value
  - `primary_exchange` string
  - `currency` string
  - `is_active` boolean
  - `is_otc` boolean
  - `market_cap` numeric nullable
  - `average_daily_volume` bigint nullable
  - `as_of` aware timestamp
  - `data_recency` string enum value
  - `retrieved_at` aware timestamp
  - `created_at` and `updated_at`
- Constraints/indexes:
  - unique `(symbol, provider)`
  - index `(symbol, provider)`

### DailyCandleRecord

- Table: `daily_candles`
- Fields:
  - `id` integer primary key
  - `symbol` string
  - `provider` string
  - `session_date` date
  - `timestamp` aware timestamp
  - `open`, `high`, `low`, `close` numeric
  - `volume` bigint
  - `vwap` numeric nullable
  - `trade_count` bigint nullable
  - `adjusted` boolean
  - `data_recency` string enum value
  - `retrieved_at` aware timestamp
  - `created_at` and `updated_at`
- Constraints/indexes:
  - unique `(symbol, provider, session_date, adjusted)`
  - index `(symbol, session_date)`
  - index `(symbol, provider, session_date)`

### QuoteSnapshotRecord

- Table: `quote_snapshots`
- Fields:
  - `id` integer primary key
  - `symbol` string
  - `provider` string
  - `last_price`, `bid_price`, `ask_price`, `day_open`, `day_high`, `day_low`, `previous_close` numeric values matching `Quote`
  - `day_volume` bigint nullable
  - `as_of` aware timestamp from provider-normalized quote
  - `data_recency` string enum value
  - `retrieved_at` aware timestamp for cache retrieval time
  - `created_at`
- Constraints/indexes:
  - unique `(symbol, provider, as_of)`
  - index `(symbol, provider, retrieved_at)`

### IngestionRunRecord

- Table: `ingestion_runs`
- Fields:
  - `id` integer primary key
  - `provider` string
  - `run_type` string, for example `ticker_reference`, `daily_candles`, `quote_snapshot`, or `market_data_refresh`
  - `status` string, values `running`, `succeeded`, `failed`
  - `started_at` aware timestamp
  - `finished_at` aware timestamp nullable
  - `requested_symbols` JSON nullable
  - `succeeded_count` integer default `0`
  - `failed_count` integer default `0`
  - `error_message` text nullable
  - `created_at` and `updated_at`
- Constraints/indexes:
  - index `(provider, run_type, started_at)`
  - index `(status, started_at)`

Do not store raw provider payloads for this slice. The accepted normalized contracts already contain the fields needed for reproducibility; add raw payload storage later only if debugging or audit requirements prove it is worth the cost.

---

## Repository API Design

Repositories should accept a SQLAlchemy `Session` in `__init__` and should call `session.flush()` after writes but not `commit()`. The caller owns transaction boundaries.

### TickerRepository

- `upsert_reference(reference: TickerReference, *, retrieved_at: datetime) -> TickerRecord`
- `get_reference(symbol: str, *, provider: str | None = None) -> TickerReference | None`

### DailyCandleRepository

- `upsert_many(candles: Sequence[DailyCandle], *, retrieved_at: datetime) -> int`
- `get_range(symbol: str, start_date: date, end_date: date, *, provider: str | None = None, adjusted: bool = True) -> tuple[DailyCandle, ...]`

### QuoteSnapshotRepository

- `upsert_snapshot(quote: Quote, *, retrieved_at: datetime) -> QuoteSnapshotRecord`
- `get_latest(symbol: str, *, provider: str | None = None) -> Quote | None`

### IngestionRunRepository

- `start(provider: str, run_type: str, *, started_at: datetime, requested_symbols: Sequence[str] = ()) -> IngestionRunRecord`
- `mark_succeeded(run_id: int, *, finished_at: datetime, succeeded_count: int, failed_count: int = 0) -> IngestionRunRecord`
- `mark_failed(run_id: int, *, finished_at: datetime, error_message: str, succeeded_count: int = 0, failed_count: int = 0) -> IngestionRunRecord`
- `get(run_id: int) -> IngestionRunRecord | None`

---

## Risks

| Risk | Mitigation |
|------|------------|
| SQLite timestamp behavior differs from PostgreSQL timestamptz. | Add a small persistence datetime type/helper that requires aware datetimes, stores UTC instants, and restores tzinfo on read. Repository tests should prove domain models round-trip through SQLite. |
| PostgreSQL upsert syntax can diverge from SQLite test syntax. | Use SQLAlchemy dialect-specific insert only behind small helper functions, or implement portable select-then-insert/update logic for this MVP slice. Prefer portability unless performance becomes a proven issue. |
| Alembic metadata may miss models if the model module is not imported. | Update `migrations/env.py` to import `app.persistence.models` for metadata registration. |
| Repositories accidentally commit, making future service transactions hard to compose. | Repositories should flush only. Tests should commit explicitly when needed, and transaction boundaries should remain with callers. |
| Cached reads accidentally return ORM rows instead of domain contracts. | Repository read methods should construct `Quote`, `DailyCandle`, and `TickerReference` so indicator/chart code receives provider-neutral contracts. |
| Raw provider payload storage expands schema and privacy footprint prematurely. | Do not add raw payload columns in this story. Store normalized fields and ingestion error messages only. |

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: Add Persistence Datetime Helper

- **File**: `app/persistence/types.py`
- **Action**: CREATE
- **Implement**: Add an SQLAlchemy type or helper for timezone-aware datetimes. It should reject naive datetimes on bind, normalize stored instants to UTC, and restore UTC tzinfo when SQLite returns naive values.
- **Mirror**: `app/market_data/schemas.py:82` - existing market timestamp validation requires aware datetimes.
- **Validate**: `uv run mypy .`

### Task 2: Define Market Data Cache ORM Models

- **File**: `app/persistence/models.py`
- **Action**: CREATE
- **Implement**: Add `TickerRecord`, `DailyCandleRecord`, `QuoteSnapshotRecord`, ingestion run status/run type constants or enums, and `IngestionRunRecord`. Use `Mapped[...]`, explicit column types, uniqueness constraints, and indexes from the Data Model Design section.
- **Mirror**: `app/persistence/base.py:1` - attach all models to the shared SQLAlchemy `Base`.
- **Validate**: `uv run mypy .`

### Task 3: Register Persistence Models for Imports and Alembic

- **File**: `app/persistence/__init__.py`
- **Action**: UPDATE
- **Implement**: Export the new model and repository names that are useful at application boundaries. Avoid eager application startup work.
- **Mirror**: `app/market_data/base.py:63` - use explicit `__all__` style for public names.
- **Validate**: `uv run ruff check .`

### Task 4: Add Alembic Metadata Import

- **File**: `migrations/env.py`
- **Action**: UPDATE
- **Implement**: Import `app.persistence.models` before Alembic uses `Base.metadata` so tables are registered. Use an explicit side-effect import with a concise comment or `# noqa: F401` if needed.
- **Mirror**: `migrations/env.py:16` - target metadata comes from `Base.metadata`.
- **Validate**: `uv run ruff check .`

### Task 5: Create Initial Market Data Cache Migration

- **File**: `migrations/versions/20260512_0001_market_data_cache_ingestion_runs.py`
- **Action**: CREATE
- **Implement**: Add Alembic `upgrade()` and `downgrade()` for `tickers`, `daily_candles`, `quote_snapshots`, and `ingestion_runs`. Include all uniqueness constraints and indexes named explicitly. Use SQLAlchemy portable types where possible so the migration can run against PostgreSQL and SQLite smoke tests.
- **Mirror**: `alembic.ini` and `migrations/script.py.mako` - follow existing Alembic script location and template conventions.
- **Validate**: `NOOKSCOUT_DATABASE_URL=sqlite+pysqlite:////tmp/nookscout-story-006-migration.db uv run alembic upgrade head`

### Task 6: Implement Ticker and Candle Repositories

- **File**: `app/persistence/repositories.py`
- **Action**: CREATE
- **Implement**: Add `TickerRepository` and `DailyCandleRepository` with the API in Repository API Design. Normalize symbol inputs with `normalize_symbol`, return `None` or empty tuples for cache misses, and return Pydantic domain contracts for reads.
- **Mirror**: `app/market_data/schemas.py:205` and `app/market_data/schemas.py:149` - use existing `TickerReference` and `DailyCandle` contracts.
- **Validate**: `uv run pytest tests/persistence/test_repositories.py`

### Task 7: Implement Quote Snapshot and Ingestion Run Repositories

- **File**: `app/persistence/repositories.py`
- **Action**: UPDATE
- **Implement**: Add `QuoteSnapshotRepository` and `IngestionRunRepository`. Quote reads should support latest snapshot by symbol/provider. Ingestion runs should support start, success, failure, and get-by-id flows with failure message preservation.
- **Mirror**: `app/market_data/schemas.py:89` - use existing `Quote` contract for cached quote reads.
- **Validate**: `uv run pytest tests/persistence/test_repositories.py`

### Task 8: Add Persistence Repository Tests

- **File**: `tests/persistence/__init__.py`
- **Action**: CREATE
- **Implement**: Add an empty package marker for the new persistence test package.
- **Mirror**: `tests/market_data/__init__.py` - existing package marker style.
- **Validate**: `uv run pytest tests/persistence/test_repositories.py`

### Task 9: Add Repository Test Coverage

- **File**: `tests/persistence/test_repositories.py`
- **Action**: CREATE
- **Implement**:
  - Create an in-memory SQLite engine and SQLAlchemy `Session` fixture.
  - Import persistence models before `Base.metadata.create_all`.
  - Add helper payload builders for `TickerReference`, `DailyCandle`, and `Quote`.
  - Cover ticker reference insert/upsert and missing symbol lookup.
  - Cover daily candle upsert, update-on-conflict, ordered retrieval by ticker/date range, adjusted filtering, and empty date-range misses.
  - Cover quote snapshot insert/upsert and latest quote retrieval.
  - Cover ingestion run start, success status, failure status, finished timestamp, counts, and error message.
  - Assert repositories return domain objects, not ORM rows, for cached market data reads.
- **Mirror**: `tests/market_data/test_schemas.py:21` and `tests/api/test_universe.py:30` - use focused payload helpers and deterministic fake data.
- **Validate**: `uv run pytest tests/persistence/test_repositories.py`

### Task 10: Run Full Backend Validation

- **File**: N/A
- **Action**: VALIDATE
- **Implement**: Run the full backend validation set after all code and migration work is complete.
- **Mirror**: `AGENTS.md:243` - backend validation expectations.
- **Validate**:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run mypy .`
  - `uv run pytest`

---

## Validation

Run the exact backend validation commands from `AGENTS.md`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

Run targeted checks during implementation:

```bash
uv run pytest tests/persistence/test_repositories.py
NOOKSCOUT_DATABASE_URL=sqlite+pysqlite:////tmp/nookscout-story-006-migration.db uv run alembic upgrade head
```

## End-to-End Verification

- [ ] Create an in-memory SQLite database from `Base.metadata`, write a ticker reference, quote snapshot, and candle series through repositories, then read them back as `TickerReference`, `Quote`, and ordered `DailyCandle` domain objects.
- [ ] Run the Alembic migration against a temporary SQLite database and confirm all four new tables are created.
- [ ] Start an ingestion run, mark it failed, and confirm status, finished timestamp, counts, and error message persist.

## Acceptance Criteria

- [ ] SQLAlchemy models and repositories persist tickers, daily candles, quote snapshots/current-price records, and ingestion run status.
- [ ] Alembic migration creates required tables with uniqueness constraints for ticker/provider, candle ticker/date/provider/adjusted, and quote ticker/provider/as_of records.
- [ ] Repository tests cover insert, upsert, retrieval by ticker/date range, missing data, and ingestion failure status.
- [ ] Cached data reads are available to indicator and chart code via repository methods returning provider-neutral domain contracts.
- [ ] Relevant tests added or updated.
- [ ] Validation commands pass.
- [ ] End-to-end verification passes.
- [ ] Implementation follows `AGENTS.md`.

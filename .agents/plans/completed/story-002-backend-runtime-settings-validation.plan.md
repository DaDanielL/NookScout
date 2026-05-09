# Plan: STORY-002 Backend Runtime, Settings, and Validation Tools

## Summary

Scaffold the first NookScout backend runtime so later data, scoring, persistence, and API stories can build behind stable commands. The implementation should add a `uv`/Python 3.12 project configuration, a minimal FastAPI app with a typed `/health` endpoint, Pydantic settings that load existing provider configuration without requiring provider calls on import, baseline SQLAlchemy/Alembic structure, a no-op scheduler entrypoint for the documented command, focused tests, and README/setup documentation.

## User Story

As a developer, I want the FastAPI backend, Python tooling, and local settings scaffolded, so that data and scoring work can be implemented behind stable project commands.

## Metadata

| Field | Value |
|-------|-------|
| Type | NEW_CAPABILITY |
| Complexity | MEDIUM |
| Systems Affected | Backend runtime, configuration, API health endpoint, validation tooling, documentation |
| GitHub Issue | #2, https://github.com/DaDanielL/NookScout/issues/2 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-002` |

---

## Patterns to Follow

There is no existing product backend yet. Mirror the project rules, story manifest, provider decision doc, and AI-layer conventions instead of inventing unrelated structure.

### Naming

```text
SOURCE: AGENTS.md:181
Use clear domain names: Watchlist, Ticker, Candle, IndicatorSnapshot, SetupRun, SetupIdea, SetupScore, and Rationale.
```

```text
SOURCE: AGENTS.md:157
Key backend files include app/main.py, app/core/settings.py, app/market_data/base.py, app/persistence/models.py, app/jobs/scheduler.py.
```

```text
SOURCE: .agents/README.md:11
Implementation plans belong under .agents/plans/.
```

### Architecture Boundaries

```text
SOURCE: AGENTS.md:95
Use a modular monolith with explicit vertical boundaries and keep the product local-first while preserving a hosted multi-user path.
```

```text
SOURCE: AGENTS.md:100
The API layer exposes typed endpoints for watchlists, tickers, setup runs, setup details, market refreshes, and health checks.
```

```text
SOURCE: AGENTS.md:119
Backend product code should live under app/ with api, core, market_data, indicators, scoring, llm, persistence, jobs, and telemetry modules.
```

### Configuration

```text
SOURCE: AGENTS.md:230
Store secrets only in environment variables or ignored local .env files, never in committed config.
```

```text
SOURCE: AGENTS.md:232
Keep .env.example current whenever settings change.
```

```text
SOURCE: .env.example:6
NOOKSCOUT_MARKET_DATA_PROVIDER=massive
```

```text
SOURCE: docs/market-data-providers.md:54
The selected provider settings are NOOKSCOUT_MARKET_DATA_PROVIDER and MASSIVE_* variables; real secret values belong only in local .env.
```

### Error Handling

```text
SOURCE: AGENTS.md:223
Fail gracefully for provider unavailability, rate limits, and missing data; future provider code should use typed failures.
```

```text
SOURCE: AGENTS.md:225
Logs must include enough context to debug without leaking API keys.
```

### Tests

```text
SOURCE: AGENTS.md:237
Backend unit tests should cover deterministic domain behavior, provider normalization, API endpoints, and prompt contracts as those layers exist.
```

```text
SOURCE: AGENTS.md:241
No live-provider tests in default CI/local validation; mock provider calls to avoid cost, rate limits, and flakiness.
```

```text
SOURCE: .agents/stories/nookscout-technical-setup-discovery.stories.md:113
Add a minimal tests/ structure that can host unit and integration tests.
```

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `pyproject.toml` | CREATE | Define Python 3.12 project metadata, runtime dependencies, dev dependencies, Ruff, mypy, and pytest settings. |
| `uv.lock` | CREATE | Lock dependencies after `uv sync`. |
| `app/__init__.py` | CREATE | Mark backend package. |
| `app/main.py` | CREATE | Build and expose the FastAPI app without external provider calls on import. |
| `app/api/__init__.py` | CREATE | Mark API package. |
| `app/api/dependencies.py` | CREATE | Provide cached settings dependency for routes. |
| `app/api/router.py` | CREATE | Aggregate API routers. |
| `app/api/routes/__init__.py` | CREATE | Mark routes package. |
| `app/api/routes/health.py` | CREATE | Expose typed `/health` endpoint. |
| `app/api/schemas.py` | CREATE | Define API response DTOs such as `HealthResponse`. |
| `app/core/__init__.py` | CREATE | Mark core package. |
| `app/core/settings.py` | CREATE | Load typed local-first settings from env and `.env`. |
| `app/jobs/__init__.py` | CREATE | Mark jobs package. |
| `app/jobs/scheduler.py` | CREATE | Provide documented scheduler module entrypoint without scheduling real work yet. |
| `app/persistence/__init__.py` | CREATE | Mark persistence package. |
| `app/persistence/base.py` | CREATE | Provide SQLAlchemy declarative base for future models. |
| `alembic.ini` | CREATE | Configure Alembic entrypoint for future migrations. |
| `migrations/env.py` | CREATE | Wire Alembic to settings and SQLAlchemy metadata without creating tables yet. |
| `migrations/script.py.mako` | CREATE | Standard Alembic migration template. |
| `migrations/versions/.gitkeep` | CREATE | Preserve empty migration versions directory. |
| `tests/conftest.py` | CREATE | Provide test app/settings fixtures that do not depend on local secrets. |
| `tests/api/test_health.py` | CREATE | Verify health endpoint contract and absence of secret-bearing fields. |
| `tests/core/test_settings.py` | CREATE | Verify defaults, env parsing, and secret redaction behavior. |
| `tests/jobs/test_scheduler.py` | CREATE | Verify scheduler module imports and placeholder command path works. |
| `.env.example` | UPDATE | Add app/database/runtime settings while preserving provider placeholders. |
| `README.md` | UPDATE | Replace template README with NookScout setup, backend commands, health check, and educational-use disclaimer. |

No frontend files are needed for this story.

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: Configure Python Project and Tooling

- **File**: `pyproject.toml`
- **Action**: CREATE
- **Implement**: Define a `nookscout` Python 3.12 project with `uv`-compatible metadata. Add runtime dependencies for `fastapi[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pandas`, `numpy`, and `apscheduler`. Add dev dependencies for `pytest`, `httpx`, `ruff`, and `mypy`. Configure pytest `testpaths = ["tests"]`, Ruff target `py312`, and mypy for typed backend code.
- **Mirror**: `AGENTS.md:28` - Python 3.12 is the primary backend runtime.
- **Validate**: `uv sync`

### Task 2: Add Typed Settings

- **File**: `app/core/settings.py`
- **Action**: CREATE
- **Implement**: Create a Pydantic `Settings` model using `pydantic-settings` and `.env` support. Include local-first app settings such as app name, environment, log level, timezone, database URL, and selected market data provider. Parse the existing `MASSIVE_*` settings as typed fields, storing `MASSIVE_API_KEY` as an optional secret so imports and tests do not require a live key. Validate the timezone with `zoneinfo.ZoneInfo`, ignore unknown env vars, and expose a cached `get_settings()` helper.
- **Mirror**: `.agents/stories/nookscout-technical-setup-discovery.stories.md:106` - `app/core/settings.py` loads typed settings from environment variables and `.env.example` documents every non-secret setting.
- **Validate**: `uv run pytest tests/core/test_settings.py`

### Task 3: Create FastAPI App and Health Contract

- **File**: `app/main.py`, `app/api/router.py`, `app/api/dependencies.py`, `app/api/routes/health.py`, `app/api/schemas.py`
- **Action**: CREATE
- **Implement**: Add a `create_app()` factory and module-level `app`. Include a typed `/health` endpoint returning a Pydantic DTO with `status`, `app_name`, `environment`, `market_data_provider`, `timezone`, and a timezone-aware `checked_at` timestamp. Use dependency-injected settings and avoid provider clients, database connections, scheduler startup, or any network calls during import.
- **Mirror**: `.agents/stories/nookscout-technical-setup-discovery.stories.md:105` - `app/main.py` exposes a FastAPI app with a typed health endpoint and no external provider calls on import.
- **Validate**: `uv run pytest tests/api/test_health.py`

### Task 4: Add Persistence, Alembic, and Scheduler Skeletons

- **File**: `app/persistence/base.py`, `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/.gitkeep`, `app/jobs/scheduler.py`
- **Action**: CREATE
- **Implement**: Add a minimal SQLAlchemy `DeclarativeBase` for future models and an Alembic environment that reads the configured database URL but does not create any migrations yet. Add a scheduler module with a `main()` function and `if __name__ == "__main__"` guard that exits cleanly with a placeholder message, keeping `uv run python -m app.jobs.scheduler` usable before ingestion jobs exist.
- **Mirror**: `AGENTS.md:127` - persistence owns SQLAlchemy models, repositories, and migrations hooks; `AGENTS.md:168` names `app/jobs/scheduler.py` as the scheduled refresh entrypoint.
- **Validate**: `uv run python -m app.jobs.scheduler`

### Task 5: Update Environment and README Documentation

- **File**: `.env.example`, `README.md`
- **Action**: UPDATE
- **Implement**: Add placeholder app/runtime settings such as `NOOKSCOUT_ENVIRONMENT`, `NOOKSCOUT_LOG_LEVEL`, `NOOKSCOUT_TIMEZONE`, and `NOOKSCOUT_DATABASE_URL`, while preserving the STORY-001 Massive provider placeholders. Replace the template README with NookScout-specific setup, local backend commands, health endpoint usage, validation commands, and a clear educational-use disclaimer. Keep command names aligned with `AGENTS.md`; if implementation chooses different commands, update both README and `AGENTS.md`.
- **Mirror**: `AGENTS.md:154` - README is the human setup guide, product overview, local commands, and educational-use disclaimer.
- **Validate**: `rg -n "uv sync|uv run fastapi dev app/main.py|uv run pytest|educational|NOOKSCOUT_DATABASE_URL" README.md .env.example`

### Task 6: Add Focused Backend Tests

- **File**: `tests/conftest.py`, `tests/api/test_health.py`, `tests/core/test_settings.py`, `tests/jobs/test_scheduler.py`
- **Action**: CREATE
- **Implement**: Add pytest fixtures that instantiate settings without relying on the user’s local `.env` secrets. Test settings defaults and env overrides, health response shape and timestamp timezone awareness, absence of secret-bearing response fields, and scheduler import/placeholder execution. Use `fastapi.testclient.TestClient` or `httpx` through FastAPI’s supported test path.
- **Mirror**: `AGENTS.md:238` - integration tests should cover API endpoints, and no live provider calls should run by default.
- **Validate**: `uv run pytest`

### Task 7: Generate Lockfile and Run Acceptance Validation

- **File**: `uv.lock`, all scaffolded files
- **Action**: CREATE / UPDATE
- **Implement**: Run `uv sync` to create or update `uv.lock`, then run the backend validation commands. Fix any lint, format, type, or test failures in the scaffold. Confirm `git diff --check` passes. If `uv sync` is blocked by sandboxed network access, rerun with approval rather than bypassing dependency resolution.
- **Mirror**: `AGENTS.md:243` - validation commands must run before reporting scaffold work complete once the scaffold exists.
- **Validate**: `uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest`

---

## Risks

| Risk | Mitigation |
|------|------------|
| Dependency resolution requires network access in the sandbox. | Run `uv sync`; if it fails for network reasons, request escalation and do not hand-edit `uv.lock`. |
| Settings may accidentally require a real Massive API key and break imports/tests. | Make provider secrets optional for scaffold import, store them as secret types, and avoid provider clients until STORY-004. |
| Health endpoint could expose secret configuration. | Return only non-secret operational fields and add a test asserting no key/token fields appear. |
| Alembic could try to connect to PostgreSQL during validation. | Configure Alembic but do not run migration commands in default validation; keep `target_metadata` available for future models. |
| README and AGENTS commands could drift. | Keep AGENTS command names unless a change is necessary; if script names differ, update both docs in the same implementation pass. |

---

## Validation

Run these exact backend commands after implementation:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
uv run python -m app.jobs.scheduler
```

For manual app startup smoke testing:

```bash
uv run fastapi dev app/main.py
```

Then call:

```bash
curl http://127.0.0.1:8000/health
```

The frontend commands from `AGENTS.md` are not applicable until the frontend scaffold exists.

## End-to-End Verification

- [ ] `uv sync` creates `uv.lock` and installs backend/dev dependencies.
- [ ] `uv run fastapi dev app/main.py` starts without provider calls or database connections on import.
- [ ] `GET /health` returns a typed JSON response with `status: "ok"` and no secret-bearing fields.
- [ ] `uv run python -m app.jobs.scheduler` exits cleanly as a placeholder scheduler command.
- [ ] README and `.env.example` match the scaffolded settings and documented commands.

## Acceptance Criteria

- [ ] `pyproject.toml` configures Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, pytest, Ruff, and uv-compatible dependency management.
- [ ] `app/main.py` exposes a FastAPI app with a typed health endpoint and no external provider calls on import.
- [ ] `app/core/settings.py` loads typed settings from environment variables and `.env.example` documents every non-secret setting.
- [ ] Backend validation commands from `AGENTS.md` run or are updated in `AGENTS.md` and `README.md` if script names differ.
- [ ] Relevant tests are added and pass without live-provider calls.
- [ ] Implementation follows `AGENTS.md`.

# AGENTS.md

This file gives Codex and other AI agents the operating context for NookScout.

## Project Overview

NookScout is a Python-first local web app for beginner to intermediate swing traders who want structured, educational technical setup discovery for liquid U.S. stocks.

The MVP helps a personal user scan a predefined liquid-stock universe or saved watchlists, rank beginner-friendly bullish long swing setup ideas, and review each setup with clear technical rationale, chart levels, and risk/reward context.

The product starts as a local-only personal tool, but architecture and code choices should preserve a clean path to a hosted multi-user web app later.

Do not build brokerage integration, automated trading, options workflows, short-selling workflows, or personalized financial-advice features in the MVP.

## Product Context

- **Primary users**: beginner to intermediate, self-directed swing traders with zero to moderate market knowledge.
- **Core problem**: users struggle to identify liquid stocks worth watching and combine technical signals into structured trade-plan ideas.
- **MVP outcome**: surface ranked bullish swing setup ideas with complete technical rationale, entry zone, stop/invalidation area, target area, risk/reward estimate, and failure case.
- **Source PRD**: `.agents/PRDs/nookscout-technical-setup-discovery.prd.md`
- **Initial user model**: local-only personal use with no user account storage.
- **Expected holding window**: generally 3 to 20 trading days.

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.12 | Primary backend, data, and quant runtime with broad package support. |
| uv | Python package, environment, and lockfile management. |
| FastAPI | Backend API for market data, watchlists, setup runs, scoring, and LLM rationale generation. |
| Pydantic | Typed validation for API contracts, settings, provider payloads, and setup schemas. |
| pandas / NumPy | Technical indicator and candle-series computation. |
| SQLAlchemy | Database access through explicit repository boundaries. |
| Alembic | Database migrations. |
| PostgreSQL | Target database for watchlists, candles, indicators, setup runs, setup ideas, scoring versions, and local analytics events. |
| SQLite | Acceptable only for very early local experiments or test fixtures. |
| APScheduler | Simple local scheduled ingestion and scoring jobs. |
| Redis + RQ or Celery | Later option when background work outgrows local scheduling. |
| React + TypeScript | Product frontend for dashboard, watchlist, setup card, and chart interactions. |
| Vite | Frontend build and development tooling for the MVP. |
| TradingView lightweight-charts | Candlestick charts with range controls, markers, and read-only entry/stop/target overlays. |
| pytest | Backend unit and integration testing. |
| Ruff | Python linting and formatting. |
| mypy or pyright | Python static type checking once scaffolded. |

## Commands

Use exact commands once the app is scaffolded. Until then, keep placeholders explicit.

```bash
# Install Python dependencies
uv sync

# Start backend development server
uv run fastapi dev app/main.py

# Run scheduled/local worker process
uv run python -m app.jobs.scheduler

# Type check backend
uv run mypy .

# Lint backend
uv run ruff check .

# Check backend formatting
uv run ruff format --check .

# Run backend tests
uv run pytest

# Install frontend dependencies
npm install

# Start frontend development server
npm run dev

# Lint frontend
npm run lint

# Type check frontend
npm run typecheck

# Test frontend
npm run test

# Build frontend
npm run build
```

If the scaffold chooses different script names, update this section immediately.

## Architecture

Use a modular monolith with explicit vertical boundaries. Keep the product local-first, but separate concerns so the app can later support authentication, hosted deployments, multiple users, and provider swaps.

Core layers:

- **Frontend dashboard**: renders Scout Mode, Watchlist Mode, ranked setup cards, expanded details, chart ranges, and local UI states.
- **API layer**: exposes typed endpoints for watchlists, tickers, setup runs, setup details, market refreshes, and health checks.
- **Market data layer**: provider adapters fetch quotes, daily candles, reference data, and liquidity inputs. Never call providers directly from scoring or UI code.
- **Indicator layer**: deterministic technical calculations for moving averages, RSI, MACD, ATR, relative volume, support/resistance, and relative strength.
- **Scoring layer**: deterministic setup classification, confidence factors, risk/reward estimates, no-clear-setup decisions, and failure conditions.
- **LLM rationale layer**: generates beginner-friendly explanations only from structured setup data produced by deterministic code.
- **Persistence layer**: repositories manage watchlists, tickers, candles, indicators, setup runs, setup ideas, scoring versions, rationale versions, and local analytics events.
- **Job layer**: scheduled local scans, candle refreshes, indicator refreshes, and setup generation runs.

## Folder Structure

Recommended scaffold:

```text
.
|-- AGENTS.md                 # Project rules for Codex and other agents
|-- README.md                 # Setup, usage, architecture, and disclaimer overview
|-- .env.example              # Required local environment variables without secrets
|-- pyproject.toml            # Python project metadata and tool configuration
|-- uv.lock                   # Reproducible Python dependency lockfile
|-- app/                      # FastAPI backend and product domain modules
|   |-- main.py               # API application entrypoint
|   |-- api/                  # Route modules and API dependencies
|   |-- core/                 # Settings, logging, time, and shared infrastructure
|   |-- market_data/          # Provider adapters, schemas, and normalization
|   |-- indicators/           # Deterministic technical indicator calculations
|   |-- scoring/              # Setup scoring, classification, and risk/reward logic
|   |-- llm/                  # LLM prompt contracts, clients, and guardrails
|   |-- persistence/          # SQLAlchemy models, repositories, and migrations hooks
|   |-- jobs/                 # Local scheduler and background task orchestration
|   `-- telemetry/            # Local analytics event capture
|-- migrations/               # Alembic migrations
|-- frontend/                 # React + TypeScript + Vite dashboard
|   |-- src/
|   |   |-- api/              # Typed client calls
|   |   |-- components/       # Reusable UI components
|   |   |-- features/         # Scout, watchlist, setup detail, and chart features
|   |   |-- charts/           # Candlestick chart wrappers and overlays
|   |   `-- styles/           # Global styles and design tokens
|   `-- package.json          # Frontend scripts and dependencies
|-- tests/                    # Backend unit, integration, and fixture tests
|   |-- fixtures/             # Candle series and provider payload fixtures
|   |-- indicators/
|   |-- scoring/
|   |-- api/
|   `-- integration/
|-- notebooks/                # Optional research notebooks, never production logic
|-- docs/                     # Data provider notes, scoring methodology, compliance notes
`-- .agents/                  # AI-layer artifacts and workflows
```

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Human setup guide, product overview, local commands, and educational-use disclaimer. |
| `.env.example` | Documents market data keys, LLM keys, database URL, and local settings. |
| `pyproject.toml` | Python dependency and tool configuration. |
| `app/main.py` | FastAPI app entrypoint. |
| `app/core/settings.py` | Typed settings loaded from environment variables. |
| `app/market_data/base.py` | Provider interface for quotes, candles, reference data, and provider capabilities. |
| `app/market_data/{provider}.py` | Concrete provider adapters such as Alpaca, Polygon/Massive, or Twelve Data. |
| `app/indicators/technical.py` | Deterministic technical indicator calculations. |
| `app/scoring/models.py` | Setup schema, scoring inputs, scoring outputs, and confidence factors. |
| `app/scoring/engine.py` | Setup scoring and classification logic. |
| `app/llm/prompts.py` | Prompt templates and structured prompt contracts. |
| `app/llm/service.py` | Rationale generation with hallucination guardrails. |
| `app/persistence/models.py` | Database models. |
| `app/persistence/repositories.py` | Data access methods. |
| `app/jobs/scheduler.py` | Local scheduled refresh and scoring runs. |
| `frontend/src/features/scout/` | Scout Mode dashboard. |
| `frontend/src/features/watchlists/` | Watchlist creation, editing, and watchlist-scoped setup discovery. |
| `frontend/src/features/setups/` | Ranked cards and expanded setup details. |
| `frontend/src/charts/SetupChart.tsx` | Candlestick chart with entry, stop/invalidation, target, and current price overlays. |
| `docs/scoring-methodology.md` | Human-readable explanation of scoring rules and indicator interpretation. |
| `docs/market-data-providers.md` | Provider evaluation, limitations, pricing notes, and licensing reminders. |
| `docs/disclaimer.md` | Educational-use, non-personalized-financial-advice language. |

## Code Patterns

### Naming

- Use clear domain names: `Watchlist`, `Ticker`, `Candle`, `IndicatorSnapshot`, `SetupRun`, `SetupIdea`, `SetupScore`, `Rationale`.
- Name provider-specific code after the provider, but keep shared contracts provider-neutral.
- Name tests after behavior, for example `test_scores_pullback_setup_when_trend_and_rsi_align`.

### File Organization

- Keep production domain logic in `app/`, not notebooks.
- Keep notebooks exploratory. Any useful notebook logic must be promoted into tested modules before app use.
- Keep frontend features grouped by workflow: scout, watchlists, setups, charts.
- Keep API schemas, domain models, and persistence models distinct when their responsibilities differ.

### Data and State

- Persist user watchlists, ticker metadata, candle cache, indicator snapshots, setup runs, setup ideas, scoring versions, rationale versions, and local analytics events.
- Store raw provider payloads only when needed for debugging or reproducibility; otherwise normalize data into provider-neutral tables.
- Version scoring logic and LLM rationale prompts so old setup ideas can be interpreted later.
- Use timezone-aware datetimes. Market-facing timestamps should preserve exchange context, generally America/New_York for U.S. equities.

### Market Data

- Access market data only through adapter interfaces.
- Do not hard-code provider response shapes outside provider modules.
- Cache candles and reference data to control cost and rate limits.
- Prefer daily candles and fresh quotes for MVP. Avoid full tick-by-tick streaming unless a later requirement proves it is needed.
- Keep liquidity rules configurable and testable.

### Indicator and Scoring Logic

- Deterministic code owns prices, indicators, setup levels, risk/reward, classification, confidence factors, and failure conditions.
- LLMs may explain setup data, but must not invent prices, indicators, ticker metadata, chart levels, or risk/reward values.
- If required structured inputs are missing, return `No Clear Setup` or an explicit incomplete-data state.
- Keep bullish long setup ideas only for MVP. Weak tickers should be labeled `No Clear Setup` or `Avoid / Wait`, not turned into short ideas.

### LLM Rationale

- Provide the LLM only normalized structured setup data and allowed educational framing.
- Require structured outputs for thesis summary, expanded rationale, signal explanations, and failure case.
- Validate LLM output for completeness and forbidden language before saving.
- Avoid language that implies certainty, guaranteed returns, individualized advice, or direct buy/sell instructions.

### Error Handling

- Fail gracefully when a provider is unavailable, rate-limited, or missing a ticker.
- Surface incomplete data states clearly in API responses and UI.
- Log provider errors with enough context to debug without leaking API keys.
- Prefer typed exceptions for provider, scoring, persistence, and LLM failures.

### Configuration

- Store secrets only in environment variables or local ignored `.env` files.
- Never commit API keys, provider tokens, LLM keys, database credentials, or private watchlists.
- Keep `.env.example` current whenever settings change.
- Separate provider configuration from scoring configuration.

## Testing

- **Unit tests**: cover indicators, support/resistance helpers, setup scoring, setup classification, risk/reward calculations, provider normalization, and LLM prompt contracts.
- **Integration tests**: cover database repositories, API endpoints, setup generation pipeline, provider adapter behavior with mocked payloads, and rationale generation with mocked LLM responses.
- **Fixture tests**: use known candle series and expected scoring outcomes so scoring regressions are obvious.
- **Frontend tests**: cover dashboard states, watchlist flows, setup card expansion, empty/error states, and chart overlay data mapping once the frontend is scaffolded.
- **No live-provider tests in default CI/local validation**: mock provider calls by default to avoid cost, rate limits, and flaky tests.

## Validation

Run these before reporting work complete once the scaffold exists:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
npm run lint
npm run typecheck
npm run test
npm run build
```

For data or scoring changes, also run fixture-based scoring regression tests.

For UI changes, verify the dashboard in a browser and capture screenshots when preparing a PR.

## GitHub Workflow

- **Issues**: Use GitHub Issues for trackable stories and bugs.
- **Issue creation**: Use `gh issue create` when turning story manifests into issues.
- **Issue inspection**: Use `gh issue view {number}` before planning linked work.
- **Labels**: use consistent labels: `data`, `scoring`, `llm`, `frontend`, `charts`, `storage`, `api`, `tests`, `docs`, `compliance`.
- **Issue size**: prefer small vertical slices that can be implemented and validated independently.
- **Branches**: `feature-{issue-number}-{short-slug}`, `fix-{issue-number}-{short-slug}`, or `docs-{issue-number}-{short-slug}`.
- **Pull requests**: Use `gh pr create` for PRs and `gh pr view` to inspect PR context.
- **PR expectation**: include summary, linked issue, validation commands run, screenshots or recordings for UI changes, and notes on provider or LLM behavior when relevant.
- **PR blockers**: formatting, linting, type checking, unit tests, integration tests, scoring fixture tests, and frontend build where applicable.

## AI Layer

Generated artifacts live under `.agents/`:

| Artifact | Path |
|----------|------|
| PRDs | `.agents/PRDs/` |
| Story manifests | `.agents/stories/` |
| Implementation plans | `.agents/plans/` |
| Implementation reports | `.agents/reports/` |
| Reviews | `.agents/reviews/` |

Recommended workflow:

1. `rules-interactive` or `create-rules`
2. `prd-interactive` or `create-prd`
3. `create-stories`
4. `prime`
5. `plan`
6. `implement`
7. `validate`
8. `review` / `security-review`

## Security Notes

- Treat market data API keys, LLM API keys, database credentials, and future trade notes as sensitive.
- Treat local watchlists as private by default, even though they are not high-risk secrets.
- Do not log secrets or full authorization headers.
- Keep LLM prompts and outputs free of secrets.
- Validate all ticker symbols and provider inputs.
- Keep financial language educational and non-personalized.
- Do not add brokerage execution, order placement, or account-linking without a dedicated PRD and security/compliance review.
- Review market data provider terms before any hosted or multi-user distribution.

## Documentation

Maintain these docs from day one:

| Topic | File |
|-------|------|
| Setup and local usage | `README.md` |
| Environment variables | `.env.example` |
| Market data provider evaluation | `docs/market-data-providers.md` |
| Scoring methodology | `docs/scoring-methodology.md` |
| Educational-use disclaimer | `docs/disclaimer.md` |
| Architecture decisions | `docs/architecture-decisions.md` |

## Open Questions

- Which market data provider should power current prices, historical daily candles, volume, and reference data?
- Should MVP compute every technical indicator internally, or use provider indicators only as a fallback/reference?
- What exact liquidity rules define the predefined stock universe for v1?
- How many setup ideas should Scout Mode show by default?
- How should confidence labels be calibrated without implying certainty?
- Should users be able to save individual setup ideas in MVP, or only save watchlists?
- Which LLM provider and model should generate setup rationale?
- Should PostgreSQL be required from the first scaffold, or should SQLite be allowed for the earliest local prototype?

## Decision Log

- Confirmed primary user: beginner to intermediate swing traders.
- Confirmed initial scope: local-only personal use.
- Confirmed product direction: long-lived product with a path to hosted multi-user expansion.
- Confirmed stack preference: Python-first, using common quant/data tooling.
- Recommended target platform: responsive web app.
- Recommended backend: FastAPI with Pydantic.
- Recommended frontend: React + TypeScript + Vite.
- Recommended package manager: `uv`.
- Recommended storage target: PostgreSQL.
- Recommended charting: TradingView lightweight-charts.
- Confirmed LLM use: rationale generation from deterministic structured setup data only.
- Confirmed MVP testing depth: solid unit and integration tests.

## Agent Notes

- Preserve user changes; do not revert unrelated work.
- Prefer existing patterns over new abstractions.
- Keep generated plans and reports in `.agents/`.
- Document deviations from plans in implementation reports.
- Do not create a demo app or scaffold during rules-generation workflows.

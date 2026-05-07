# Stories: NookScout Technical Setup Discovery

**Source PRD**: `.agents/PRDs/nookscout-technical-setup-discovery.prd.md`
**Generated**: 2026-05-07 18:06 EDT
**Status**: draft
**Requested GitHub Repo**: `DaDanielL/NookScout`
**Requested Milestone**: `MVP - Technical Setup Discovery` (resolved to milestone `1`)
**GitHub Issue Creation**: completed via `gh issue create`.

## Summary

| ID | Title | Type | Priority | Complexity | Phase | GitHub Issue |
|----|-------|------|----------|------------|-------|--------------|
| STORY-001 | Decide MVP Market Data Provider and Constraints | Spike | High | Small | 1 - Market Data Foundation | [#1](https://github.com/DaDanielL/NookScout/issues/1) |
| STORY-002 | Scaffold Backend Runtime, Settings, and Validation Tools | Technical | High | Medium | 1 - Market Data Foundation | [#2](https://github.com/DaDanielL/NookScout/issues/2) |
| STORY-003 | Define Market Data Contracts and Normalized Schemas | Technical | High | Small | 1 - Market Data Foundation | [#3](https://github.com/DaDanielL/NookScout/issues/3) |
| STORY-004 | Implement Daily Candle and Quote Provider Adapter | Technical | High | Medium | 1 - Market Data Foundation | [#4](https://github.com/DaDanielL/NookScout/issues/4) |
| STORY-005 | Define and Apply Liquid Stock Universe Rules | Feature | High | Medium | 1 - Market Data Foundation | [#5](https://github.com/DaDanielL/NookScout/issues/5) |
| STORY-006 | Persist Market Data Cache and Ingestion Runs | Technical | High | Medium | 1 - Market Data Foundation | [#6](https://github.com/DaDanielL/NookScout/issues/6) |
| STORY-007 | Decide Indicator Ownership Strategy | Spike | High | Small | 2 - Technical Indicator Pipeline | [#7](https://github.com/DaDanielL/NookScout/issues/7) |
| STORY-008 | Compute Core Technical Indicators | Technical | High | Medium | 2 - Technical Indicator Pipeline | [#8](https://github.com/DaDanielL/NookScout/issues/8) |
| STORY-009 | Compute Support, Resistance, and Relative Strength Signals | Technical | High | Medium | 2 - Technical Indicator Pipeline | [#9](https://github.com/DaDanielL/NookScout/issues/9) |
| STORY-010 | Persist Indicator Snapshots and Refresh Pipeline | Technical | High | Medium | 2 - Technical Indicator Pipeline | [#10](https://github.com/DaDanielL/NookScout/issues/10) |
| STORY-011 | Define Setup Scoring Schemas and Version Contracts | Technical | High | Small | 3 - Setup Scoring Engine | [#11](https://github.com/DaDanielL/NookScout/issues/11) |
| STORY-012 | Classify Bullish Setup Types and No Clear Setup Outcomes | Feature | High | Medium | 3 - Setup Scoring Engine | [#12](https://github.com/DaDanielL/NookScout/issues/12) |
| STORY-013 | Calculate Entry, Invalidation, Target, Risk/Reward, and Holding Window | Feature | High | Medium | 3 - Setup Scoring Engine | [#13](https://github.com/DaDanielL/NookScout/issues/13) |
| STORY-014 | Calibrate Confidence Labels for Educational Use | Spike | High | Small | 3 - Setup Scoring Engine | [#14](https://github.com/DaDanielL/NookScout/issues/14) |
| STORY-015 | Add Scoring Fixture Regression Tests | Technical | High | Medium | 3 - Setup Scoring Engine | [#15](https://github.com/DaDanielL/NookScout/issues/15) |
| STORY-016 | Persist Setup Runs and Ranked Setup Ideas | Feature | High | Medium | 4 - Setup Synthesis | [#16](https://github.com/DaDanielL/NookScout/issues/16) |
| STORY-017 | Define Educational Disclaimer and Forbidden Financial Advice Language | Spike | High | Small | 4 - Setup Synthesis | [#17](https://github.com/DaDanielL/NookScout/issues/17) |
| STORY-018 | Generate Beginner-Friendly LLM Rationale from Structured Setup Data | Feature | High | Medium | 4 - Setup Synthesis | [#18](https://github.com/DaDanielL/NookScout/issues/18) |
| STORY-019 | Expose Setup Summary and Expanded Detail API Responses | Feature | High | Medium | 4 - Setup Synthesis | [#19](https://github.com/DaDanielL/NookScout/issues/19) |
| STORY-020 | Decide Whether MVP Saves Individual Setup Ideas | Spike | Medium | Small | 4 - Setup Synthesis | [#20](https://github.com/DaDanielL/NookScout/issues/20) |
| STORY-021 | Scaffold Frontend App Shell and Typed API Client | Technical | High | Medium | 5 - Scout Mode UI | [#21](https://github.com/DaDanielL/NookScout/issues/21) |
| STORY-022 | Build Scout Mode Ranked Setup Card Dashboard | Feature | High | Medium | 5 - Scout Mode UI | [#22](https://github.com/DaDanielL/NookScout/issues/22) |
| STORY-023 | Build Expanded Setup Detail and Signal Explanation UI | Feature | High | Medium | 5 - Scout Mode UI | [#23](https://github.com/DaDanielL/NookScout/issues/23) |
| STORY-024 | Add Watchlist Persistence and CRUD API | Feature | High | Medium | 6 - Watchlist Mode UI | [#24](https://github.com/DaDanielL/NookScout/issues/24) |
| STORY-025 | Build Watchlist Management UI | Feature | High | Medium | 6 - Watchlist Mode UI | [#25](https://github.com/DaDanielL/NookScout/issues/25) |
| STORY-026 | Run Watchlist-Scoped Setup Discovery | Feature | High | Medium | 6 - Watchlist Mode UI | [#26](https://github.com/DaDanielL/NookScout/issues/26) |
| STORY-027 | Expose Chart Candle Data and Range API | Feature | High | Small | 7 - Annotated Chart Experience | [#27](https://github.com/DaDanielL/NookScout/issues/27) |
| STORY-028 | Render Daily Candlestick Chart with Range Controls | Feature | High | Medium | 7 - Annotated Chart Experience | [#28](https://github.com/DaDanielL/NookScout/issues/28) |
| STORY-029 | Render Read-Only Entry, Stop, Target, and Current Price Overlays | Feature | High | Medium | 7 - Annotated Chart Experience | [#29](https://github.com/DaDanielL/NookScout/issues/29) |
| STORY-030 | Add Local Analytics Event Capture | Technical | Medium | Medium | 8 - MVP Instrumentation | [#30](https://github.com/DaDanielL/NookScout/issues/30) |
| STORY-031 | Track Scout, Watchlist, Setup Review, and Completeness Metrics | Technical | Medium | Medium | 8 - MVP Instrumentation | [#31](https://github.com/DaDanielL/NookScout/issues/31) |
| STORY-032 | Add Clarity Feedback and Weekly Retention Reporting | Feature | Medium | Medium | 8 - MVP Instrumentation | [#32](https://github.com/DaDanielL/NookScout/issues/32) |
| STORY-033 | Publish MVP Setup, Scoring, Provider, and Disclaimer Documentation | Technical | Medium | Small | 8 - MVP Instrumentation | [#33](https://github.com/DaDanielL/NookScout/issues/33) |

---

## STORY-001: Decide MVP Market Data Provider and Constraints

**Type**: Spike
**Priority**: High
**Complexity**: Small
**Phase**: 1 - Market Data Foundation
**Labels**: `type:spike`, `data`, `backend`, `docs`, `compliance`
**GitHub Issue**: [#1](https://github.com/DaDanielL/NookScout/issues/1)
**Source**: `Open Questions`, `Implementation Phases / 1 - Market Data Foundation`, `Market Data`

### Description

As a local NookScout operator, I want to select the MVP market data provider and document constraints, so that ingestion, scoring, and licensing decisions have a clear foundation.

### Acceptance Criteria

- [ ] `docs/market-data-providers.md` compares at least two viable providers for quotes, historical daily candles, volume, reference data, cost, limits, and licensing.
- [ ] One provider is recommended for MVP with explicit notes on budget, rate limits, delayed or real-time data behavior, and local-only assumptions.
- [ ] Required environment variables are listed for the chosen provider without committing secrets.
- [ ] The decision records whether provider-supplied indicators are available, but does not rely on them before STORY-007.

### Technical Notes

- Use provider adapters under `app/market_data/`; do not call provider APIs directly from scoring or UI code.
- Keep hosted or multi-user redistribution risks visible in the provider notes.
- Update `.env.example` if the selected provider requires keys or runtime settings.

### Dependencies

- Blocked by: None
- Blocks: STORY-003, STORY-004, STORY-005

### GitHub Issue Body

Create a provider decision spike for NookScout MVP market data. Compare providers, document licensing and budget constraints, recommend one MVP provider, list required env vars, and preserve a clean provider-adapter path.

---

## STORY-002: Scaffold Backend Runtime, Settings, and Validation Tools

**Type**: Technical
**Priority**: High
**Complexity**: Medium
**Phase**: 1 - Market Data Foundation
**Labels**: `type:technical`, `backend`, `api`, `testing`
**GitHub Issue**: [#2](https://github.com/DaDanielL/NookScout/issues/2)
**Source**: `Tech Stack`, `Architecture`, `Commands`, `Testing`, `Validation`

### Description

As a developer, I want the FastAPI backend, Python tooling, and local settings scaffolded, so that data and scoring work can be implemented behind stable project commands.

### Acceptance Criteria

- [ ] `pyproject.toml` configures Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, pytest, Ruff, and uv-compatible dependency management.
- [ ] `app/main.py` exposes a FastAPI app with a typed health endpoint and no external provider calls on import.
- [ ] `app/core/settings.py` loads typed settings from environment variables and `.env.example` documents every non-secret setting.
- [ ] Backend validation commands from `AGENTS.md` run or are updated in `AGENTS.md` and `README.md` if script names differ.

### Technical Notes

- Keep configuration local-first while leaving room for hosted deployment settings later.
- Prefer typed Pydantic settings and timezone-aware defaults.
- Add a minimal `tests/` structure that can host unit and integration tests.

### Dependencies

- Blocked by: None
- Blocks: STORY-003, STORY-006, STORY-010, STORY-016, STORY-024, STORY-030

### GitHub Issue Body

Scaffold the backend runtime and validation tools for NookScout. Include FastAPI entrypoint, typed settings, `.env.example`, uv/Ruff/pytest configuration, and a minimal health endpoint.

---

## STORY-003: Define Market Data Contracts and Normalized Schemas

**Type**: Technical
**Priority**: High
**Complexity**: Small
**Phase**: 1 - Market Data Foundation
**Labels**: `type:technical`, `data`, `backend`
**GitHub Issue**: [#3](https://github.com/DaDanielL/NookScout/issues/3)
**Source**: `Architecture / Market data layer`, `Key Files`, `Market Data`

### Description

As a developer, I want provider-neutral market data contracts, so that provider payloads can be normalized before ingestion, indicators, scoring, or UI code use them.

### Acceptance Criteria

- [ ] `app/market_data/base.py` defines provider interfaces for quotes, daily candles, reference data, and provider capabilities.
- [ ] Pydantic schemas validate ticker symbols, quote fields, daily OHLCV candles, exchange timestamps, and reference-data attributes needed for liquidity filtering.
- [ ] Provider-specific response shapes are isolated outside shared scoring, indicator, persistence, and API modules.
- [ ] Unit tests cover schema validation for valid payloads, missing required fields, invalid ticker symbols, and timezone-aware candle timestamps.

### Technical Notes

- Normalize market-facing timestamps with exchange context, generally `America/New_York` for U.S. equities.
- Include enough metadata to support delayed data or provider capability warnings.
- Keep contracts provider-neutral even after STORY-001 selects a first provider.

### Dependencies

- Blocked by: STORY-001, STORY-002
- Blocks: STORY-004, STORY-005, STORY-006, STORY-008

### GitHub Issue Body

Define provider-neutral market data contracts and normalized schemas for quotes, candles, reference data, and provider capabilities. Add validation tests and keep provider payload details out of downstream code.

---

## STORY-004: Implement Daily Candle and Quote Provider Adapter

**Type**: Technical
**Priority**: High
**Complexity**: Medium
**Phase**: 1 - Market Data Foundation
**Labels**: `type:technical`, `data`, `backend`, `testing`
**GitHub Issue**: [#4](https://github.com/DaDanielL/NookScout/issues/4)
**Source**: `MVP Scope / Technical setup scoring`, `Implementation Phases / 1 - Market Data Foundation`, `Market Data`

### Description

As a developer, I want the first provider adapter to fetch current quotes and daily historical candles, so that NookScout can build setup inputs without live-provider calls leaking into domain code.

### Acceptance Criteria

- [ ] A concrete provider adapter implements quote and daily candle methods using the contracts from STORY-003.
- [ ] Provider errors, missing tickers, rate limits, and unavailable data return typed exceptions or explicit incomplete-data results.
- [ ] Tests use mocked provider payloads and do not perform live-provider requests by default.
- [ ] Provider logs include ticker and operation context without API keys, authorization headers, or full secret-bearing URLs.

### Technical Notes

- Store provider-specific code under `app/market_data/{provider}.py`.
- Favor daily candles and fresh quotes for the MVP; do not add streaming or tick-level data.
- Keep fixture payloads in `tests/fixtures/`.

### Dependencies

- Blocked by: STORY-001, STORY-003
- Blocks: STORY-006, STORY-009, STORY-027

### GitHub Issue Body

Implement the first market data provider adapter for current quotes and daily candles. Normalize responses through shared schemas, add mocked fixture tests, and handle provider failures safely.

---

## STORY-005: Define and Apply Liquid Stock Universe Rules

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 1 - Market Data Foundation
**Labels**: `type:feature`, `data`, `backend`, `api`, `testing`
**GitHub Issue**: [#5](https://github.com/DaDanielL/NookScout/issues/5)
**Source**: `MVP Scope / Liquid stock universe filter`, `Open Questions`, `Implementation Phases / 1 - Market Data Foundation`

### Description

As a beginner swing trader, I want Scout Mode to scan only liquid U.S.-listed stocks, so that the setup list avoids beginner-unfriendly illiquid or OTC names.

### Acceptance Criteria

- [ ] Liquidity rules are configurable and cover price, average volume, dollar volume, market cap, listing venue, and OTC/illiquid exclusions.
- [ ] The default rules reflect the PRD ranges unless STORY-001 documents a provider limitation or stronger product decision.
- [ ] An API or internal service returns the eligible predefined universe with exclusion reasons for ineligible tickers.
- [ ] Tests cover accepted names, low-price exclusions, low-volume exclusions, low-dollar-volume exclusions, missing-reference-data behavior, and OTC exclusions.

### Technical Notes

- Keep liquidity rules testable and separate from provider response shapes.
- Consider storing the selected universe and exclusion reasons for reproducibility.
- Do not hard-code one-off ticker lists in scoring code.

### Dependencies

- Blocked by: STORY-001, STORY-003
- Blocks: STORY-016, STORY-022

### GitHub Issue Body

Build configurable liquid-stock universe filtering for Scout Mode. Cover price, average volume, dollar volume, market cap, listing venue, OTC exclusions, provider gaps, and tests.

---

## STORY-006: Persist Market Data Cache and Ingestion Runs

**Type**: Technical
**Priority**: High
**Complexity**: Medium
**Phase**: 1 - Market Data Foundation
**Labels**: `type:technical`, `database`, `data`, `backend`, `testing`
**GitHub Issue**: [#6](https://github.com/DaDanielL/NookScout/issues/6)
**Source**: `Architecture / Persistence layer`, `Data and State`, `Future Extension Considerations`

### Description

As a developer, I want quotes, candles, ticker metadata, and ingestion run metadata persisted, so that NookScout can control provider cost, reproduce setup ideas, and support later hosted operation.

### Acceptance Criteria

- [ ] SQLAlchemy models and repositories persist tickers, daily candles, quote snapshots or current-price records, and ingestion run status.
- [ ] Alembic migrations create the required tables with appropriate uniqueness constraints for ticker/date/provider records.
- [ ] Repository tests cover insert, upsert, retrieval by ticker/date range, missing data, and ingestion failure status.
- [ ] Cached data reads are available to indicator and chart code without direct provider calls.

### Technical Notes

- PostgreSQL is the target database; SQLite may be used only for tests or earliest local fixtures if documented.
- Preserve provider, retrieval timestamp, and normalized timestamp separately where useful.
- Store raw provider payloads only if needed for debugging or reproducibility.

### Dependencies

- Blocked by: STORY-002, STORY-003, STORY-004
- Blocks: STORY-010, STORY-016, STORY-027

### GitHub Issue Body

Add persistence for market data cache and ingestion runs. Include SQLAlchemy models, Alembic migrations, repositories, and tests for ticker metadata, daily candles, quotes, and ingestion status.

---

## STORY-007: Decide Indicator Ownership Strategy

**Type**: Spike
**Priority**: High
**Complexity**: Small
**Phase**: 2 - Technical Indicator Pipeline
**Labels**: `type:spike`, `scoring`, `data`, `docs`
**GitHub Issue**: [#7](https://github.com/DaDanielL/NookScout/issues/7)
**Source**: `Open Questions`, `Indicator and Scoring Logic`, `Implementation Phases / 2 - Technical Indicator Pipeline`

### Description

As a developer, I want to decide whether NookScout computes indicators internally or uses provider indicators as a fallback, so that setup scoring remains deterministic and reproducible.

### Acceptance Criteria

- [ ] `docs/scoring-methodology.md` records the MVP decision for internal calculation versus provider-precomputed indicators.
- [ ] The decision explicitly covers moving averages, RSI, MACD, ATR, relative volume, support/resistance, and relative strength.
- [ ] Any provider indicator use is limited to fallback or reference behavior unless the PRD is updated.
- [ ] Follow-up implementation notes identify required fixtures and expected tolerance for numerical tests.

### Technical Notes

- The PRD states deterministic code owns indicators and setup levels.
- Favor pandas/NumPy calculations with fixture regression tests unless a documented provider constraint forces a different choice.
- Keep old scoring outputs interpretable by recording calculation and scoring versions.

### Dependencies

- Blocked by: STORY-001
- Blocks: STORY-008, STORY-009, STORY-010

### GitHub Issue Body

Decide and document the MVP indicator ownership strategy. Cover each required technical signal, provider fallback rules, numerical-test expectations, and scoring reproducibility requirements.

---

## STORY-008: Compute Core Technical Indicators

**Type**: Technical
**Priority**: High
**Complexity**: Medium
**Phase**: 2 - Technical Indicator Pipeline
**Labels**: `type:technical`, `scoring`, `backend`, `testing`
**GitHub Issue**: [#8](https://github.com/DaDanielL/NookScout/issues/8)
**Source**: `MVP Scope / Technical setup scoring`, `Indicator and Scoring Logic`, `Implementation Phases / 2 - Technical Indicator Pipeline`

### Description

As a developer, I want deterministic core indicator calculations, so that setup scoring can evaluate trend, momentum, volume, and volatility consistently.

### Acceptance Criteria

- [ ] `app/indicators/technical.py` computes 20/50/200 moving averages, RSI, MACD, relative volume, and ATR from normalized daily candles.
- [ ] Indicator outputs include enough recent values and metadata for scoring and explanation.
- [ ] Incomplete candle histories return explicit incomplete-data states instead of fabricated values.
- [ ] Fixture tests cover expected values, insufficient history, flat price series, volatile series, and missing volume.

### Technical Notes

- Use pandas/NumPy and avoid notebook-only implementation.
- Keep indicator function inputs provider-neutral.
- Make periods configurable where it does not complicate the MVP.

### Dependencies

- Blocked by: STORY-003, STORY-007
- Blocks: STORY-009, STORY-010, STORY-011

### GitHub Issue Body

Implement deterministic core technical indicators for moving averages, RSI, MACD, relative volume, and ATR. Include incomplete-data states and fixture tests.

---

## STORY-009: Compute Support, Resistance, and Relative Strength Signals

**Type**: Technical
**Priority**: High
**Complexity**: Medium
**Phase**: 2 - Technical Indicator Pipeline
**Labels**: `type:technical`, `scoring`, `backend`, `testing`
**GitHub Issue**: [#9](https://github.com/DaDanielL/NookScout/issues/9)
**Source**: `MVP Scope / Technical setup scoring`, `Open Questions`, `Implementation Phases / 2 - Technical Indicator Pipeline`

### Description

As a developer, I want support/resistance and benchmark-relative strength signals, so that setup scoring can reason about key chart levels and stock strength versus broad market benchmarks.

### Acceptance Criteria

- [ ] Support and resistance helpers identify recent swing levels or zones from daily candle data with documented parameters.
- [ ] Relative strength is computed versus SPY and/or QQQ by default, with the sector-relative-strength open question explicitly deferred or documented.
- [ ] Outputs identify incomplete benchmark data separately from weak relative strength.
- [ ] Fixture tests cover breakout, pullback-near-support, failed-resistance, outperforming-benchmark, and underperforming-benchmark scenarios.

### Technical Notes

- Keep support/resistance heuristics simple, transparent, and documented for beginner-facing explanations.
- Fetch or cache benchmark candles through the same market data layer.
- Avoid implying certainty from support or resistance zones.

### Dependencies

- Blocked by: STORY-004, STORY-008
- Blocks: STORY-010, STORY-011, STORY-013

### GitHub Issue Body

Implement support/resistance and relative strength calculations. Default to SPY/QQQ unless documented otherwise, expose incomplete benchmark states, and add fixture tests.

---

## STORY-010: Persist Indicator Snapshots and Refresh Pipeline

**Type**: Technical
**Priority**: High
**Complexity**: Medium
**Phase**: 2 - Technical Indicator Pipeline
**Labels**: `type:technical`, `database`, `scoring`, `backend`, `testing`
**GitHub Issue**: [#10](https://github.com/DaDanielL/NookScout/issues/10)
**Source**: `Architecture / Indicator layer`, `Architecture / Job layer`, `Data and State`, `Implementation Phases / 2 - Technical Indicator Pipeline`

### Description

As a developer, I want indicator snapshots persisted and refreshed from cached candle data, so that setup runs can be reproduced and old ideas can be interpreted later.

### Acceptance Criteria

- [ ] Indicator snapshot models store ticker, calculation date, input candle range, indicator values, incomplete-data flags, and calculation version.
- [ ] A service or job recomputes indicators from cached candles for a ticker set without calling providers directly from indicator code.
- [ ] Repository tests cover snapshot creation, latest snapshot lookup, versioned snapshot lookup, and incomplete-data persistence.
- [ ] Refresh failures are logged with ticker and calculation context without secrets.

### Technical Notes

- APScheduler can orchestrate local refreshes once job scaffolding exists.
- Version indicator calculations from the first implementation.
- Keep this pipeline callable by Scout Mode and Watchlist Mode setup generation.

### Dependencies

- Blocked by: STORY-006, STORY-008, STORY-009
- Blocks: STORY-011, STORY-016

### GitHub Issue Body

Persist indicator snapshots and add a refresh service or local job that computes indicators from cached candles. Include versioning, incomplete-data states, repositories, and tests.

---

## STORY-011: Define Setup Scoring Schemas and Version Contracts

**Type**: Technical
**Priority**: High
**Complexity**: Small
**Phase**: 3 - Setup Scoring Engine
**Labels**: `type:technical`, `scoring`, `backend`, `api`
**GitHub Issue**: [#11](https://github.com/DaDanielL/NookScout/issues/11)
**Source**: `Key Files / app/scoring/models.py`, `Indicator and Scoring Logic`, `Future Extension Considerations`

### Description

As a developer, I want typed setup scoring inputs and outputs, so that scoring, persistence, API responses, UI cards, charts, and LLM rationale all share one structured contract.

### Acceptance Criteria

- [ ] `app/scoring/models.py` defines scoring inputs, setup outputs, confidence factors, setup levels, failure conditions, and setup type enums.
- [ ] Schemas cover bullish setup labels, `No Clear Setup`, `Avoid / Wait`, risk/reward, expected holding window, and structured signal explanations.
- [ ] A scoring version and rationale version field are part of the setup idea contract.
- [ ] Tests validate required fields and reject outputs missing entry, stop/invalidation, target, or failure-case data when a trade-plan setup is produced.

### Technical Notes

- Keep domain models distinct from persistence and API schemas when responsibilities differ.
- Include enough chart-level structure for overlay rendering later.
- Avoid language in enums or labels that implies a direct buy/sell instruction.

### Dependencies

- Blocked by: STORY-008, STORY-009, STORY-010
- Blocks: STORY-012, STORY-013, STORY-014, STORY-016, STORY-018, STORY-019

### GitHub Issue Body

Define typed scoring contracts for setup inputs, outputs, levels, confidence factors, setup labels, versions, and failure conditions. Add validation tests for complete setup outputs.

---

## STORY-012: Classify Bullish Setup Types and No Clear Setup Outcomes

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 3 - Setup Scoring Engine
**Labels**: `type:feature`, `scoring`, `backend`, `testing`
**GitHub Issue**: [#12](https://github.com/DaDanielL/NookScout/issues/12)
**Source**: `MVP Scope / Bullish long setup ideas only`, `MVP Scope / Setup type labels`, `Implementation Phases / 3 - Setup Scoring Engine`

### Description

As a beginner swing trader, I want NookScout to classify only beginner-friendly bullish long setups or wait states, so that the MVP avoids short-selling workflows and confusing bearish trade ideas.

### Acceptance Criteria

- [ ] The scoring engine classifies eligible tickers into `Breakout Watch`, `Pullback Setup`, `Trend Continuation`, `Reversal Watch`, `No Clear Setup`, or `Avoid / Wait`.
- [ ] Weak or incomplete tickers are never transformed into short ideas.
- [ ] Each non-wait setup includes structured reasons tied to trend, momentum, volume, support/resistance, volatility, and relative strength signals.
- [ ] Tests cover each setup type, no-clear-setup cases, avoid/wait cases, and incomplete indicator inputs.

### Technical Notes

- Keep setup classification deterministic and transparent.
- Start with simple weighted rules that can be explained in `docs/scoring-methodology.md`.
- Do not use the LLM to classify setups.

### Dependencies

- Blocked by: STORY-011
- Blocks: STORY-015, STORY-016, STORY-019

### GitHub Issue Body

Implement deterministic bullish setup classification and wait states. Cover required setup labels, avoid short ideas, include structured reasons, and add tests for each classification path.

---

## STORY-013: Calculate Entry, Invalidation, Target, Risk/Reward, and Holding Window

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 3 - Setup Scoring Engine
**Labels**: `type:feature`, `scoring`, `backend`, `testing`
**GitHub Issue**: [#13](https://github.com/DaDanielL/NookScout/issues/13)
**Source**: `MVP Scope / Ranked setup card summary`, `MVP Scope / Expanded setup detail`, `MVP Scope / Expected holding window`

### Description

As a beginner swing trader, I want each setup idea to include clear chart levels and risk/reward context, so that I can evaluate the idea as an educational trade-plan candidate.

### Acceptance Criteria

- [ ] The scoring engine produces entry zone, stop/invalidation area, target area, risk/reward estimate, and failure case for each actionable setup.
- [ ] Expected holding window is labeled and defaults to the PRD range of 3 to 20 trading days unless the setup is non-actionable.
- [ ] Level calculations use deterministic price, ATR, support/resistance, and trend inputs rather than LLM-generated prices.
- [ ] Tests cover valid reward/risk math, invalid or negative risk cases, missing level inputs, ATR-sensitive stops, and non-actionable setup behavior.

### Technical Notes

- Prefer zones over precise instructions where appropriate for educational framing.
- Keep invalidation and stop language clear but non-advisory.
- Chart overlays in STORY-029 will consume these structured levels.

### Dependencies

- Blocked by: STORY-009, STORY-011
- Blocks: STORY-015, STORY-016, STORY-019, STORY-029

### GitHub Issue Body

Implement deterministic setup levels, risk/reward estimates, failure cases, and expected holding windows. Add tests for math, missing data, and non-actionable states.

---

## STORY-014: Calibrate Confidence Labels for Educational Use

**Type**: Spike
**Priority**: High
**Complexity**: Small
**Phase**: 3 - Setup Scoring Engine
**Labels**: `type:spike`, `scoring`, `docs`, `compliance`
**GitHub Issue**: [#14](https://github.com/DaDanielL/NookScout/issues/14)
**Source**: `Open Questions`, `MVP Scope / Ranked setup card summary`, `LLM Rationale`

### Description

As a product owner, I want confidence labels calibrated without implying certainty, so that ranked setup ideas remain educational and non-personalized.

### Acceptance Criteria

- [ ] Confidence label names, score bands, and allowed explanatory copy are documented in `docs/scoring-methodology.md`.
- [ ] The decision explicitly avoids certainty, guaranteed returns, and individualized financial advice.
- [ ] Confidence factors are tied to deterministic scoring inputs and not generated by the LLM.
- [ ] Follow-up implementation notes identify how the frontend and API should display confidence labels.

### Technical Notes

- Consider labels like low, moderate, and strong only if their definitions stay educational.
- This spike should inform scoring tests and LLM guardrails.
- Coordinate with STORY-017 for forbidden financial-advice language.

### Dependencies

- Blocked by: STORY-011
- Blocks: STORY-015, STORY-016, STORY-017, STORY-019, STORY-022

### GitHub Issue Body

Decide confidence label names, score bands, and educational display language. Document the policy and ensure labels come from deterministic factors rather than LLM output.

---

## STORY-015: Add Scoring Fixture Regression Tests

**Type**: Technical
**Priority**: High
**Complexity**: Medium
**Phase**: 3 - Setup Scoring Engine
**Labels**: `type:technical`, `scoring`, `testing`
**GitHub Issue**: [#15](https://github.com/DaDanielL/NookScout/issues/15)
**Source**: `Testing`, `Validation`, `Success Metrics / Setup completeness`

### Description

As a developer, I want fixture-based scoring regression tests, so that changes to indicators or scoring rules do not silently degrade setup quality.

### Acceptance Criteria

- [ ] `tests/fixtures/` includes representative candle series for breakout, pullback, trend continuation, reversal watch, no-clear-setup, avoid/wait, and incomplete-data scenarios.
- [ ] Tests assert setup type, confidence label, key confidence factors, level completeness, failure case presence, and expected holding window behavior.
- [ ] Regression tests run under `uv run pytest` without live-provider calls.
- [ ] A setup completeness helper verifies the PRD-required fields for generated setup ideas.

### Technical Notes

- Keep expected outputs readable enough to review in code review.
- Use tolerances for numerical indicators where appropriate.
- This story may update `docs/scoring-methodology.md` with fixture scenario descriptions.

### Dependencies

- Blocked by: STORY-012, STORY-013, STORY-014
- Blocks: STORY-016, STORY-019, STORY-031

### GitHub Issue Body

Add fixture regression tests for setup scoring and completeness. Cover all setup labels, expected fields, confidence factors, failure cases, holding windows, and no live-provider calls.

---

## STORY-016: Persist Setup Runs and Ranked Setup Ideas

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 4 - Setup Synthesis
**Labels**: `type:feature`, `scoring`, `database`, `backend`, `api`, `testing`
**GitHub Issue**: [#16](https://github.com/DaDanielL/NookScout/issues/16)
**Source**: `Implementation Phases / 4 - Setup Synthesis`, `Data and State`, `Future Extension Considerations`

### Description

As a NookScout user, I want setup scans saved as ranked runs, so that I can review reproducible setup ideas generated from the same data and scoring version.

### Acceptance Criteria

- [ ] Setup run models store run type, ticker universe or watchlist scope, timestamps, status, scoring version, and input data version references.
- [ ] Setup idea models store rank, ticker, setup type, confidence, levels, risk/reward, technical factors, rationale version placeholder, and failure case.
- [ ] A service generates ranked setup ideas for an eligible ticker set and persists no-clear-setup or avoid/wait outcomes as appropriate.
- [ ] Repository and service tests cover successful runs, partial incomplete-data runs, no-setup runs, and reproducible lookup of old runs.

### Technical Notes

- Keep setup runs independent of the UI so scheduled scans can reuse the same service.
- Store structured setup inputs and outputs to support future journaling and evaluation agents.
- Do not require LLM rationale for deterministic setup persistence.

### Dependencies

- Blocked by: STORY-005, STORY-010, STORY-012, STORY-013, STORY-014, STORY-015
- Blocks: STORY-018, STORY-019, STORY-022, STORY-026

### GitHub Issue Body

Persist setup runs and ranked setup ideas. Include run scope, status, scoring versions, structured setup fields, no-setup outcomes, and tests for reproducibility and incomplete data.

---

## STORY-017: Define Educational Disclaimer and Forbidden Financial Advice Language

**Type**: Spike
**Priority**: High
**Complexity**: Small
**Phase**: 4 - Setup Synthesis
**Labels**: `type:spike`, `compliance`, `docs`, `llm`, `frontend`
**GitHub Issue**: [#17](https://github.com/DaDanielL/NookScout/issues/17)
**Source**: `Open Questions`, `LLM Rationale`, `Security Notes`, `Documentation`

### Description

As a product owner, I want educational-use and forbidden-language rules documented, so that setup rationale and UI copy avoid personalized financial advice.

### Acceptance Criteria

- [ ] `docs/disclaimer.md` defines educational-use, non-personalized-financial-advice language for the MVP.
- [ ] A forbidden-language checklist covers certainty, guarantees, direct buy/sell instructions, individualized suitability, and brokerage/order language.
- [ ] The documentation identifies where the disclaimer should appear in the API, UI, README, and LLM validation.
- [ ] Follow-up notes specify how to validate LLM output against forbidden language.

### Technical Notes

- This is not legal advice; capture product-safe wording and mark any legal-review assumptions.
- Keep compliance language concise enough for beginner-facing UI.
- This story blocks rationale generation and final docs.

### Dependencies

- Blocked by: STORY-014
- Blocks: STORY-018, STORY-019, STORY-022, STORY-023, STORY-033

### GitHub Issue Body

Document educational-use disclaimer language and forbidden financial-advice phrasing. Identify UI/API/LLM validation touchpoints and legal-review assumptions.

---

## STORY-018: Generate Beginner-Friendly LLM Rationale from Structured Setup Data

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 4 - Setup Synthesis
**Labels**: `type:feature`, `llm`, `scoring`, `backend`, `testing`
**GitHub Issue**: [#18](https://github.com/DaDanielL/NookScout/issues/18)
**Source**: `MVP Scope / Beginner-friendly signal explanations`, `LLM Rationale`, `Implementation Phases / 4 - Setup Synthesis`

### Description

As a beginner swing trader, I want setup rationale explained in plain language, so that I can understand the technical signals without relying on invented or advisory claims.

### Acceptance Criteria

- [ ] `app/llm/prompts.py` defines structured prompt contracts that include only normalized setup data from deterministic code.
- [ ] `app/llm/service.py` validates structured outputs for thesis summary, expanded rationale, signal explanations, and failure case.
- [ ] Guardrails reject output that invents prices, indicators, levels, risk/reward values, certainty claims, or direct buy/sell instructions.
- [ ] Tests use mocked LLM responses for valid rationale, missing fields, invented values, and forbidden language.

### Technical Notes

- The LLM may explain setup data but must not classify setups or create chart levels.
- Store rationale version separately from scoring version.
- Keep prompt and validation code free of secrets.

### Dependencies

- Blocked by: STORY-016, STORY-017
- Blocks: STORY-019, STORY-023, STORY-031

### GitHub Issue Body

Implement LLM rationale generation from structured setup data. Add prompt contracts, output validation, hallucination guardrails, forbidden-language checks, and mocked tests.

---

## STORY-019: Expose Setup Summary and Expanded Detail API Responses

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 4 - Setup Synthesis
**Labels**: `type:feature`, `api`, `scoring`, `llm`, `backend`, `testing`
**GitHub Issue**: [#19](https://github.com/DaDanielL/NookScout/issues/19)
**Source**: `MVP Scope / Ranked setup card summary`, `MVP Scope / Expanded setup detail`, `Success Metrics / Setup completeness`

### Description

As a frontend user, I want setup summary and detail endpoints, so that cards, expanded detail panels, and charts can render complete setup information from typed API contracts.

### Acceptance Criteria

- [ ] API responses include rank, ticker, company name, current price, setup type, confidence label, risk/reward estimate, holding window, and one-sentence thesis summary.
- [ ] Expanded detail responses include full thesis, trend context, support/resistance rationale, RSI/MACD interpretation, volume confirmation, ATR/volatility context, relative strength, levels, and failure case.
- [ ] Incomplete data and no-clear-setup states are represented clearly without fake levels or rationale.
- [ ] API tests cover summary list, detail lookup, empty runs, incomplete-data runs, validation errors, and setup completeness checks.

### Technical Notes

- Keep API schemas distinct from domain scoring models if the UI needs different shape or naming.
- Include chart overlay data or stable identifiers for STORY-027 and STORY-029.
- Surface educational disclaimer metadata where appropriate from STORY-017.

### Dependencies

- Blocked by: STORY-011, STORY-012, STORY-013, STORY-014, STORY-015, STORY-016, STORY-017, STORY-018
- Blocks: STORY-021, STORY-022, STORY-023, STORY-026, STORY-027, STORY-031

### GitHub Issue Body

Expose typed setup summary and expanded detail API responses. Include all PRD-required card and detail fields, incomplete-data handling, no-clear-setup states, and API tests.

---

## STORY-020: Decide Whether MVP Saves Individual Setup Ideas

**Type**: Spike
**Priority**: Medium
**Complexity**: Small
**Phase**: 4 - Setup Synthesis
**Labels**: `type:spike`, `frontend`, `database`, `product`
**GitHub Issue**: [#20](https://github.com/DaDanielL/NookScout/issues/20)
**Source**: `Open Questions`, `Success Metrics / Scout Mode usefulness`, `Future Extension Considerations`

### Description

As a product owner, I want to decide whether users can save individual setup ideas in MVP, so that Scout Mode metrics and persistence stay aligned with the intended workflow.

### Acceptance Criteria

- [ ] The decision states whether MVP supports saving individual setup ideas or only watchlists.
- [ ] If setup saving is included, required persistence fields, UI states, and analytics events are listed.
- [ ] If setup saving is deferred, Scout Mode usefulness uses expansion/review events only and the PRD or docs note the deferral.
- [ ] Follow-up stories are created or updated if the decision changes the scope of Scout Mode UI or instrumentation.

### Technical Notes

- The PRD includes a success metric for expanding or saving Scout Mode ideas but lists setup saving as an open question.
- Avoid building trade journaling under this decision; journaling is explicitly out of MVP scope.
- Keep future extension compatibility with saved setup IDs.

### Dependencies

- Blocked by: STORY-016, STORY-019
- Blocks: STORY-022, STORY-030, STORY-031

### GitHub Issue Body

Resolve whether MVP saves individual setup ideas or only watchlists. Update Scout Mode, persistence, and analytics follow-ups based on the decision without adding trade journaling.

---

## STORY-021: Scaffold Frontend App Shell and Typed API Client

**Type**: Technical
**Priority**: High
**Complexity**: Medium
**Phase**: 5 - Scout Mode UI
**Labels**: `type:technical`, `frontend`, `api`, `testing`
**GitHub Issue**: [#21](https://github.com/DaDanielL/NookScout/issues/21)
**Source**: `Tech Stack`, `Architecture / Frontend dashboard`, `Commands`, `Folder Structure`

### Description

As a developer, I want a React, TypeScript, and Vite frontend scaffold with typed API access, so that Scout Mode, Watchlist Mode, and chart features share stable UI foundations.

### Acceptance Criteria

- [ ] `frontend/` contains a Vite React TypeScript app with scripts for dev, lint, typecheck, test, and build.
- [ ] A typed API client handles setup run, setup list, setup detail, watchlist, chart data, and error-response shapes.
- [ ] Shared layout, styles, and reusable loading, empty, and error states are available without creating a marketing landing page.
- [ ] Frontend validation commands run or are documented with any script-name deviations in `AGENTS.md` and `README.md`.

### Technical Notes

- Build the actual app dashboard as the first screen.
- Keep UI dense, calm, and work-focused for swing setup review.
- Follow frontend instructions in `AGENTS.md`, including responsive text and no card nesting.

### Dependencies

- Blocked by: STORY-019
- Blocks: STORY-022, STORY-023, STORY-025, STORY-028, STORY-029

### GitHub Issue Body

Scaffold the frontend app shell and typed API client. Include Vite React TypeScript scripts, shared app states, responsive styling foundations, and no marketing landing page.

---

## STORY-022: Build Scout Mode Ranked Setup Card Dashboard

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 5 - Scout Mode UI
**Labels**: `type:feature`, `frontend`, `scoring`, `api`, `testing`
**GitHub Issue**: [#22](https://github.com/DaDanielL/NookScout/issues/22)
**Source**: `MVP Scope / Scout Mode`, `MVP Scope / Ranked setup card summary`, `Open Questions`

### Description

As a beginner swing trader, I want Scout Mode to show ranked setup cards from the liquid universe, so that I can quickly find stocks worth reviewing without already knowing what to watch.

### Acceptance Criteria

- [ ] Scout Mode loads the latest or requested predefined-universe setup run and displays ranked cards.
- [ ] Each card shows rank, ticker, company name, current price, setup type, confidence label, risk/reward estimate, holding window, and one-sentence thesis summary.
- [ ] The default number of visible setup ideas is documented or configurable, and the UI avoids overwhelming the user.
- [ ] Empty, loading, provider-error, incomplete-data, and no-clear-setup states are displayed clearly.

### Technical Notes

- Use feature grouping under `frontend/src/features/scout/` and reusable setup components where useful.
- Do not turn cards into direct buy/sell instructions.
- Respect the setup save decision from STORY-020 before adding save controls.

### Dependencies

- Blocked by: STORY-005, STORY-014, STORY-016, STORY-017, STORY-019, STORY-020, STORY-021
- Blocks: STORY-023, STORY-031

### GitHub Issue Body

Build Scout Mode ranked setup cards from the predefined liquid universe. Include all summary fields, sensible default count behavior, and clear loading, empty, error, incomplete-data, and no-clear-setup states.

---

## STORY-023: Build Expanded Setup Detail and Signal Explanation UI

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 5 - Scout Mode UI
**Labels**: `type:feature`, `frontend`, `llm`, `scoring`, `testing`
**GitHub Issue**: [#23](https://github.com/DaDanielL/NookScout/issues/23)
**Source**: `MVP Scope / Expanded setup detail`, `MVP Scope / Beginner-friendly signal explanations`, `Success Metrics / User clarity`

### Description

As a beginner swing trader, I want to expand a setup and read plain-language technical rationale, so that I understand why the setup may be worth watching and why it might fail.

### Acceptance Criteria

- [ ] Expanded detail shows full thesis, trend context, support/resistance rationale, RSI/MACD interpretation, volume confirmation, ATR/volatility context, relative strength, entry zone, stop/invalidation area, target area, and failure case.
- [ ] Signal explanations are plain-language and do not overcrowd the default card view.
- [ ] Educational disclaimer or non-advice copy appears in the location defined by STORY-017.
- [ ] UI tests cover expansion, collapsed card behavior, missing rationale, incomplete-data detail, and forbidden direct-action copy snapshots or assertions.

### Technical Notes

- Keep beginner explanations available at the point of need.
- Use the API response from STORY-019 instead of recalculating signal interpretation in the frontend.
- Chart integration can land in STORY-028 and STORY-029.

### Dependencies

- Blocked by: STORY-017, STORY-018, STORY-019, STORY-021, STORY-022
- Blocks: STORY-031, STORY-032

### GitHub Issue Body

Build expanded setup detail UI with beginner-friendly technical rationale, all PRD-required detail fields, failure case, educational disclaimer placement, and UI tests.

---

## STORY-024: Add Watchlist Persistence and CRUD API

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 6 - Watchlist Mode UI
**Labels**: `type:feature`, `watchlists`, `database`, `api`, `backend`, `testing`
**GitHub Issue**: [#24](https://github.com/DaDanielL/NookScout/issues/24)
**Source**: `MVP Scope / Watchlist Mode`, `Architecture / Persistence layer`, `Data and State`

### Description

As a local NookScout user, I want saved watchlists with ticker management, so that I can scan symbols I already care about.

### Acceptance Criteria

- [ ] Watchlist models and repositories support create, rename, list, detail, add ticker, remove ticker, and delete operations for local-only use.
- [ ] API endpoints validate ticker symbols and return clear errors for duplicates, invalid symbols, missing watchlists, and empty watchlists.
- [ ] Watchlist data is persisted locally without user account storage.
- [ ] API and repository tests cover CRUD, ticker validation, duplicate handling, and local-only assumptions.

### Technical Notes

- Keep watchlist persistence ready for a future user owner field without requiring accounts in MVP.
- Treat local watchlists as private by default and do not log full private lists unnecessarily.
- Avoid brokerage, trade journal, or order-placement concepts.

### Dependencies

- Blocked by: STORY-002, STORY-006
- Blocks: STORY-025, STORY-026, STORY-031

### GitHub Issue Body

Add local watchlist persistence and CRUD API. Include ticker validation, duplicate handling, empty states, local-only assumptions, and tests.

---

## STORY-025: Build Watchlist Management UI

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 6 - Watchlist Mode UI
**Labels**: `type:feature`, `watchlists`, `frontend`, `api`, `testing`
**GitHub Issue**: [#25](https://github.com/DaDanielL/NookScout/issues/25)
**Source**: `MVP Scope / Watchlist Mode`, `Success Metrics / Watchlist Mode usefulness`

### Description

As a local NookScout user, I want to create and edit watchlists in the app, so that I can keep a personal set of stocks ready for setup discovery.

### Acceptance Criteria

- [ ] The UI supports creating, renaming, selecting, and deleting watchlists.
- [ ] Users can add and remove tickers with validation feedback for invalid, duplicate, or unsupported symbols.
- [ ] Empty watchlist, loading, API error, and successful update states are clear and usable.
- [ ] Frontend tests cover the main watchlist creation and ticker management flows.

### Technical Notes

- Place feature code under `frontend/src/features/watchlists/`.
- Use compact operational UI rather than landing-page presentation.
- Watchlists remain local-only with no account UX.

### Dependencies

- Blocked by: STORY-021, STORY-024
- Blocks: STORY-026, STORY-031

### GitHub Issue Body

Build Watchlist Mode management UI for local watchlists. Include create, rename, select, delete, add/remove tickers, validation feedback, empty states, and frontend tests.

---

## STORY-026: Run Watchlist-Scoped Setup Discovery

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 6 - Watchlist Mode UI
**Labels**: `type:feature`, `watchlists`, `scoring`, `frontend`, `api`, `testing`
**GitHub Issue**: [#26](https://github.com/DaDanielL/NookScout/issues/26)
**Source**: `MVP Scope / Watchlist Mode`, `Implementation Phases / 6 - Watchlist Mode UI`, `Success Metrics / Watchlist Mode usefulness`

### Description

As a local NookScout user, I want to rank setup ideas only within a selected watchlist, so that I can focus on stocks I already follow.

### Acceptance Criteria

- [ ] An API path starts or retrieves setup runs scoped to a selected watchlist.
- [ ] Watchlist Mode displays ranked setup cards using the same summary and detail components as Scout Mode.
- [ ] Empty watchlists, unsupported tickers, no-clear-setup results, and partial incomplete-data results are handled clearly.
- [ ] Tests cover watchlist-scoped setup generation, UI display, and reuse of setup card behavior.

### Technical Notes

- Reuse setup generation services from STORY-016 and setup API contracts from STORY-019.
- Do not duplicate scoring logic in watchlist code.
- Preserve watchlist analysis analytics events for STORY-031.

### Dependencies

- Blocked by: STORY-016, STORY-019, STORY-024, STORY-025
- Blocks: STORY-031

### GitHub Issue Body

Implement watchlist-scoped setup discovery. Reuse setup services and cards, handle empty and incomplete states, and test API plus frontend flows.

---

## STORY-027: Expose Chart Candle Data and Range API

**Type**: Feature
**Priority**: High
**Complexity**: Small
**Phase**: 7 - Annotated Chart Experience
**Labels**: `type:feature`, `charts`, `api`, `data`, `backend`, `testing`
**GitHub Issue**: [#27](https://github.com/DaDanielL/NookScout/issues/27)
**Source**: `MVP Scope / Annotated price chart`, `MVP Scope / Chart range controls`, `Key Files / frontend/src/charts/SetupChart.tsx`

### Description

As a frontend developer, I want a chart data API with supported ranges, so that setup detail can render daily candles without reaching into provider or database internals.

### Acceptance Criteria

- [ ] The API returns daily OHLCV candles for a setup ticker using supported ranges `1M`, `3M`, `6M`, and `1Y`.
- [ ] The default range is `3M`.
- [ ] Responses include current price marker data or enough information for the frontend to place the current price marker.
- [ ] API tests cover range validation, default range behavior, missing candles, unsupported ticker, and cached data retrieval.

### Technical Notes

- Read candles from the cache created by STORY-006.
- Keep range slicing deterministic and timezone-aware.
- Avoid live provider calls from the chart endpoint unless explicitly routed through market data services.

### Dependencies

- Blocked by: STORY-004, STORY-006, STORY-019
- Blocks: STORY-028, STORY-029

### GitHub Issue Body

Expose a chart data API for daily OHLCV candles with `1M`, `3M`, `6M`, `1Y` ranges and `3M` default. Include current-price marker data and API tests.

---

## STORY-028: Render Daily Candlestick Chart with Range Controls

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 7 - Annotated Chart Experience
**Labels**: `type:feature`, `charts`, `frontend`, `api`, `testing`
**GitHub Issue**: [#28](https://github.com/DaDanielL/NookScout/issues/28)
**Source**: `MVP Scope / Annotated price chart`, `MVP Scope / Chart range controls`, `Tech Stack / TradingView lightweight-charts`

### Description

As a beginner swing trader, I want an interactive daily price chart with range controls, so that I can inspect the setup context over relevant swing-trading timeframes.

### Acceptance Criteria

- [ ] `frontend/src/charts/SetupChart.tsx` renders daily candlesticks using TradingView lightweight-charts.
- [ ] Range controls support `1M`, `3M`, `6M`, and `1Y`, with `3M` selected by default.
- [ ] Loading, empty, missing-candle, and API-error chart states are clear and do not resize the layout unexpectedly.
- [ ] UI or component tests cover range switching and chart data mapping.

### Technical Notes

- Keep the chart read-only for MVP.
- Use stable dimensions and responsive constraints so chart controls do not shift the layout.
- Do not add brokerage or order-entry interactions.

### Dependencies

- Blocked by: STORY-021, STORY-027
- Blocks: STORY-029

### GitHub Issue Body

Render daily candlesticks with TradingView lightweight-charts and range controls for `1M`, `3M`, `6M`, and `1Y`, defaulting to `3M`. Include robust chart states and tests.

---

## STORY-029: Render Read-Only Entry, Stop, Target, and Current Price Overlays

**Type**: Feature
**Priority**: High
**Complexity**: Medium
**Phase**: 7 - Annotated Chart Experience
**Labels**: `type:feature`, `charts`, `frontend`, `scoring`, `testing`
**GitHub Issue**: [#29](https://github.com/DaDanielL/NookScout/issues/29)
**Source**: `MVP Scope / Annotated price chart`, `MVP Scope / Expanded setup detail`, `Indicator and Scoring Logic`

### Description

As a beginner swing trader, I want setup levels overlaid on the chart, so that I can see entry, invalidation, target, and current price context without editing or placing trades.

### Acceptance Criteria

- [ ] The chart renders read-only entry zone, stop/invalidation area, target area, and current price overlays from setup API data.
- [ ] Overlay labels use educational language and do not imply order placement or direct instructions.
- [ ] Missing or non-actionable setup levels are handled without fake overlays.
- [ ] Visual or component tests verify overlay mapping, range changes, and non-overlap of labels across desktop and mobile widths.

### Technical Notes

- Consume deterministic levels from STORY-013 through API responses from STORY-019.
- Keep overlays visually clear but restrained.
- If browser verification tooling is available during implementation, capture screenshots for PR review.

### Dependencies

- Blocked by: STORY-013, STORY-019, STORY-021, STORY-027, STORY-028
- Blocks: STORY-031

### GitHub Issue Body

Render read-only setup overlays on the candlestick chart for entry, stop/invalidation, target, and current price. Handle missing levels and test overlay mapping and responsive label behavior.

---

## STORY-030: Add Local Analytics Event Capture

**Type**: Technical
**Priority**: Medium
**Complexity**: Medium
**Phase**: 8 - MVP Instrumentation
**Labels**: `type:technical`, `telemetry`, `database`, `backend`, `testing`
**GitHub Issue**: [#30](https://github.com/DaDanielL/NookScout/issues/30)
**Source**: `Success Metrics`, `Architecture / telemetry`, `Data and State`

### Description

As a product owner, I want local analytics events captured, so that MVP success metrics can be evaluated without adding hosted user tracking.

### Acceptance Criteria

- [ ] `app/telemetry/` defines typed local analytics events for setup creation, card expansion, setup review, watchlist creation, watchlist analysis, clarity feedback, and weekly activity.
- [ ] Persistence stores event name, timestamp, local session or anonymous identifier, entity references, and metadata without secrets.
- [ ] Event capture can be disabled through settings.
- [ ] Tests cover event validation, persistence, disabled telemetry, and metadata redaction.

### Technical Notes

- Keep local analytics private by default.
- Do not add third-party analytics SDKs in the MVP.
- Coordinate event names with frontend instrumentation in STORY-031.

### Dependencies

- Blocked by: STORY-002, STORY-020
- Blocks: STORY-031, STORY-032

### GitHub Issue Body

Add local analytics event capture for MVP metrics. Include typed events, persistence, disable setting, redaction behavior, and tests.

---

## STORY-031: Track Scout, Watchlist, Setup Review, and Completeness Metrics

**Type**: Technical
**Priority**: Medium
**Complexity**: Medium
**Phase**: 8 - MVP Instrumentation
**Labels**: `type:technical`, `telemetry`, `frontend`, `backend`, `testing`
**GitHub Issue**: [#31](https://github.com/DaDanielL/NookScout/issues/31)
**Source**: `Success Metrics`, `Implementation Phases / 8 - MVP Instrumentation`

### Description

As a product owner, I want NookScout to track core MVP events and setup completeness, so that I can evaluate whether users are creating and reviewing useful setup ideas.

### Acceptance Criteria

- [ ] Setup generation records setup creation and completeness-check outcomes.
- [ ] Scout Mode records card expansion or setup review events, and setup save events only if STORY-020 includes setup saving.
- [ ] Watchlist Mode records watchlist creation and watchlist analysis events.
- [ ] Tests cover event emission for setup generation, card expansion, watchlist creation, watchlist analysis, disabled telemetry, and completeness failures.

### Technical Notes

- Metrics should support the PRD targets for weekly setup engagement, setup completeness, Scout Mode usefulness, and Watchlist Mode usefulness.
- Avoid tracking personal brokerage or account data.
- Keep event emission idempotent where repeated UI renders might otherwise duplicate events.

### Dependencies

- Blocked by: STORY-015, STORY-018, STORY-019, STORY-020, STORY-022, STORY-023, STORY-024, STORY-025, STORY-026, STORY-029, STORY-030
- Blocks: STORY-032

### GitHub Issue Body

Track MVP success events and setup completeness outcomes across setup generation, Scout Mode, Watchlist Mode, and chart/detail review. Include tests and disabled telemetry behavior.

---

## STORY-032: Add Clarity Feedback and Weekly Retention Reporting

**Type**: Feature
**Priority**: Medium
**Complexity**: Medium
**Phase**: 8 - MVP Instrumentation
**Labels**: `type:feature`, `telemetry`, `frontend`, `backend`, `testing`
**GitHub Issue**: [#32](https://github.com/DaDanielL/NookScout/issues/32)
**Source**: `Success Metrics / User clarity`, `Success Metrics / Weekly retention`, `Implementation Phases / 8 - MVP Instrumentation`

### Description

As a product owner, I want lightweight clarity feedback and weekly retention reporting, so that I can judge whether users feel more confident and return weekly.

### Acceptance Criteria

- [ ] A lightweight in-product feedback prompt appears after setup detail review according to a documented trigger rule.
- [ ] Feedback responses are stored locally with timestamp, setup reference, optional rating, and optional short note.
- [ ] A local report or endpoint summarizes weekly active usage, setup review count, Scout Mode usefulness, Watchlist Mode usefulness, and clarity feedback.
- [ ] Tests cover feedback submission, skipped feedback, weekly aggregation, and no-data reporting.

### Technical Notes

- Keep feedback optional and low-friction.
- Do not ask for personal financial situation or suitability information.
- Weekly aggregation can be local-only and simple for MVP.

### Dependencies

- Blocked by: STORY-023, STORY-030, STORY-031
- Blocks: STORY-033

### GitHub Issue Body

Add optional clarity feedback and local weekly retention reporting. Store responses privately, aggregate MVP metrics, and test feedback plus reporting behavior.

---

## STORY-033: Publish MVP Setup, Scoring, Provider, and Disclaimer Documentation

**Type**: Technical
**Priority**: Medium
**Complexity**: Small
**Phase**: 8 - MVP Instrumentation
**Labels**: `type:technical`, `docs`, `compliance`, `testing`
**GitHub Issue**: [#33](https://github.com/DaDanielL/NookScout/issues/33)
**Source**: `Documentation`, `Commands`, `Validation`, `Future Extension Considerations`

### Description

As a developer and local operator, I want MVP documentation kept current, so that setup, validation, scoring behavior, provider assumptions, and disclaimers are clear from day one.

### Acceptance Criteria

- [ ] `README.md` documents local setup, backend and frontend commands, development workflow, and educational-use disclaimer summary.
- [ ] `.env.example` matches the settings needed by provider, database, LLM, telemetry, and local app configuration.
- [ ] `docs/scoring-methodology.md`, `docs/market-data-providers.md`, `docs/disclaimer.md`, and `docs/architecture-decisions.md` reflect implemented MVP behavior.
- [ ] Validation commands from `AGENTS.md` are run and the results are recorded in the PR or implementation report.

### Technical Notes

- Keep docs aligned with any deviations from the original scaffold commands.
- Include no secrets, private watchlists, or provider credentials.
- Document deferred out-of-scope items such as brokerage integration, trade journaling, short ideas, options, catalysts, and backtesting.

### Dependencies

- Blocked by: STORY-001, STORY-007, STORY-014, STORY-017, STORY-032
- Blocks: None

### GitHub Issue Body

Update MVP documentation for setup, commands, environment variables, scoring methodology, provider decisions, disclaimers, architecture decisions, validation results, and deferred out-of-scope items.

---

## Coverage Validation

- [x] Every MVP capability maps to at least one story: Scout Mode, Watchlist Mode, liquid universe filtering, bullish-only setup logic, technical scoring, setup cards, expanded detail, annotated charts, chart ranges, holding window, beginner explanations, setup labels, and instrumentation.
- [x] Every implementation phase maps to ordered stories with blockers before dependent UI or instrumentation work.
- [x] PRD open questions map to spikes or explicit acceptance criteria: provider choice, indicator ownership, liquidity rules, Scout Mode default count, confidence labels, compliance language, benchmark scope, setup saving, and budget/licensing constraints.
- [x] Stories cover domain logic, API, persistence, UI, charting, LLM guardrails, telemetry, tests, docs, and local operations.
- [x] Dependencies form a DAG; no story depends on a later story that also depends on it.
- [x] No story is marked Large; medium stories are scoped to independently reviewable vertical slices.


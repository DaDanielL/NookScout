# Plan: STORY-001 Market Data Provider Decision

## Summary

Create the first market-data decision artifacts for NookScout. The implementation should research current official provider pricing, capabilities, limits, and licensing terms, document a comparison in `docs/market-data-providers.md`, recommend one MVP provider for local-only use, and create `.env.example` entries for the chosen provider without adding secrets or product-code adapters yet.

## User Story

As a local NookScout operator, I want to select the MVP market data provider and document constraints, so that ingestion, scoring, and licensing decisions have a clear foundation.

## Metadata

| Field | Value |
|-------|-------|
| Type | SPIKE |
| Complexity | LOW |
| Systems Affected | Documentation, local configuration, future market data adapter boundary |
| GitHub Issue | #1, https://github.com/DaDanielL/NookScout/issues/1 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-001` |

---

## Patterns to Follow

### Naming

```text
SOURCE: AGENTS.md:177
Use clear domain names such as Watchlist, Ticker, Candle, IndicatorSnapshot, SetupRun, SetupIdea, SetupScore, and Rationale.
```

```text
SOURCE: AGENTS.md:160
Concrete provider adapters should eventually live under app/market_data/{provider}.py, with candidate examples such as Alpaca, Polygon/Massive, or Twelve Data.
```

```text
SOURCE: AGENTS.md:174
docs/market-data-providers.md is the expected provider evaluation, limitations, pricing, and licensing document.
```

### Architecture Boundaries

```text
SOURCE: AGENTS.md:101
Market data provider adapters fetch quotes, daily candles, reference data, and liquidity inputs. Scoring and UI code must not call providers directly.
```

```text
SOURCE: AGENTS.md:199
Access market data only through adapter interfaces, cache candles and reference data, prefer daily candles and fresh quotes, and keep liquidity rules configurable.
```

### Error Handling

```text
SOURCE: AGENTS.md:222
Provider failures should be graceful, incomplete data should surface clearly, logs must avoid API keys, and typed exceptions are preferred once product code exists.
```

### Configuration

```text
SOURCE: AGENTS.md:228
Secrets belong only in environment variables or ignored local .env files; .env.example must stay current and must not contain real API keys or credentials.
```

### Tests and Validation

```text
SOURCE: AGENTS.md:235
Default tests should mock provider behavior and avoid live-provider calls to control cost, rate limits, and flakiness.
```

```text
SOURCE: AGENTS.md:243
Full backend and frontend validation commands are defined, but the app scaffold does not exist yet. This story should use docs/config verification now and leave product validation to later scaffold stories.
```

### AI Layer

```text
SOURCE: .agents/README.md:11
Implementation plans belong under .agents/plans/.
```

```text
SOURCE: .agents/README.md:61
Story manifests keep local STORY-### IDs even when GitHub issues are created, preserving traceability from PRD to story to issue to plan.
```

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `docs/market-data-providers.md` | CREATE | Compare viable market data providers and record the MVP recommendation, constraints, and licensing assumptions. |
| `.env.example` | CREATE | List the selected provider's required local environment variables using placeholders only. |

No product code should be created for this story. The repository currently has no `app/`, `frontend/`, `pyproject.toml`, or package scripts; STORY-002 and later market-data stories will handle scaffold and adapter implementation.

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: Research Current Provider Sources

- **File**: `docs/market-data-providers.md`
- **Action**: CREATE
- **Implement**: Research at least two viable providers using current official sources during implementation. Favor the provider candidates already named in `AGENTS.md`: Alpaca Market Data, Polygon/Massive, and Twelve Data. Capture the research date and source links for pricing, market-data coverage, delayed versus real-time behavior, rate limits, reference data, and licensing or redistribution constraints.
- **Mirror**: `AGENTS.md:199` - keep the research focused on quotes, daily candles, reference data, volume, provider limits, caching, and adapter boundaries.
- **Validate**: `rg -n "Research date|Alpaca|Polygon|Massive|Twelve Data|Licensing|Rate limits" docs/market-data-providers.md`

### Task 2: Build the Provider Comparison Matrix

- **File**: `docs/market-data-providers.md`
- **Action**: CREATE
- **Implement**: Add a comparison table covering quotes, historical daily candles, volume, reference data needed for liquidity filtering, costs, free or paid limits, delayed or real-time data behavior, provider-supplied indicators, API ergonomics, local-only fit, hosted or multi-user licensing risk, and adapter notes.
- **Mirror**: `.agents/stories/nookscout-technical-setup-discovery.stories.md:64` - satisfy every comparison dimension listed in STORY-001 acceptance criteria.
- **Validate**: `rg -n "quotes|historical daily candles|volume|reference data|cost|limits|licensing|indicator" docs/market-data-providers.md`

### Task 3: Record the MVP Recommendation

- **File**: `docs/market-data-providers.md`
- **Action**: CREATE
- **Implement**: Add a clear "MVP Recommendation" section naming one provider, why it is the best initial fit, budget expectations, rate-limit assumptions, delayed or real-time behavior, local-only assumptions, and the known reasons this decision may need to change before hosted or multi-user distribution.
- **Mirror**: `.agents/stories/nookscout-technical-setup-discovery.stories.md:66` - recommend one provider with explicit budget, rate limit, data freshness, and local-only notes.
- **Validate**: `rg -n "MVP Recommendation|Budget|Rate limits|Delayed|Real-time|Local-only|Hosted|Multi-user" docs/market-data-providers.md`

### Task 4: Document Indicator Ownership Boundary

- **File**: `docs/market-data-providers.md`
- **Action**: CREATE
- **Implement**: Record whether each compared provider offers precomputed indicators, but explicitly state that NookScout will not rely on provider-supplied indicators before STORY-007 decides indicator ownership. The wording should preserve deterministic internal scoring as the default product direction.
- **Mirror**: `AGENTS.md:207` - deterministic code owns prices, indicators, setup levels, risk/reward, setup classification, and failure conditions.
- **Validate**: `rg -n "provider-supplied indicators|precomputed indicators|STORY-007|deterministic" docs/market-data-providers.md`

### Task 5: Create Environment Variable Template

- **File**: `.env.example`
- **Action**: CREATE
- **Implement**: Add placeholder environment variables for the recommended provider only. Include a neutral selector such as `NOOKSCOUT_MARKET_DATA_PROVIDER`, the provider API key or token names required by the provider, and any non-secret runtime settings such as base URL, data feed, timeout, or rate-limit guardrails if the chosen provider needs them. Use comments to show expected values without committing secrets.
- **Mirror**: `AGENTS.md:228` - keep secrets out of the repo and keep `.env.example` current whenever settings change.
- **Validate**: `rg -n "NOOKSCOUT_MARKET_DATA_PROVIDER|API|KEY|TOKEN|SECRET|URL|TIMEOUT|RATE" .env.example`

### Task 6: Final Acceptance Pass

- **File**: `docs/market-data-providers.md`, `.env.example`
- **Action**: UPDATE
- **Implement**: Review the diff against STORY-001 acceptance criteria. Confirm the docs compare at least two providers, recommend exactly one MVP provider, list required env vars for that provider, preserve local-only assumptions, warn about hosted or multi-user redistribution risk, and avoid live-provider code or secrets.
- **Mirror**: `.agents/stories/nookscout-technical-setup-discovery.stories.md:64` - all acceptance criteria should be visibly covered.
- **Validate**: `git diff --check`

---

## Risks

| Risk | Mitigation |
|------|------------|
| Provider pricing, rate limits, or licensing terms may have changed recently. | Use current official provider docs during implementation, include a research date, and avoid relying on remembered pricing details. |
| A provider may have attractive technical capabilities but unsuitable redistribution or hosted-use terms. | Separate local-only MVP fit from hosted or multi-user risk in the comparison and recommendation. |
| Provider-supplied indicators could blur deterministic scoring ownership. | Record indicator availability only as context and explicitly defer indicator ownership to STORY-007. |
| `.env.example` could drift from the later settings implementation. | Use provider-specific names that can be mirrored in STORY-002 settings, and update the file again when settings are scaffolded. |
| The repo currently lacks product validation tooling. | Treat this as docs/config validation only and do not run nonexistent backend or frontend commands. |

---

## Validation

The app scaffold is not present yet, so the full `AGENTS.md` validation commands are not runnable for this story. For this docs/config spike, run:

```bash
git diff --check
rg -n "MVP Recommendation|Licensing|Rate limits|provider-supplied indicators|STORY-007" docs/market-data-providers.md
rg -n "NOOKSCOUT_MARKET_DATA_PROVIDER|API|KEY|TOKEN|SECRET" .env.example
```

Once STORY-002 scaffolds backend tooling, future market-data work should use the relevant AGENTS validation commands:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

## End-to-End Verification

- [ ] `docs/market-data-providers.md` can be read by a future implementer and unambiguously identifies the recommended MVP provider.
- [ ] The selected provider's required env vars are documented in `.env.example` with placeholders only.
- [ ] The recommendation explains local-only assumptions and calls out hosted or multi-user redistribution risk.
- [ ] The provider indicators section does not make STORY-007 unnecessary.

## Acceptance Criteria

- [ ] `docs/market-data-providers.md` compares at least two viable providers for quotes, historical daily candles, volume, reference data, cost, limits, and licensing.
- [ ] One provider is recommended for MVP with explicit notes on budget, rate limits, delayed or real-time data behavior, and local-only assumptions.
- [ ] Required environment variables are listed for the chosen provider without committing secrets.
- [ ] The decision records whether provider-supplied indicators are available, but does not rely on them before STORY-007.
- [ ] Implementation follows `AGENTS.md`.

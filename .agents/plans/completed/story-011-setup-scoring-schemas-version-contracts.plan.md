# Plan: Setup Scoring Schemas and Version Contracts

## Summary

Add the first setup scoring domain contracts by creating a new `app/scoring` package with
frozen Pydantic models for scoring inputs, setup ideas, setup labels, confidence factors,
chart overlay levels, risk/reward, expected holding windows, signal explanations, and
failure conditions. This story should not implement the scoring engine, persistence,
API routes, or LLM generation; it should create the shared typed contract that later
stories can consume safely, with validation that trade-plan setup ideas cannot omit
entry, stop/invalidation, target, or failure-case data.

## User Story

As a developer, I want typed setup scoring inputs and outputs, so that scoring,
persistence, API responses, UI cards, charts, and LLM rationale all share one structured
contract.

## Metadata

| Field | Value |
|-------|-------|
| Type | NEW_CAPABILITY |
| Complexity | LOW |
| Systems Affected | Backend scoring domain contracts, backend tests, scoring methodology docs |
| GitHub Issue | #11, https://github.com/DaDanielL/NookScout/issues/11 |
| Source PRD | `.agents/PRDs/nookscout-technical-setup-discovery.prd.md` |
| Source Story | `.agents/stories/nookscout-technical-setup-discovery.stories.md#STORY-011` |

---

## Patterns to Follow

### Naming

```text
SOURCE: AGENTS.md:176
Use clear domain names: Watchlist, Ticker, Candle, IndicatorSnapshot, SetupRun,
SetupIdea, SetupScore, Rationale. Name the new scoring contracts around SetupIdea,
SetupScore, SetupLevel, ConfidenceFactor, SignalExplanation, and FailureCondition.
```

```text
SOURCE: app/indicators/snapshots.py:19
Indicator snapshots use an explicit version constant:
INDICATOR_CALCULATION_VERSION = "indicator-v1".
Mirror this with scoring/rationale version constants such as SCORING_VERSION and
RATIONALE_VERSION.
```

```text
SOURCE: app/indicators/signals.py:22
Domain enums use StrEnum with lowercase provider-neutral string values. Use the same
style for setup labels, level kinds, confidence labels, and setup decision/status values.
```

### Types and Contracts

```text
SOURCE: app/market_data/schemas.py:44
Provider-neutral contracts inherit from frozen MarketDataModel. New scoring contracts
should inherit from MarketDataModel unless there is a specific API DTO reason not to.
```

```text
SOURCE: app/market_data/schemas.py:50
normalize_symbol centralizes ticker validation and normalization. Setup scoring inputs
and outputs should use it for every symbol field.
```

```text
SOURCE: app/indicators/technical.py:157
TechnicalIndicatorSnapshot is the existing typed indicator payload intended for scoring.
SetupScoringInput should accept this rather than re-shaping indicator internals.
```

```text
SOURCE: app/indicators/signals.py:164
SupportResistanceSnapshot provides latest support/resistance levels and chart context.
SetupScoringInput should consume it directly for later setup level derivation.
```

```text
SOURCE: app/indicators/signals.py:307
RelativeStrengthSnapshot provides benchmark-relative labels and comparisons. Include it
in SetupScoringInput so future scoring and rationale share the same source data.
```

### Validation

```text
SOURCE: app/market_data/schemas.py:123
Cross-field invariants use model_validator(mode="after"). Use model validators for
trade-plan completeness, level ordering, risk/reward coherence, and holding-window
coherence.
```

```text
SOURCE: app/indicators/snapshots.py:68
Timezone-aware calculation timestamps are validated explicitly. Setup scoring inputs and
ideas should require timezone-aware scored_at/as_of timestamps.
```

```text
SOURCE: app/indicators/signals.py:135
Price zones validate that zone_low <= zone_high and that representative prices are
inside the zone. Setup level zones should validate the same chart-overlay invariant.
```

```text
SOURCE: AGENTS.md:207
Deterministic code owns setup levels, risk/reward, classification, confidence factors,
and failure conditions. LLMs may explain these fields but must not invent them.
```

### Error Handling

```text
SOURCE: AGENTS.md:221
Prefer typed exceptions for provider, scoring, persistence, and LLM failures. For this
schema-only story, use Pydantic validation errors for malformed contracts and avoid
adding service-level exceptions until the scoring engine exists.
```

```text
SOURCE: AGENTS.md:211
If required structured inputs are missing, return No Clear Setup or an explicit
incomplete-data state. Model validators should distinguish non-trade outputs from
trade-plan setup ideas.
```

### Tests

```text
SOURCE: tests/market_data/test_schemas.py:73
Schema tests build payload dictionaries, validate models with model_validate, and assert
normalization and enum coercion.
```

```text
SOURCE: tests/indicators/test_technical.py:95
Incomplete indicator behavior is asserted explicitly. Scoring schema tests should assert
No Clear Setup and Avoid / Wait outputs are valid without trade-plan levels.
```

```text
SOURCE: tests/persistence/test_indicator_snapshots.py:56
Tests assert version metadata, normalized symbols, and persisted contract fields
directly. Scoring tests should assert scoring_version and rationale_version defaults.
```

---

## Proposed Contract Design

Implement in `app/scoring/models.py`.

### Constants

- `SCORING_VERSION = "scoring-v1"`
- `RATIONALE_VERSION = "rationale-v1"`

### Enums

- `SetupLabel`
  - `BULLISH_BREAKOUT = "bullish_breakout"`
  - `BULLISH_PULLBACK = "bullish_pullback"`
  - `BULLISH_CONTINUATION = "bullish_continuation"`
  - `NO_CLEAR_SETUP = "no_clear_setup"`
  - `AVOID_WAIT = "avoid_wait"`
  - `INCOMPLETE_DATA = "incomplete_data"`
- `ConfidenceLabel`
  - `LOW = "low"`
  - `MODERATE = "moderate"`
  - `HIGH = "high"`
- `SetupLevelKind`
  - `CURRENT_PRICE = "current_price"`
  - `ENTRY_ZONE = "entry_zone"`
  - `STOP_INVALIDATION = "stop_invalidation"`
  - `TARGET_ZONE = "target_zone"`
  - `SUPPORT = "support"`
  - `RESISTANCE = "resistance"`
- `SignalCategory`
  - `TREND = "trend"`
  - `MOMENTUM = "momentum"`
  - `VOLUME = "volume"`
  - `VOLATILITY = "volatility"`
  - `SUPPORT_RESISTANCE = "support_resistance"`
  - `RELATIVE_STRENGTH = "relative_strength"`
  - `RISK_REWARD = "risk_reward"`
  - `DATA_QUALITY = "data_quality"`
- `SignalPolarity`
  - `SUPPORTIVE = "supportive"`
  - `NEUTRAL = "neutral"`
  - `CAUTION = "caution"`

Maintain a module-level `TRADE_PLAN_LABELS` tuple or frozenset containing only the
bullish setup labels. This keeps validators explicit and avoids treating No Clear Setup
or Avoid / Wait as trade-plan ideas.

### Models

- `SetupScoringInput`
  - `symbol`
  - `provider`
  - `scored_at`
  - `indicator_snapshot_id: int | None`
  - `indicator_calculation_version`
  - `technical_snapshot: TechnicalIndicatorSnapshot`
  - `support_resistance_snapshot: SupportResistanceSnapshot`
  - `relative_strength_snapshot: RelativeStrengthSnapshot`
  - Validate symbol, provider/version text, positive snapshot id when present, and
    timezone-aware `scored_at`.
- `SetupLevel`
  - `kind: SetupLevelKind`
  - `label`
  - `price: PositiveDecimal | None = None`
  - `zone_low: PositiveDecimal | None = None`
  - `zone_high: PositiveDecimal | None = None`
  - `source`
  - `display_order: int`
  - Validate non-empty labels/source, non-negative display order, at least one price or
    zone, and coherent zone bounds. If `price`, `zone_low`, and `zone_high` are all
    present, require `price` inside the zone.
- `ExpectedHoldingWindow`
  - `min_trading_days: int = 3`
  - `max_trading_days: int = 20`
  - `label: str = "3 to 20 trading days"`
  - Validate positive days and `min_trading_days <= max_trading_days`.
- `RiskRewardEstimate`
  - `risk_per_share: PositiveDecimal`
  - `reward_per_share: PositiveDecimal`
  - `ratio: PositiveDecimal`
  - Optional `notes`
  - Validate required positive values. Do not compute ratios here unless the existing
    fields clearly support a deterministic check without rounding surprises.
- `FailureCondition`
  - `label`
  - `description`
  - `level: SetupLevel | None = None`
  - `signal_category: SignalCategory | None = None`
  - Validate non-empty label and description.
- `ConfidenceFactor`
  - `name`
  - `category: SignalCategory`
  - `polarity: SignalPolarity`
  - `score_impact: int`
  - `explanation`
  - Validate non-empty name/explanation.
- `SignalExplanation`
  - `category: SignalCategory`
  - `polarity: SignalPolarity`
  - `title`
  - `summary`
  - Optional `value`, `source`
  - Validate non-empty title and summary. This becomes the structured handoff to UI and
    LLM rationale.
- `SetupTradePlan`
  - `entry: SetupLevel`
  - `stop_invalidation: SetupLevel`
  - `target: SetupLevel`
  - `risk_reward: RiskRewardEstimate`
  - `expected_holding_window: ExpectedHoldingWindow`
  - `failure_conditions: tuple[FailureCondition, ...]`
  - Validate level kinds match their roles and `failure_conditions` is non-empty.
- `SetupIdea`
  - `symbol`
  - `setup_label: SetupLabel`
  - `score: int`
  - `confidence: ConfidenceLabel`
  - `scored_at`
  - `scoring_version: str = SCORING_VERSION`
  - `rationale_version: str = RATIONALE_VERSION`
  - `indicator_snapshot_id: int | None = None`
  - `trade_plan: SetupTradePlan | None = None`
  - `confidence_factors: tuple[ConfidenceFactor, ...]`
  - `signal_explanations: tuple[SignalExplanation, ...]`
  - `no_setup_reasons: tuple[str, ...] = ()`
  - Validate:
    - trade-plan labels require `trade_plan`
    - trade-plan labels require entry, stop/invalidation, target, risk/reward, holding
      window, and at least one failure condition through `SetupTradePlan`
    - non-trade labels (`no_clear_setup`, `avoid_wait`, `incomplete_data`) must not carry
      a `trade_plan`
    - non-trade labels should include at least one `no_setup_reasons` item
    - symbol and version fields are normalized/non-empty
    - `scored_at` is timezone-aware

Keep the wording educational and descriptive. Avoid enum or field names such as `buy`,
`sell`, `order`, `execute`, or `recommendation`.

---

## Files to Change

| File | Action | Purpose |
|------|--------|---------|
| `app/scoring/__init__.py` | CREATE | Export scoring model contracts and version constants from the new scoring package. |
| `app/scoring/models.py` | CREATE | Define setup scoring input/output schemas, enums, setup levels, confidence factors, signal explanations, risk/reward, holding window, failure conditions, and validation rules. |
| `tests/scoring/__init__.py` | CREATE | Mark scoring tests as a package, consistent with existing test folders. |
| `tests/scoring/test_models.py` | CREATE | Validate scoring model normalization, version defaults, valid trade-plan outputs, no-clear/wait outputs, and rejection of incomplete trade-plan outputs. |
| `docs/scoring-methodology.md` | UPDATE | Record that setup scoring contracts now exist while scoring/ranking logic remains planned for later stories. |

No database migration, API route, repository, scheduler, frontend, or LLM files should be
changed in this story.

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: Create the Scoring Package Shell

- **File**: `app/scoring/__init__.py`
- **Action**: CREATE
- **Implement**: Add a package docstring, import all public contracts from
  `app.scoring.models`, and define `__all__` explicitly.
- **Mirror**: `app/indicators/__init__.py:1` - package-level exports for domain
  contracts.
- **Validate**: `uv run ruff check app/scoring tests/scoring`

### Task 2: Define Version Constants and Enums

- **File**: `app/scoring/models.py`
- **Action**: CREATE
- **Implement**: Add module docstring, future annotations, imports, `SCORING_VERSION`,
  `RATIONALE_VERSION`, `SetupLabel`, `ConfidenceLabel`, `SetupLevelKind`,
  `SignalCategory`, `SignalPolarity`, and `TRADE_PLAN_LABELS`.
- **Mirror**: `app/indicators/snapshots.py:19` for version constants and
  `app/indicators/signals.py:22` for StrEnum naming.
- **Validate**: `uv run mypy app/scoring tests/scoring`

### Task 3: Define Input and Shared Helper Models

- **File**: `app/scoring/models.py`
- **Action**: UPDATE
- **Implement**: Add `SetupScoringInput`, `SetupLevel`, `ExpectedHoldingWindow`,
  `RiskRewardEstimate`, `FailureCondition`, `ConfidenceFactor`, and
  `SignalExplanation`. Use `MarketDataModel`, `normalize_symbol`,
  `normalize_required_text`, `PositiveDecimal`, and typed indicator snapshots.
- **Mirror**: `app/market_data/schemas.py:44` for frozen model contracts,
  `app/market_data/schemas.py:50` for symbol normalization, and
  `app/indicators/snapshots.py:68` for timezone validation.
- **Validate**: `uv run pytest tests/scoring/test_models.py`

### Task 4: Define Setup Trade Plan and Setup Idea Validators

- **File**: `app/scoring/models.py`
- **Action**: UPDATE
- **Implement**: Add `SetupTradePlan` and `SetupIdea` with model validators enforcing
  trade-plan completeness and non-trade output behavior. Ensure bullish setup labels
  require entry, stop/invalidation, target, risk/reward, expected holding window, and
  failure conditions; ensure `No Clear Setup`, `Avoid / Wait`, and incomplete-data
  outputs carry reasons and no trade plan.
- **Mirror**: `app/market_data/schemas.py:123` and `app/indicators/signals.py:135` for
  cross-field validators.
- **Validate**: `uv run pytest tests/scoring/test_models.py`

### Task 5: Add Focused Scoring Schema Tests

- **File**: `tests/scoring/__init__.py`
- **Action**: CREATE
- **Implement**: Add a simple package marker.
- **Mirror**: `tests/indicators/__init__.py` and `tests/persistence/__init__.py`.
- **Validate**: `uv run pytest tests/scoring`

- **File**: `tests/scoring/test_models.py`
- **Action**: CREATE
- **Implement**: Add fixture builders for levels, risk/reward, failure conditions,
  signal explanations, and setup ideas. Cover:
  - valid bullish trade-plan setup normalizes symbol and applies scoring/rationale
    version defaults
  - valid `NO_CLEAR_SETUP` output without trade-plan levels
  - valid `AVOID_WAIT` output without trade-plan levels
  - trade-plan setup rejects missing `trade_plan`
  - trade-plan setup rejects missing/incorrect entry, stop/invalidation, target, or
    failure-case data
  - non-trade setup rejects an attached trade plan
  - invalid level zones and invalid holding windows raise `ValidationError`
- **Mirror**: `tests/market_data/test_schemas.py:73` for Pydantic schema tests and
  `tests/indicators/test_technical.py:95` for explicit incomplete-state tests.
- **Validate**: `uv run pytest tests/scoring/test_models.py`

### Task 6: Update Scoring Methodology Documentation

- **File**: `docs/scoring-methodology.md`
- **Action**: UPDATE
- **Implement**: Update the implementation status section to say setup scoring schemas
  and version contracts are implemented by STORY-011, while actual scoring/ranking logic
  remains planned. Add a short section describing the shared setup idea contract, the
  required trade-plan levels, no-clear/wait behavior, and the `scoring-v1` /
  `rationale-v1` version fields.
- **Mirror**: `docs/scoring-methodology.md:394` for persisted indicator snapshot
  documentation style and `docs/scoring-methodology.md:431` for future scoring notes.
- **Validate**: `uv run ruff format --check .`

### Task 7: Run Full Backend Validation

- **File**: N/A
- **Action**: VALIDATE
- **Implement**: Run the backend commands from `AGENTS.md`.
- **Mirror**: `AGENTS.md:247` - project validation commands.
- **Validate**:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run mypy .`
  - `uv run pytest`

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Schema names imply direct trading advice or execution. | Use educational labels such as `entry_zone`, `stop_invalidation`, and `target_zone`; avoid buy/sell/order/execute language. |
| Trade-plan outputs could be partially populated and break future UI/LLM consumers. | Centralize completeness checks in `SetupTradePlan` and `SetupIdea` validators, then test each missing required piece. |
| No-clear or wait states get forced into trade-plan shape. | Keep `TRADE_PLAN_LABELS` explicit and require reasons for non-trade labels while rejecting attached trade plans. |
| Version fields are forgotten in later persistence/API work. | Put `scoring_version` and `rationale_version` directly on `SetupIdea` with defaults and tests. |
| Scope expands into scoring logic or persistence. | Limit this story to contracts, exports, tests, and docs. Defer engine, API, repositories, migrations, and LLM service to dependent stories. |
| Decimal/float inconsistencies appear at chart level boundaries. | Use Decimal for setup price/risk contracts, while consuming existing indicator floats only through typed snapshots. |

---

## Validation

Run these exact backend commands:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

For a narrow development loop while implementing:

```bash
uv run pytest tests/scoring/test_models.py
uv run mypy app/scoring tests/scoring
```

## End-to-End Verification

- [ ] `tests/scoring/test_models.py` can construct a complete bullish setup idea with
      entry, stop/invalidation, target, risk/reward, expected holding window, failure
      conditions, signal explanations, confidence factors, and version fields.
- [ ] The same test module rejects a bullish setup idea when any required trade-plan
      component is absent.
- [ ] `No Clear Setup`, `Avoid / Wait`, and incomplete-data outputs validate without
      trade-plan levels and include explicit reasons.
- [ ] Full backend validation passes.

## Acceptance Criteria

- [ ] `app/scoring/models.py` defines scoring inputs, setup outputs, confidence factors,
      setup levels, failure conditions, and setup type enums.
- [ ] Schemas cover bullish setup labels, `No Clear Setup`, `Avoid / Wait`, risk/reward,
      expected holding window, and structured signal explanations.
- [ ] A scoring version and rationale version field are part of the setup idea contract.
- [ ] Tests validate required fields and reject outputs missing entry, stop/invalidation,
      target, or failure-case data when a trade-plan setup is produced.
- [ ] Relevant tests added.
- [ ] Validation commands pass.
- [ ] Implementation follows `AGENTS.md`.

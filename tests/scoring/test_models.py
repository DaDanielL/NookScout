"""Setup scoring contract tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.indicators.signals import (
    RelativeStrengthConfig,
    SupportResistanceConfig,
    calculate_relative_strength,
    calculate_support_resistance,
)
from app.indicators.technical import IndicatorConfig, calculate_technical_indicators
from app.market_data.schemas import DailyCandle
from app.scoring.models import (
    RATIONALE_VERSION,
    SCORING_VERSION,
    ConfidenceLabel,
    ExpectedHoldingWindow,
    SetupIdea,
    SetupLabel,
    SetupLevel,
    SetupLevelKind,
    SetupScoringInput,
    SignalCategory,
    SignalPolarity,
)

SCORED_AT = datetime(2026, 5, 14, 20, 30, tzinfo=UTC)
START_DATE = date(2026, 5, 1)


def test_setup_scoring_input_normalizes_symbol_and_validates_metadata() -> None:
    scoring_input = SetupScoringInput.model_validate(
        scoring_input_payload(symbol="aapl", provider=" fixture ")
    )

    assert scoring_input.symbol == "AAPL"
    assert scoring_input.provider == "fixture"
    assert scoring_input.indicator_calculation_version == "indicator-v1"
    assert scoring_input.indicator_snapshot_id == 42


@pytest.mark.parametrize(
    "snapshot_name",
    [
        "technical_snapshot",
        "support_resistance_snapshot",
        "relative_strength_snapshot",
    ],
)
def test_setup_scoring_input_rejects_snapshot_symbol_mismatches(snapshot_name: str) -> None:
    payload = scoring_input_payload()
    payload[snapshot_name] = populated_snapshots(symbol="MSFT")[snapshot_name]

    with pytest.raises(ValidationError):
        SetupScoringInput.model_validate(payload)


@pytest.mark.parametrize(
    "snapshot_name",
    [
        "technical_snapshot",
        "support_resistance_snapshot",
        "relative_strength_snapshot",
    ],
)
def test_setup_scoring_input_rejects_snapshot_provider_mismatches(snapshot_name: str) -> None:
    payload = scoring_input_payload()
    payload[snapshot_name] = populated_snapshots(provider="other")[snapshot_name]

    with pytest.raises(ValidationError):
        SetupScoringInput.model_validate(payload)


def test_valid_bullish_setup_normalizes_symbol_and_applies_version_defaults() -> None:
    setup = SetupIdea.model_validate(setup_idea_payload(symbol="aapl"))

    assert setup.symbol == "AAPL"
    assert setup.setup_label is SetupLabel.BULLISH_BREAKOUT
    assert setup.scoring_version == SCORING_VERSION
    assert setup.rationale_version == RATIONALE_VERSION
    assert setup.trade_plan is not None
    assert setup.trade_plan.entry.kind is SetupLevelKind.ENTRY_ZONE
    assert setup.trade_plan.failure_conditions


def test_valid_bullish_setup_defaults_holding_window_when_omitted() -> None:
    setup = SetupIdea.model_validate(
        setup_idea_payload(trade_plan=trade_plan_payload(expected_holding_window=None))
    )

    assert setup.trade_plan is not None
    assert setup.trade_plan.expected_holding_window.min_trading_days == 3
    assert setup.trade_plan.expected_holding_window.max_trading_days == 20
    assert setup.trade_plan.expected_holding_window.label == "3 to 20 trading days"


def test_no_clear_setup_output_is_valid_without_trade_plan_levels() -> None:
    setup = SetupIdea.model_validate(
        setup_idea_payload(
            setup_label=SetupLabel.NO_CLEAR_SETUP,
            trade_plan=None,
            no_setup_reasons=("Trend and level signals are mixed.",),
        )
    )

    assert setup.setup_label is SetupLabel.NO_CLEAR_SETUP
    assert setup.trade_plan is None
    assert setup.no_setup_reasons == ("Trend and level signals are mixed.",)


def test_avoid_wait_output_is_valid_without_trade_plan_levels() -> None:
    setup = SetupIdea.model_validate(
        setup_idea_payload(
            setup_label=SetupLabel.AVOID_WAIT,
            trade_plan=None,
            no_setup_reasons=("Price is extended from nearby support.",),
        )
    )

    assert setup.setup_label is SetupLabel.AVOID_WAIT
    assert setup.trade_plan is None


def test_trade_plan_setup_rejects_missing_trade_plan() -> None:
    with pytest.raises(ValidationError):
        SetupIdea.model_validate(setup_idea_payload(trade_plan=None))


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("entry", None),
        ("stop_invalidation", None),
        ("target", None),
        ("failure_conditions", ()),
        ("entry", SetupLevelKind.CURRENT_PRICE),
        ("stop_invalidation", SetupLevelKind.SUPPORT),
        ("target", SetupLevelKind.RESISTANCE),
    ],
)
def test_trade_plan_setup_rejects_missing_or_incorrect_required_plan_data(
    field_name: str,
    replacement: object,
) -> None:
    if isinstance(replacement, SetupLevelKind):
        replacement = level_payload(replacement)
    payload = setup_idea_payload(trade_plan=trade_plan_payload(**{field_name: replacement}))

    with pytest.raises(ValidationError):
        SetupIdea.model_validate(payload)


def test_non_trade_setup_rejects_attached_trade_plan() -> None:
    with pytest.raises(ValidationError):
        SetupIdea.model_validate(
            setup_idea_payload(
                setup_label=SetupLabel.NO_CLEAR_SETUP,
                no_setup_reasons=("Setup is unclear.",),
            )
        )


def test_non_trade_setup_requires_reason_text() -> None:
    with pytest.raises(ValidationError):
        SetupIdea.model_validate(
            setup_idea_payload(
                setup_label=SetupLabel.INCOMPLETE_DATA,
                trade_plan=None,
                no_setup_reasons=(" ",),
            )
        )


@pytest.mark.parametrize(
    "level_overrides",
    [
        {"price": None, "zone_low": None, "zone_high": None},
        {"price": None, "zone_low": "104.00", "zone_high": None},
        {"price": "106.00", "zone_low": "100.00", "zone_high": "105.00"},
        {"price": None, "zone_low": "105.00", "zone_high": "100.00"},
        {"display_order": -1},
    ],
)
def test_invalid_setup_level_shapes_raise_validation_error(
    level_overrides: dict[str, object],
) -> None:
    payload = level_payload()
    payload.update(level_overrides)

    with pytest.raises(ValidationError):
        SetupLevel.model_validate(payload)


def test_invalid_holding_window_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        ExpectedHoldingWindow.model_validate(
            {
                "min_trading_days": 20,
                "max_trading_days": 3,
                "label": "20 to 3 trading days",
            }
        )


def compact_indicator_config() -> IndicatorConfig:
    """Build a compact config for empty snapshot fixtures."""
    return IndicatorConfig(
        sma_periods=(2,),
        rsi_period=2,
        macd_fast_period=1,
        macd_slow_period=2,
        macd_signal_period=1,
        relative_volume_period=1,
        atr_period=1,
        recent_periods=2,
    )


def compact_support_resistance_config() -> SupportResistanceConfig:
    """Build a compact support/resistance config for empty snapshot fixtures."""
    return SupportResistanceConfig(
        lookback_period=3,
        pivot_left=1,
        pivot_right=1,
        zone_percent=0.01,
        proximity_percent=0.03,
        breakout_buffer_percent=0.005,
        max_levels=3,
    )


def scoring_input_payload(**overrides: object) -> dict[str, object]:
    """Return a valid setup scoring input payload with optional overrides."""
    payload: dict[str, object] = {
        "symbol": "AAPL",
        "provider": "fixture",
        "scored_at": SCORED_AT,
        "indicator_snapshot_id": 42,
        "indicator_calculation_version": "indicator-v1",
        **populated_snapshots(),
    }
    payload.update(overrides)
    return payload


def populated_snapshots(symbol: str = "AAPL", provider: str = "fixture") -> dict[str, object]:
    """Build matching populated indicator snapshots for scoring input tests."""
    ticker_candles = candles(symbol=symbol, provider=provider, count=3)
    benchmark_candles = candles(symbol="SPY", provider=provider, count=3)
    return {
        "technical_snapshot": calculate_technical_indicators(
            ticker_candles,
            compact_indicator_config(),
        ),
        "support_resistance_snapshot": calculate_support_resistance(
            ticker_candles,
            compact_support_resistance_config(),
        ),
        "relative_strength_snapshot": calculate_relative_strength(
            ticker_candles,
            {"SPY": benchmark_candles},
            RelativeStrengthConfig(benchmark_symbols=("SPY",), lookback_periods=(1,)),
        ),
    }


def candles(symbol: str, provider: str, count: int) -> tuple[DailyCandle, ...]:
    """Return compact daily candle fixtures."""
    return tuple(
        DailyCandle(
            symbol=symbol,
            session_date=START_DATE + timedelta(days=index),
            timestamp=datetime(
                START_DATE.year,
                START_DATE.month,
                START_DATE.day + index,
                20,
                0,
                tzinfo=UTC,
            ),
            open=Decimal(100 + index),
            high=Decimal(102 + index),
            low=Decimal(99 + index),
            close=Decimal(101 + index),
            volume=1_000_000 + index,
            provider=provider,
        )
        for index in range(count)
    )


def setup_idea_payload(**overrides: object) -> dict[str, object]:
    """Return a valid setup idea payload with optional overrides."""
    payload: dict[str, object] = {
        "symbol": "AAPL",
        "setup_label": SetupLabel.BULLISH_BREAKOUT,
        "score": 82,
        "confidence": ConfidenceLabel.MODERATE,
        "scored_at": SCORED_AT,
        "indicator_snapshot_id": 7,
        "trade_plan": trade_plan_payload(),
        "confidence_factors": (
            {
                "name": "Trend alignment",
                "category": SignalCategory.TREND,
                "polarity": SignalPolarity.SUPPORTIVE,
                "score_impact": 2,
                "explanation": "Price is holding above key moving averages.",
            },
        ),
        "signal_explanations": (
            {
                "category": SignalCategory.SUPPORT_RESISTANCE,
                "polarity": SignalPolarity.SUPPORTIVE,
                "title": "Breakout context",
                "summary": "Price is above a recent resistance zone.",
                "value": "Prior resistance near 104",
                "source": "support_resistance_snapshot",
            },
        ),
    }
    payload.update(overrides)
    return payload


def trade_plan_payload(**overrides: object) -> dict[str, object]:
    """Return a valid trade plan payload with optional overrides."""
    payload: dict[str, object] = {
        "entry": level_payload(
            SetupLevelKind.ENTRY_ZONE,
            label="Entry zone",
            zone_low="105.00",
            zone_high="106.00",
            display_order=1,
        ),
        "stop_invalidation": level_payload(
            SetupLevelKind.STOP_INVALIDATION,
            label="Stop / invalidation",
            price="99.00",
            zone_low=None,
            zone_high=None,
            display_order=2,
        ),
        "target": level_payload(
            SetupLevelKind.TARGET_ZONE,
            label="Target zone",
            price=None,
            zone_low="115.00",
            zone_high="118.00",
            display_order=3,
        ),
        "risk_reward": {
            "risk_per_share": "6.00",
            "reward_per_share": "12.00",
            "ratio": "2.00",
            "notes": "Based on the midpoint of the planned zones.",
        },
        "expected_holding_window": {
            "min_trading_days": 3,
            "max_trading_days": 20,
            "label": "3 to 20 trading days",
        },
        "failure_conditions": (
            {
                "label": "Breakout failure",
                "description": "Price closes back below the breakout area.",
                "level": level_payload(
                    SetupLevelKind.STOP_INVALIDATION,
                    label="Invalidation area",
                    price="99.00",
                    zone_low=None,
                    zone_high=None,
                    display_order=4,
                ),
                "signal_category": SignalCategory.SUPPORT_RESISTANCE,
            },
        ),
    }
    payload.update({key: value for key, value in overrides.items() if value is not None})
    for key, value in overrides.items():
        if value is None:
            payload.pop(key, None)
    return payload


def level_payload(
    kind: SetupLevelKind = SetupLevelKind.ENTRY_ZONE,
    **overrides: object,
) -> dict[str, object]:
    """Return a valid setup level payload with optional overrides."""
    payload: dict[str, object] = {
        "kind": kind,
        "label": "Level",
        "price": "105.00",
        "zone_low": "104.00",
        "zone_high": "106.00",
        "source": "fixture",
        "display_order": 0,
    }
    payload.update(overrides)
    return payload

"""Support/resistance and relative-strength signal tests."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import cast

import pytest

from app.indicators.signals import (
    PriceLevelKind,
    RelativeStrengthConfig,
    RelativeStrengthIncompleteReason,
    RelativeStrengthLabel,
    SupportResistanceConfig,
    SupportResistanceIncompleteReason,
    SupportResistanceState,
    calculate_relative_strength,
    calculate_support_resistance,
)
from app.market_data.schemas import DailyCandle, DataRecency

START_DATE = date(2026, 1, 2)


def candle_payload(**overrides: object) -> dict[str, object]:
    """Return a valid normalized daily candle payload with optional overrides."""
    session_date = cast(date, overrides.get("session_date", START_DATE))
    close = _decimal(overrides.get("close", "100"))
    open_price = _decimal(overrides.get("open", close))
    high = _decimal(overrides.get("high", max(open_price, close) + Decimal("1")))
    low = _decimal(overrides.get("low", min(open_price, close) - Decimal("1")))
    if low <= 0:
        low = Decimal("0.01")

    payload: dict[str, object] = {
        "symbol": "AAPL",
        "session_date": session_date,
        "timestamp": datetime(
            session_date.year,
            session_date.month,
            session_date.day,
            21,
            0,
            tzinfo=UTC,
        ),
        "open": _decimal_text(open_price),
        "high": _decimal_text(high),
        "low": _decimal_text(low),
        "close": _decimal_text(close),
        "volume": 100,
        "adjusted": True,
        "provider": "fixture",
        "data_recency": "delayed",
    }
    payload.update(overrides)
    return payload


def candle(**overrides: object) -> DailyCandle:
    """Build a normalized daily candle."""
    return DailyCandle.model_validate(candle_payload(**overrides))


def candle_series(
    closes: Sequence[object],
    *,
    symbol: str = "AAPL",
    provider: str = "fixture",
    start_date: date = START_DATE,
    flat_ohlc: bool = False,
) -> tuple[DailyCandle, ...]:
    """Build sequential normalized daily candles."""
    candles: list[DailyCandle] = []
    for index, close in enumerate(closes):
        session_date = start_date + timedelta(days=index)
        payload: dict[str, object] = {
            "symbol": symbol,
            "provider": provider,
            "session_date": session_date,
            "close": close,
        }
        if flat_ohlc:
            payload["open"] = close
            payload["high"] = close
            payload["low"] = close
        candles.append(candle(**payload))
    return tuple(candles)


def ohlc_series(
    rows: Sequence[tuple[object, object, object, object]],
    *,
    symbol: str = "AAPL",
    provider: str = "fixture",
) -> tuple[DailyCandle, ...]:
    """Build sequential candles from open/high/low/close rows."""
    return tuple(
        candle(
            symbol=symbol,
            provider=provider,
            session_date=START_DATE + timedelta(days=index),
            open=open_price,
            high=high,
            low=low,
            close=close,
        )
        for index, (open_price, high, low, close) in enumerate(rows)
    )


def support_resistance_config(**overrides: object) -> SupportResistanceConfig:
    """Build compact support/resistance config for fixtures."""
    payload: dict[str, object] = {
        "lookback_period": 12,
        "pivot_left": 1,
        "pivot_right": 1,
        "zone_percent": 0.01,
        "proximity_percent": 0.03,
        "breakout_buffer_percent": 0.005,
        "max_levels": 3,
    }
    payload.update(overrides)
    return SupportResistanceConfig.model_validate(payload)


def test_support_resistance_identifies_breakout_above_prior_resistance() -> None:
    snapshot = calculate_support_resistance(
        ohlc_series(
            (
                (100, 101, 99, 100),
                (103, 105, 100, 103),
                (101, 103, 99, 100),
                (101, 104, 98, 101),
                (100, 102, 97, 99),
                (106, 109, 104, 108),
            )
        ),
        support_resistance_config(),
    )

    assert snapshot.state is SupportResistanceState.BREAKOUT
    assert snapshot.is_complete is True
    assert snapshot.latest_close == pytest.approx(108.0)
    assert snapshot.broken_resistance is not None
    assert snapshot.broken_resistance.kind is PriceLevelKind.RESISTANCE
    assert snapshot.broken_resistance.price == pytest.approx(104.5)
    assert snapshot.broken_resistance.touch_count == 2


def test_support_resistance_identifies_pullback_near_support() -> None:
    snapshot = calculate_support_resistance(
        ohlc_series(
            (
                (105, 106, 104, 105),
                (101, 105, 100, 101),
                (105, 106, 102, 105),
                (101, 104, "99.5", 101),
                (107, 108, 103, 107),
                (102, 103, "101.5", 102),
            )
        ),
        support_resistance_config(),
    )

    assert snapshot.state is SupportResistanceState.PULLBACK_NEAR_SUPPORT
    assert snapshot.nearest_support is not None
    assert snapshot.nearest_support.kind is PriceLevelKind.SUPPORT
    assert snapshot.nearest_support.price == pytest.approx(99.75)
    assert snapshot.nearest_resistance is not None


def test_support_resistance_identifies_failed_resistance() -> None:
    snapshot = calculate_support_resistance(
        ohlc_series(
            (
                (100, 101, 99, 100),
                (104, 105, 100, 104),
                (101, 103, 99, 101),
                (100, 104, 98, 100),
                (101, 102, 99, 101),
                (104, "105.5", 102, 103),
            )
        ),
        support_resistance_config(),
    )

    assert snapshot.state is SupportResistanceState.FAILED_RESISTANCE
    assert snapshot.broken_resistance is None
    assert snapshot.nearest_resistance is not None
    assert snapshot.latest_high == pytest.approx(105.5)


def test_support_resistance_no_candles_returns_explicit_incomplete_snapshot() -> None:
    snapshot = calculate_support_resistance((), support_resistance_config())

    assert snapshot.symbol is None
    assert snapshot.provider is None
    assert snapshot.adjusted is None
    assert snapshot.data_recency is DataRecency.UNKNOWN
    assert snapshot.state is SupportResistanceState.INCOMPLETE
    assert snapshot.is_complete is False
    assert snapshot.required_candles == 3
    assert snapshot.incomplete_details[0].reason is SupportResistanceIncompleteReason.NO_CANDLES


def test_support_resistance_insufficient_history_returns_incomplete_state() -> None:
    snapshot = calculate_support_resistance(
        candle_series((100, 101), flat_ohlc=True),
        support_resistance_config(),
    )

    assert snapshot.state is SupportResistanceState.INCOMPLETE
    assert snapshot.is_complete is False
    assert snapshot.available_candles == 2
    assert (
        snapshot.incomplete_details[0].reason
        is SupportResistanceIncompleteReason.INSUFFICIENT_HISTORY
    )


def test_support_resistance_no_swing_levels_returns_no_clear_level() -> None:
    snapshot = calculate_support_resistance(
        candle_series((100, 101, 102, 103, 104), flat_ohlc=True),
        support_resistance_config(),
    )

    assert snapshot.state is SupportResistanceState.NO_CLEAR_LEVEL
    assert snapshot.is_complete is False
    assert snapshot.support_levels == ()
    assert snapshot.resistance_levels == ()
    assert (
        snapshot.incomplete_details[0].reason is SupportResistanceIncompleteReason.NO_SWING_LEVELS
    )


def test_support_resistance_flat_ohlc_does_not_emit_swing_levels() -> None:
    snapshot = calculate_support_resistance(
        candle_series((100, 100, 100, 100, 100), flat_ohlc=True),
        support_resistance_config(),
    )

    assert snapshot.state is SupportResistanceState.NO_CLEAR_LEVEL
    assert snapshot.is_complete is False
    assert snapshot.support_levels == ()
    assert snapshot.resistance_levels == ()
    assert (
        snapshot.incomplete_details[0].reason is SupportResistanceIncompleteReason.NO_SWING_LEVELS
    )


def test_support_resistance_sorts_candles_without_mutating_input_sequence() -> None:
    candles = list(
        ohlc_series(
            (
                (100, 101, 99, 100),
                (103, 105, 100, 103),
                (101, 103, 99, 100),
                (101, 104, 98, 101),
                (100, 102, 97, 99),
                (106, 109, 104, 108),
            )
        )
    )
    original_order = [item.session_date for item in candles]

    snapshot = calculate_support_resistance(
        list(reversed(candles)),
        support_resistance_config(),
    )

    assert [item.session_date for item in candles] == original_order
    assert snapshot.start_session_date == original_order[0]
    assert snapshot.end_session_date == original_order[-1]


@pytest.mark.parametrize(
    "invalid_candles",
    [
        lambda: (
            candle(symbol="AAPL"),
            candle(symbol="MSFT", session_date=START_DATE + timedelta(days=1)),
        ),
        lambda: (
            candle(provider="fixture"),
            candle(provider="other", session_date=START_DATE + timedelta(days=1)),
        ),
        lambda: (
            candle(adjusted=True),
            candle(adjusted=False, session_date=START_DATE + timedelta(days=1)),
        ),
        lambda: (
            candle(),
            candle(close=101),
        ),
        lambda: (
            candle(),
            candle().model_copy(update={"session_date": START_DATE + timedelta(days=1)}),
        ),
    ],
)
def test_support_resistance_invalid_candle_basis_inputs_raise_value_error(
    invalid_candles: Callable[[], Sequence[DailyCandle]],
) -> None:
    with pytest.raises(ValueError):
        calculate_support_resistance(
            cast(Sequence[DailyCandle], invalid_candles()),
            support_resistance_config(),
        )


def test_relative_strength_defaults_to_spy_qqq_and_identifies_outperformance() -> None:
    snapshot = calculate_relative_strength(
        candle_series(_trend_closes(100, 120, 21), flat_ohlc=True),
        {
            "SPY": candle_series(_trend_closes(100, 105, 21), symbol="SPY", flat_ohlc=True),
            "QQQ": candle_series(_trend_closes(100, 110, 21), symbol="QQQ", flat_ohlc=True),
        },
    )

    assert snapshot.benchmark_symbols == ("SPY", "QQQ")
    assert snapshot.lookback_periods == (20,)
    assert snapshot.overall_label is RelativeStrengthLabel.OUTPERFORMING
    assert snapshot.is_complete is True
    assert [comparison.label for comparison in snapshot.comparisons] == [
        RelativeStrengthLabel.OUTPERFORMING,
        RelativeStrengthLabel.OUTPERFORMING,
    ]

    spy_comparison = snapshot.comparisons[0]
    assert spy_comparison.benchmark_symbol == "SPY"
    assert spy_comparison.ticker_return == pytest.approx(0.20)
    assert spy_comparison.benchmark_return == pytest.approx(0.05)
    assert spy_comparison.excess_return == pytest.approx(0.15)


def test_relative_strength_identifies_underperformance() -> None:
    snapshot = calculate_relative_strength(
        candle_series(_trend_closes(100, 102, 21), flat_ohlc=True),
        {
            "SPY": candle_series(_trend_closes(100, 110, 21), symbol="SPY", flat_ohlc=True),
            "QQQ": candle_series(_trend_closes(100, 105, 21), symbol="QQQ", flat_ohlc=True),
        },
    )

    assert snapshot.overall_label is RelativeStrengthLabel.UNDERPERFORMING
    assert snapshot.is_complete is True
    assert all(
        comparison.label is RelativeStrengthLabel.UNDERPERFORMING
        for comparison in snapshot.comparisons
    )
    assert snapshot.comparisons[0].excess_return == pytest.approx(-0.08)


def test_relative_strength_missing_benchmarks_are_incomplete_not_underperforming() -> None:
    snapshot = calculate_relative_strength(
        candle_series(_trend_closes(100, 120, 21), flat_ohlc=True),
        {},
    )

    assert snapshot.overall_label is RelativeStrengthLabel.INCOMPLETE
    assert snapshot.is_complete is False
    assert {detail.reason for detail in snapshot.incomplete_details} == {
        RelativeStrengthIncompleteReason.MISSING_BENCHMARK
    }
    assert all(
        comparison.label is RelativeStrengthLabel.INCOMPLETE for comparison in snapshot.comparisons
    )
    assert all(
        comparison.label is not RelativeStrengthLabel.UNDERPERFORMING
        for comparison in snapshot.comparisons
    )


def test_relative_strength_insufficient_benchmark_history_is_incomplete() -> None:
    snapshot = calculate_relative_strength(
        candle_series(_trend_closes(100, 120, 21), flat_ohlc=True),
        {"SPY": (candle(symbol="SPY", close=100, open=100, high=100, low=100),)},
        RelativeStrengthConfig(benchmark_symbols=("SPY",), lookback_periods=(20,)),
    )

    assert snapshot.overall_label is RelativeStrengthLabel.INCOMPLETE
    assert snapshot.is_complete is False
    assert snapshot.comparisons[0].label is RelativeStrengthLabel.INCOMPLETE
    assert (
        snapshot.incomplete_details[0].reason
        is RelativeStrengthIncompleteReason.INSUFFICIENT_BENCHMARK_HISTORY
    )


def test_relative_strength_uses_matched_dates_without_full_benchmark_window() -> None:
    benchmark_start = candle(symbol="SPY", close=100, open=100, high=100, low=100)
    benchmark_end = candle(
        symbol="SPY",
        session_date=START_DATE + timedelta(days=20),
        close=105,
        open=105,
        high=105,
        low=105,
    )

    snapshot = calculate_relative_strength(
        candle_series(_trend_closes(100, 120, 21), flat_ohlc=True),
        {"SPY": (benchmark_start, benchmark_end)},
        RelativeStrengthConfig(benchmark_symbols=("SPY",), lookback_periods=(20,)),
    )

    assert snapshot.overall_label is RelativeStrengthLabel.OUTPERFORMING
    assert snapshot.is_complete is True
    assert snapshot.incomplete_details == ()
    assert snapshot.comparisons[0].ticker_return == pytest.approx(0.20)
    assert snapshot.comparisons[0].benchmark_return == pytest.approx(0.05)
    assert snapshot.comparisons[0].excess_return == pytest.approx(0.15)


def test_relative_strength_no_overlapping_dates_is_incomplete() -> None:
    snapshot = calculate_relative_strength(
        candle_series(_trend_closes(100, 120, 21), flat_ohlc=True),
        {
            "SPY": candle_series(
                _trend_closes(100, 105, 21),
                symbol="SPY",
                start_date=START_DATE + timedelta(days=1),
                flat_ohlc=True,
            )
        },
        RelativeStrengthConfig(benchmark_symbols=("SPY",), lookback_periods=(20,)),
    )

    assert snapshot.overall_label is RelativeStrengthLabel.INCOMPLETE
    assert snapshot.comparisons[0].label is RelativeStrengthLabel.INCOMPLETE
    assert (
        snapshot.incomplete_details[0].reason
        is RelativeStrengthIncompleteReason.NO_OVERLAPPING_DATES
    )


def test_relative_strength_rejects_invalid_ticker_or_benchmark_basis() -> None:
    config = RelativeStrengthConfig(benchmark_symbols=("SPY",), lookback_periods=(1,))
    mixed_ticker_candles = (
        candle(symbol="AAPL"),
        candle(symbol="MSFT", session_date=START_DATE + timedelta(days=1)),
    )
    provider_mismatch_benchmark = {
        "SPY": candle_series(
            _trend_closes(100, 101, 2),
            symbol="SPY",
            provider="other",
            flat_ohlc=True,
        )
    }

    with pytest.raises(ValueError):
        calculate_relative_strength(mixed_ticker_candles, {}, config)

    with pytest.raises(ValueError):
        calculate_relative_strength(
            candle_series(_trend_closes(100, 102, 2), flat_ohlc=True),
            provider_mismatch_benchmark,
            config,
        )


def _trend_closes(start: float, end: float, count: int) -> tuple[float, ...]:
    if count <= 1:
        return (end,)
    step = (end - start) / (count - 1)
    return tuple(start + (step * index) for index in range(count))


def _decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")

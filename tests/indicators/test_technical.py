"""Technical indicator calculation tests."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import cast

import pytest
from pydantic import ValidationError

from app.indicators.technical import (
    IndicatorConfig,
    IndicatorIncompleteReason,
    TechnicalIndicatorSnapshot,
    calculate_technical_indicators,
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
    volumes: Sequence[int] | None = None,
    flat_ohlc: bool = False,
) -> tuple[DailyCandle, ...]:
    """Build sequential normalized daily candles for indicator fixtures."""
    volume_values = volumes or tuple(100 for _ in closes)
    candles: list[DailyCandle] = []
    for index, close in enumerate(closes):
        session_date = START_DATE + timedelta(days=index)
        payload: dict[str, object] = {
            "session_date": session_date,
            "close": close,
            "volume": volume_values[index],
        }
        if flat_ohlc:
            payload["open"] = close
            payload["high"] = close
            payload["low"] = close
        candles.append(candle(**payload))
    return tuple(candles)


def compact_config(**overrides: object) -> IndicatorConfig:
    """Build a small-period config for hand-checkable indicator fixtures."""
    payload: dict[str, object] = {
        "sma_periods": (3, 5),
        "rsi_period": 3,
        "macd_fast_period": 3,
        "macd_slow_period": 5,
        "macd_signal_period": 3,
        "relative_volume_period": 3,
        "atr_period": 3,
        "recent_periods": 3,
    }
    payload.update(overrides)
    return IndicatorConfig.model_validate(payload)


def test_no_candles_returns_explicit_incomplete_snapshot() -> None:
    snapshot = calculate_technical_indicators(())

    assert snapshot.symbol is None
    assert snapshot.provider is None
    assert snapshot.adjusted is None
    assert snapshot.data_recency is DataRecency.UNKNOWN
    assert snapshot.available_candles == 0
    assert snapshot.required_candles == 200
    assert snapshot.latest is None
    assert snapshot.recent_points == ()
    assert snapshot.is_complete is False
    assert snapshot.incomplete_details[0].reason is IndicatorIncompleteReason.NO_CANDLES


def test_calculates_hand_checkable_sma_macd_relative_volume_and_atr_values() -> None:
    snapshot = calculate_technical_indicators(
        candle_series(
            (10, 11, 12, 13, 14, 15, 16),
            volumes=(100, 120, 180, 300, 240, 360, 600),
        ),
        compact_config(),
    )

    latest = snapshot.latest
    assert latest is not None
    assert snapshot.is_complete is True
    assert snapshot.required_candles == 7
    assert snapshot.start_session_date == START_DATE
    assert snapshot.end_session_date == START_DATE + timedelta(days=6)
    assert [point.session_date for point in snapshot.recent_points] == [
        START_DATE + timedelta(days=4),
        START_DATE + timedelta(days=5),
        START_DATE + timedelta(days=6),
    ]

    assert latest.moving_averages[3] == pytest.approx(15.0)
    assert latest.moving_averages[5] == pytest.approx(14.0)
    assert latest.rsi == pytest.approx(100.0)
    assert latest.macd.line == pytest.approx(1.0)
    assert latest.macd.signal == pytest.approx(1.0)
    assert latest.macd.histogram == pytest.approx(0.0)
    assert latest.relative_volume == pytest.approx(2.0)
    assert latest.atr == pytest.approx(2.0)


def test_rsi_uses_wilder_smoothing_for_mixed_gain_loss_series() -> None:
    snapshot = calculate_technical_indicators(
        candle_series((10, 12, 11, 13, 12, 14)),
        compact_config(sma_periods=(2,), macd_fast_period=2, macd_slow_period=3),
    )

    assert snapshot.latest is not None
    assert snapshot.latest.rsi == pytest.approx(77.2727272727)


def test_tiny_nonzero_rsi_moves_are_not_classified_as_flat() -> None:
    snapshot = calculate_technical_indicators(
        candle_series(("1.000000000", "1.000000002", "1.000000001")),
        compact_config(
            sma_periods=(2,),
            rsi_period=2,
            macd_fast_period=1,
            macd_slow_period=2,
            macd_signal_period=1,
            relative_volume_period=1,
            atr_period=1,
        ),
    )

    assert snapshot.latest is not None
    assert snapshot.latest.rsi == pytest.approx(66.6666666667)


def test_relative_volume_excludes_current_session_from_baseline() -> None:
    snapshot = calculate_technical_indicators(
        candle_series((10, 10, 10, 10), volumes=(100, 100, 100, 1000)),
        compact_config(
            sma_periods=(2,),
            rsi_period=2,
            macd_fast_period=1,
            macd_slow_period=2,
            macd_signal_period=1,
            relative_volume_period=3,
            atr_period=1,
        ),
    )

    assert snapshot.latest is not None
    assert snapshot.latest.relative_volume == pytest.approx(10.0)


def test_zero_volume_baseline_returns_incomplete_detail() -> None:
    snapshot = calculate_technical_indicators(
        candle_series((10, 10, 10, 10), volumes=(0, 0, 0, 10)),
        compact_config(
            sma_periods=(2,),
            rsi_period=2,
            macd_fast_period=1,
            macd_slow_period=2,
            macd_signal_period=1,
            relative_volume_period=3,
            atr_period=1,
        ),
    )

    assert snapshot.latest is not None
    assert snapshot.latest.relative_volume is None
    assert snapshot.is_complete is False
    assert IndicatorIncompleteReason.ZERO_VOLUME_BASELINE in {
        detail.reason for detail in snapshot.incomplete_details
    }


def test_default_snapshot_is_complete_only_after_full_two_hundred_candle_warmup() -> None:
    incomplete = calculate_technical_indicators(candle_series([100] * 199, flat_ohlc=True))
    complete = calculate_technical_indicators(candle_series([100] * 200, flat_ohlc=True))

    assert incomplete.is_complete is False
    assert incomplete.latest is not None
    assert incomplete.latest.moving_averages[200] is None
    assert incomplete.incomplete_details

    latest = complete.latest
    assert latest is not None
    assert complete.required_candles == 200
    assert complete.is_complete is True
    assert complete.incomplete_details == ()
    assert latest.moving_averages[20] == pytest.approx(100.0)
    assert latest.moving_averages[50] == pytest.approx(100.0)
    assert latest.moving_averages[200] == pytest.approx(100.0)
    assert latest.rsi == pytest.approx(50.0)
    assert latest.macd.line == pytest.approx(0.0)
    assert latest.macd.signal == pytest.approx(0.0)
    assert latest.macd.histogram == pytest.approx(0.0)
    assert latest.relative_volume == pytest.approx(1.0)
    assert latest.atr == pytest.approx(0.0)
    assert_snapshot_has_no_non_finite_numbers(complete)


def test_volatile_series_produces_nonzero_momentum_and_volatility_values() -> None:
    closes = tuple(100 + ((-1) ** index * (index % 5)) + index * 0.4 for index in range(40))
    snapshot = calculate_technical_indicators(
        candle_series(closes),
        compact_config(sma_periods=(5, 10), macd_fast_period=4, macd_slow_period=8),
    )

    latest = snapshot.latest
    assert latest is not None
    assert snapshot.is_complete is True
    assert latest.atr is not None and latest.atr > 0
    assert latest.rsi is not None and 0 < latest.rsi < 100
    assert latest.macd.histogram is not None
    assert abs(latest.macd.histogram) > 0


def test_sorts_candles_without_mutating_input_sequence() -> None:
    candles = list(candle_series((10, 11, 12, 13, 14)))
    original_order = [item.session_date for item in candles]

    snapshot = calculate_technical_indicators(
        list(reversed(candles)),
        compact_config(sma_periods=(2,), macd_fast_period=2, macd_slow_period=3),
    )

    assert [item.session_date for item in candles] == original_order
    assert snapshot.start_session_date == original_order[0]
    assert snapshot.end_session_date == original_order[-1]


@pytest.mark.parametrize(
    "invalid_candles",
    [
        lambda: (
            candle(symbol="AAPL"),
            candle(
                symbol="MSFT",
                session_date=START_DATE + timedelta(days=1),
            ),
        ),
        lambda: (
            candle(provider="fixture"),
            candle(
                provider="other",
                session_date=START_DATE + timedelta(days=1),
            ),
        ),
        lambda: (
            candle(adjusted=True),
            candle(
                adjusted=False,
                session_date=START_DATE + timedelta(days=1),
            ),
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
def test_invalid_candle_basis_inputs_raise_value_error(
    invalid_candles: Callable[[], Sequence[DailyCandle]],
) -> None:
    with pytest.raises(ValueError):
        calculate_technical_indicators(cast(Sequence[DailyCandle], invalid_candles()))


def test_rejects_non_daily_candle_objects() -> None:
    with pytest.raises(ValueError):
        calculate_technical_indicators(cast(Sequence[DailyCandle], (object(),)))


def test_missing_volume_is_rejected_by_daily_candle_contract() -> None:
    with pytest.raises(ValidationError):
        DailyCandle.model_validate(candle_payload(volume=None))


def assert_snapshot_has_no_non_finite_numbers(snapshot: TechnicalIndicatorSnapshot) -> None:
    """Assert public snapshot values contain no NaN or infinite floats."""
    for point in snapshot.recent_points:
        assert math.isfinite(point.close)
        for value in point.moving_averages.values():
            assert value is None or math.isfinite(value)
        assert point.rsi is None or math.isfinite(point.rsi)
        assert point.macd.line is None or math.isfinite(point.macd.line)
        assert point.macd.signal is None or math.isfinite(point.macd.signal)
        assert point.macd.histogram is None or math.isfinite(point.macd.histogram)
        assert point.relative_volume is None or math.isfinite(point.relative_volume)
        assert point.atr is None or math.isfinite(point.atr)


def _decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")

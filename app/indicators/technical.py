"""Deterministic technical indicator calculations."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import date
from enum import StrEnum
from typing import Any, Self, cast

import pandas as pd  # type: ignore[import-untyped]
from pydantic import field_validator, model_validator

from app.market_data.schemas import DailyCandle, DataRecency, MarketDataModel

EPSILON = 1e-12


class IndicatorConfig(MarketDataModel):
    """Configurable periods for core technical indicator calculations."""

    sma_periods: tuple[int, ...] = (20, 50, 200)
    rsi_period: int = 14
    macd_fast_period: int = 12
    macd_slow_period: int = 26
    macd_signal_period: int = 9
    relative_volume_period: int = 20
    atr_period: int = 14
    recent_periods: int = 5

    @field_validator("sma_periods")
    @classmethod
    def validate_sma_periods(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        """Require positive, unique SMA periods and expose them in ascending order."""
        if not value:
            raise ValueError("sma_periods must include at least one period")
        if any(period <= 0 for period in value):
            raise ValueError("sma_periods must contain only positive periods")

        sorted_periods = tuple(sorted(value))
        if len(set(sorted_periods)) != len(sorted_periods):
            raise ValueError("sma_periods must be unique")
        return sorted_periods

    @field_validator(
        "rsi_period",
        "macd_fast_period",
        "macd_slow_period",
        "macd_signal_period",
        "relative_volume_period",
        "atr_period",
        "recent_periods",
    )
    @classmethod
    def validate_positive_period(cls, value: int) -> int:
        """Require positive periods for every configurable indicator window."""
        if value <= 0:
            raise ValueError("indicator periods must be positive")
        return value

    @model_validator(mode="after")
    def validate_macd_periods(self) -> Self:
        """Require MACD slow period to be greater than the fast period."""
        if self.macd_slow_period <= self.macd_fast_period:
            raise ValueError("macd_slow_period must be greater than macd_fast_period")
        return self


class IndicatorIncompleteReason(StrEnum):
    """Reasons an indicator value is not available for the latest candle."""

    NO_CANDLES = "no_candles"
    INSUFFICIENT_HISTORY = "insufficient_history"
    ZERO_VOLUME_BASELINE = "zero_volume_baseline"


class IndicatorIncompleteDetail(MarketDataModel):
    """Explanation for an unavailable latest indicator value."""

    indicator: str
    reason: IndicatorIncompleteReason
    required_candles: int
    available_candles: int
    message: str | None = None

    @field_validator("indicator")
    @classmethod
    def validate_indicator(cls, value: str) -> str:
        """Require an indicator identifier for downstream diagnostics."""
        indicator = value.strip()
        if not indicator:
            raise ValueError("indicator is required")
        return indicator


class MacdValue(MarketDataModel):
    """MACD line, signal, and histogram values for one session."""

    line: float | None
    signal: float | None
    histogram: float | None

    @field_validator("line", "signal", "histogram")
    @classmethod
    def validate_optional_float(cls, value: float | None) -> float | None:
        """Prevent non-finite MACD values from leaving the indicator layer."""
        return _validate_optional_float(value)


class IndicatorPoint(MarketDataModel):
    """Technical indicator values aligned to one completed daily candle."""

    session_date: date
    close: float
    volume: int
    moving_averages: dict[int, float | None]
    rsi: float | None
    macd: MacdValue
    relative_volume: float | None
    atr: float | None

    @field_validator("close")
    @classmethod
    def validate_close(cls, value: float) -> float:
        """Prevent non-finite close values from leaving the indicator layer."""
        return _validate_required_float(value)

    @field_validator("volume")
    @classmethod
    def validate_volume(cls, value: int) -> int:
        """Require a non-negative normalized volume value."""
        if value < 0:
            raise ValueError("volume must be non-negative")
        return value

    @field_validator("moving_averages")
    @classmethod
    def validate_moving_averages(
        cls,
        value: dict[int, float | None],
    ) -> dict[int, float | None]:
        """Prevent non-finite SMA values from leaving the indicator layer."""
        validated: dict[int, float | None] = {}
        for period, average in value.items():
            if period <= 0:
                raise ValueError("moving average periods must be positive")
            validated[period] = _validate_optional_float(average)
        return validated

    @field_validator("rsi", "relative_volume", "atr")
    @classmethod
    def validate_optional_indicator(cls, value: float | None) -> float | None:
        """Prevent non-finite indicator values from leaving the indicator layer."""
        return _validate_optional_float(value)


class TechnicalIndicatorSnapshot(MarketDataModel):
    """Recent technical indicator values and completeness metadata for scoring."""

    symbol: str | None
    provider: str | None
    adjusted: bool | None
    data_recency: DataRecency
    start_session_date: date | None
    end_session_date: date | None
    available_candles: int
    required_candles: int
    is_complete: bool
    latest: IndicatorPoint | None
    recent_points: tuple[IndicatorPoint, ...]
    incomplete_details: tuple[IndicatorIncompleteDetail, ...]


_DEFAULT_INDICATOR_CONFIG = IndicatorConfig()


def calculate_technical_indicators(
    candles: Sequence[DailyCandle],
    config: IndicatorConfig = _DEFAULT_INDICATOR_CONFIG,
) -> TechnicalIndicatorSnapshot:
    """Calculate core technical indicators from normalized completed daily candles."""
    sorted_candles = _prepare_candles(candles)
    required_candles = _required_candles(config)
    if not sorted_candles:
        return _no_candles_snapshot(required_candles)

    close_values = [_to_finite_float(candle.close, "close") for candle in sorted_candles]
    high_values = [_to_finite_float(candle.high, "high") for candle in sorted_candles]
    low_values = [_to_finite_float(candle.low, "low") for candle in sorted_candles]
    volumes = [candle.volume for candle in sorted_candles]

    moving_averages = {
        period: _simple_moving_average(close_values, period) for period in config.sma_periods
    }
    rsi_values = _relative_strength_index(close_values, config.rsi_period)
    macd_lines, macd_signals, macd_histograms = _macd(
        close_values,
        fast_period=config.macd_fast_period,
        slow_period=config.macd_slow_period,
        signal_period=config.macd_signal_period,
    )
    relative_volumes, zero_volume_baselines = _relative_volume(
        volumes,
        config.relative_volume_period,
    )
    atr_values = _average_true_range(
        high_values,
        low_values,
        close_values,
        config.atr_period,
    )

    points = tuple(
        _indicator_point(
            index=index,
            candle=candle,
            close=close_values[index],
            moving_averages=moving_averages,
            rsi_values=rsi_values,
            macd_lines=macd_lines,
            macd_signals=macd_signals,
            macd_histograms=macd_histograms,
            relative_volumes=relative_volumes,
            atr_values=atr_values,
        )
        for index, candle in enumerate(sorted_candles)
    )
    latest = points[-1]
    incomplete_details = _latest_incomplete_details(
        latest,
        config,
        available_candles=len(sorted_candles),
        latest_zero_volume_baseline=zero_volume_baselines[-1],
    )

    return TechnicalIndicatorSnapshot(
        symbol=sorted_candles[-1].symbol,
        provider=sorted_candles[-1].provider,
        adjusted=sorted_candles[-1].adjusted,
        data_recency=sorted_candles[-1].data_recency,
        start_session_date=sorted_candles[0].session_date,
        end_session_date=sorted_candles[-1].session_date,
        available_candles=len(sorted_candles),
        required_candles=required_candles,
        is_complete=not incomplete_details,
        latest=latest,
        recent_points=points[-config.recent_periods :],
        incomplete_details=incomplete_details,
    )


def _prepare_candles(candles: Sequence[DailyCandle]) -> tuple[DailyCandle, ...]:
    raw_candles = tuple(candles)
    for candle in raw_candles:
        if not isinstance(candle, DailyCandle):
            raise ValueError("candles must contain DailyCandle objects")

    sorted_candles = tuple(sorted(raw_candles, key=lambda candle: candle.session_date))
    if not sorted_candles:
        return ()

    symbols = {candle.symbol for candle in sorted_candles}
    if len(symbols) > 1:
        raise ValueError("candles must not mix symbols")

    providers = {candle.provider for candle in sorted_candles}
    if len(providers) > 1:
        raise ValueError("candles must not mix providers")

    adjusted_values = {candle.adjusted for candle in sorted_candles}
    if len(adjusted_values) > 1:
        raise ValueError("candles must not mix adjusted and unadjusted bars")

    session_dates: set[date] = set()
    timestamps_by_session: dict[object, date] = {}
    for candle in sorted_candles:
        if candle.session_date in session_dates:
            raise ValueError("candles must not contain duplicate session_date values")
        session_dates.add(candle.session_date)

        timestamp_session = timestamps_by_session.get(candle.timestamp)
        if timestamp_session is not None and timestamp_session != candle.session_date:
            raise ValueError("candles must not reuse one timestamp for different sessions")
        timestamps_by_session[candle.timestamp] = candle.session_date

        _to_finite_float(candle.open, "open")
        _to_finite_float(candle.high, "high")
        _to_finite_float(candle.low, "low")
        _to_finite_float(candle.close, "close")

    return sorted_candles


def _no_candles_snapshot(required_candles: int) -> TechnicalIndicatorSnapshot:
    return TechnicalIndicatorSnapshot(
        symbol=None,
        provider=None,
        adjusted=None,
        data_recency=DataRecency.UNKNOWN,
        start_session_date=None,
        end_session_date=None,
        available_candles=0,
        required_candles=required_candles,
        is_complete=False,
        latest=None,
        recent_points=(),
        incomplete_details=(
            IndicatorIncompleteDetail(
                indicator="all",
                reason=IndicatorIncompleteReason.NO_CANDLES,
                required_candles=required_candles,
                available_candles=0,
                message="No daily candles were provided.",
            ),
        ),
    )


def _required_candles(config: IndicatorConfig) -> int:
    return max(
        max(config.sma_periods),
        config.rsi_period + 1,
        config.macd_slow_period + config.macd_signal_period - 1,
        config.relative_volume_period + 1,
        config.atr_period,
    )


def _indicator_point(
    *,
    index: int,
    candle: DailyCandle,
    close: float,
    moving_averages: dict[int, list[float | None]],
    rsi_values: Sequence[float | None],
    macd_lines: Sequence[float | None],
    macd_signals: Sequence[float | None],
    macd_histograms: Sequence[float | None],
    relative_volumes: Sequence[float | None],
    atr_values: Sequence[float | None],
) -> IndicatorPoint:
    return IndicatorPoint(
        session_date=candle.session_date,
        close=close,
        volume=candle.volume,
        moving_averages={
            period: _public_value(values[index]) for period, values in moving_averages.items()
        },
        rsi=_public_value(rsi_values[index]),
        macd=MacdValue(
            line=_public_value(macd_lines[index]),
            signal=_public_value(macd_signals[index]),
            histogram=_public_value(macd_histograms[index]),
        ),
        relative_volume=_public_value(relative_volumes[index]),
        atr=_public_value(atr_values[index]),
    )


def _simple_moving_average(values: Sequence[float], period: int) -> list[float | None]:
    series = pd.Series(values, dtype="float64")
    moving_average = series.rolling(period, min_periods=period).mean()
    return [_public_value(value) for value in moving_average.to_numpy()]


def _relative_strength_index(values: Sequence[float], period: int) -> list[float | None]:
    rsi: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return rsi

    deltas = [values[index] - values[index - 1] for index in range(1, len(values))]
    gains = [max(delta, 0.0) for delta in deltas]
    losses = [max(-delta, 0.0) for delta in deltas]

    average_gain = sum(gains[:period]) / period
    average_loss = sum(losses[:period]) / period
    rsi[period] = _rsi_from_averages(average_gain, average_loss)

    for index in range(period + 1, len(values)):
        gain = gains[index - 1]
        loss = losses[index - 1]
        average_gain = ((average_gain * (period - 1)) + gain) / period
        average_loss = ((average_loss * (period - 1)) + loss) / period
        rsi[index] = _rsi_from_averages(average_gain, average_loss)

    return rsi


def _rsi_from_averages(average_gain: float, average_loss: float) -> float:
    gain_is_zero = abs(average_gain) <= EPSILON
    loss_is_zero = abs(average_loss) <= EPSILON
    if gain_is_zero and loss_is_zero:
        return 50.0
    if loss_is_zero:
        return 100.0
    if gain_is_zero:
        return 0.0

    relative_strength = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def _macd(
    values: Sequence[float],
    *,
    fast_period: int,
    slow_period: int,
    signal_period: int,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    fast_ema = _ema_sma_seeded(values, fast_period)
    slow_ema = _ema_sma_seeded(values, slow_period)
    macd_line = [
        fast - slow if fast is not None and slow is not None else None
        for fast, slow in zip(fast_ema, slow_ema, strict=True)
    ]
    signal_line = _ema_sma_seeded(macd_line, signal_period)
    histogram = [
        line - signal if line is not None and signal is not None else None
        for line, signal in zip(macd_line, signal_line, strict=True)
    ]
    return macd_line, signal_line, histogram


def _ema_sma_seeded(values: Sequence[float | None], period: int) -> list[float | None]:
    ema_values: list[float | None] = [None] * len(values)
    alpha = 2.0 / (period + 1)
    seed_values: list[float] = []
    previous_ema: float | None = None

    for index, value in enumerate(values):
        if value is None:
            if previous_ema is None:
                seed_values.clear()
            continue

        finite_value = _validate_required_float(value)
        if previous_ema is None:
            seed_values.append(finite_value)
            if len(seed_values) == period:
                previous_ema = sum(seed_values) / period
                ema_values[index] = previous_ema
            continue

        previous_ema = ((finite_value - previous_ema) * alpha) + previous_ema
        ema_values[index] = previous_ema

    return ema_values


def _average_true_range(
    high_values: Sequence[float],
    low_values: Sequence[float],
    close_values: Sequence[float],
    period: int,
) -> list[float | None]:
    atr_values: list[float | None] = [None] * len(close_values)
    if len(close_values) < period:
        return atr_values

    true_ranges: list[float] = []
    for index, (high, low) in enumerate(zip(high_values, low_values, strict=True)):
        if index == 0:
            true_ranges.append(high - low)
            continue
        previous_close = close_values[index - 1]
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))

    previous_atr = sum(true_ranges[:period]) / period
    atr_values[period - 1] = previous_atr
    for index in range(period, len(true_ranges)):
        previous_atr = ((previous_atr * (period - 1)) + true_ranges[index]) / period
        atr_values[index] = previous_atr

    return atr_values


def _relative_volume(
    volumes: Sequence[int],
    period: int,
) -> tuple[list[float | None], list[bool]]:
    series = pd.Series(volumes, dtype="float64")
    baseline = series.shift(1).rolling(period, min_periods=period).mean()

    relative_volumes: list[float | None] = []
    zero_baselines: list[bool] = []
    for volume, baseline_value in zip(series.to_numpy(), baseline.to_numpy(), strict=True):
        if math.isnan(baseline_value):
            relative_volumes.append(None)
            zero_baselines.append(False)
            continue
        if baseline_value == 0:
            relative_volumes.append(None)
            zero_baselines.append(True)
            continue
        relative_volumes.append(_public_value(volume / baseline_value))
        zero_baselines.append(False)
    return relative_volumes, zero_baselines


def _latest_incomplete_details(
    latest: IndicatorPoint,
    config: IndicatorConfig,
    *,
    available_candles: int,
    latest_zero_volume_baseline: bool,
) -> tuple[IndicatorIncompleteDetail, ...]:
    details: list[IndicatorIncompleteDetail] = []

    for period in config.sma_periods:
        if latest.moving_averages[period] is None:
            details.append(
                _insufficient_history_detail(
                    indicator=f"sma_{period}",
                    required_candles=period,
                    available_candles=available_candles,
                )
            )

    if latest.rsi is None:
        details.append(
            _insufficient_history_detail(
                indicator="rsi",
                required_candles=config.rsi_period + 1,
                available_candles=available_candles,
            )
        )

    if latest.macd.line is None:
        details.append(
            _insufficient_history_detail(
                indicator="macd_line",
                required_candles=config.macd_slow_period,
                available_candles=available_candles,
            )
        )
    if latest.macd.signal is None:
        details.append(
            _insufficient_history_detail(
                indicator="macd_signal",
                required_candles=config.macd_slow_period + config.macd_signal_period - 1,
                available_candles=available_candles,
            )
        )
    if latest.macd.histogram is None:
        details.append(
            _insufficient_history_detail(
                indicator="macd_histogram",
                required_candles=config.macd_slow_period + config.macd_signal_period - 1,
                available_candles=available_candles,
            )
        )

    if latest.relative_volume is None:
        reason = (
            IndicatorIncompleteReason.ZERO_VOLUME_BASELINE
            if latest_zero_volume_baseline
            else IndicatorIncompleteReason.INSUFFICIENT_HISTORY
        )
        details.append(
            IndicatorIncompleteDetail(
                indicator="relative_volume",
                reason=reason,
                required_candles=config.relative_volume_period + 1,
                available_candles=available_candles,
                message=(
                    "Prior-volume baseline is zero."
                    if latest_zero_volume_baseline
                    else "Not enough completed daily candles for relative volume."
                ),
            )
        )

    if latest.atr is None:
        details.append(
            _insufficient_history_detail(
                indicator="atr",
                required_candles=config.atr_period,
                available_candles=available_candles,
            )
        )

    return tuple(details)


def _insufficient_history_detail(
    *,
    indicator: str,
    required_candles: int,
    available_candles: int,
) -> IndicatorIncompleteDetail:
    return IndicatorIncompleteDetail(
        indicator=indicator,
        reason=IndicatorIncompleteReason.INSUFFICIENT_HISTORY,
        required_candles=required_candles,
        available_candles=available_candles,
        message=f"Not enough completed daily candles for {indicator}.",
    )


def _to_finite_float(value: object, field_name: str) -> float:
    try:
        float_value = float(cast(Any, value))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if not math.isfinite(float_value):
        raise ValueError(f"{field_name} must be finite")
    return float_value


def _public_value(value: object) -> float | None:
    if value is None:
        return None
    try:
        float_value = float(cast(Any, value))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("indicator value must be finite") from exc
    if math.isnan(float_value):
        return None
    if math.isinf(float_value):
        raise ValueError("indicator value must be finite")
    return float_value


def _validate_required_float(value: float) -> float:
    float_value = float(value)
    if not math.isfinite(float_value):
        raise ValueError("value must be finite")
    return float_value


def _validate_optional_float(value: float | None) -> float | None:
    if value is None:
        return None
    return _validate_required_float(value)


__all__ = [
    "EPSILON",
    "IndicatorConfig",
    "IndicatorIncompleteDetail",
    "IndicatorIncompleteReason",
    "IndicatorPoint",
    "MacdValue",
    "TechnicalIndicatorSnapshot",
    "calculate_technical_indicators",
]

"""Deterministic support/resistance and relative-strength signals."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any, Self, cast

from pydantic import field_validator, model_validator

from app.market_data.schemas import (
    DailyCandle,
    DataRecency,
    MarketDataModel,
    normalize_symbol,
)


class PriceLevelKind(StrEnum):
    """Supported price-level categories."""

    SUPPORT = "support"
    RESISTANCE = "resistance"


class SupportResistanceState(StrEnum):
    """Conservative latest-price state against recent support/resistance zones."""

    BREAKOUT = "breakout"
    PULLBACK_NEAR_SUPPORT = "pullback_near_support"
    FAILED_RESISTANCE = "failed_resistance"
    BETWEEN_LEVELS = "between_levels"
    NO_CLEAR_LEVEL = "no_clear_level"
    INCOMPLETE = "incomplete"


class SupportResistanceIncompleteReason(StrEnum):
    """Reasons support/resistance signals are unavailable or incomplete."""

    NO_CANDLES = "no_candles"
    INSUFFICIENT_HISTORY = "insufficient_history"
    NO_SWING_LEVELS = "no_swing_levels"


class RelativeStrengthLabel(StrEnum):
    """Relative-strength labels for benchmark comparisons."""

    OUTPERFORMING = "outperforming"
    UNDERPERFORMING = "underperforming"
    MIXED = "mixed"
    INCOMPLETE = "incomplete"


class RelativeStrengthIncompleteReason(StrEnum):
    """Reasons a benchmark-relative comparison cannot be calculated."""

    NO_TICKER_CANDLES = "no_ticker_candles"
    INSUFFICIENT_TICKER_HISTORY = "insufficient_ticker_history"
    MISSING_BENCHMARK = "missing_benchmark"
    INSUFFICIENT_BENCHMARK_HISTORY = "insufficient_benchmark_history"
    NO_OVERLAPPING_DATES = "no_overlapping_dates"
    INVALID_START_PRICE = "invalid_start_price"


class SupportResistanceConfig(MarketDataModel):
    """Configurable support/resistance swing-level heuristic parameters."""

    lookback_period: int = 60
    pivot_left: int = 2
    pivot_right: int = 2
    zone_percent: float = 0.01
    proximity_percent: float = 0.03
    breakout_buffer_percent: float = 0.005
    max_levels: int = 3

    @field_validator("lookback_period", "pivot_left", "pivot_right", "max_levels")
    @classmethod
    def validate_positive_count(cls, value: int) -> int:
        """Require positive candle windows and level counts."""
        if value <= 0:
            raise ValueError("support/resistance counts must be positive")
        return value

    @field_validator("zone_percent", "proximity_percent", "breakout_buffer_percent")
    @classmethod
    def validate_non_negative_percent(cls, value: float) -> float:
        """Require finite, non-negative percentage parameters."""
        float_value = _validate_required_float(value)
        if float_value < 0:
            raise ValueError("support/resistance percentages must be non-negative")
        return float_value

    @model_validator(mode="after")
    def validate_lookback_supports_pivots(self) -> Self:
        """Require the lookback window to be large enough to confirm one pivot."""
        if self.lookback_period < self.pivot_left + self.pivot_right + 1:
            raise ValueError("lookback_period must fit pivot_left + pivot_right + 1")
        return self


class PriceLevelZone(MarketDataModel):
    """A simple price zone derived from one or more recent swing pivots."""

    kind: PriceLevelKind
    price: float
    zone_low: float
    zone_high: float
    touch_count: int
    last_touched_session_date: date
    distance_from_latest_close_percent: float | None = None

    @field_validator("price", "zone_low", "zone_high")
    @classmethod
    def validate_required_price(cls, value: float) -> float:
        """Prevent non-finite level prices from leaving the indicator layer."""
        return _validate_required_float(value)

    @field_validator("distance_from_latest_close_percent")
    @classmethod
    def validate_optional_distance(cls, value: float | None) -> float | None:
        """Prevent non-finite distance values from leaving the indicator layer."""
        return _validate_optional_float(value)

    @field_validator("touch_count")
    @classmethod
    def validate_touch_count(cls, value: int) -> int:
        """Require at least one pivot touch for every emitted zone."""
        if value <= 0:
            raise ValueError("touch_count must be positive")
        return value

    @model_validator(mode="after")
    def validate_zone_bounds(self) -> Self:
        """Require each zone to contain its representative price."""
        if self.zone_low > self.zone_high:
            raise ValueError("zone_low must be less than or equal to zone_high")
        if self.price < self.zone_low or self.price > self.zone_high:
            raise ValueError("price must be inside the zone")
        return self


class SupportResistanceIncompleteDetail(MarketDataModel):
    """Explanation for unavailable support/resistance signal output."""

    signal: str
    reason: SupportResistanceIncompleteReason
    required_candles: int
    available_candles: int
    message: str | None = None

    @field_validator("signal")
    @classmethod
    def validate_signal(cls, value: str) -> str:
        """Require a signal identifier for downstream diagnostics."""
        signal = value.strip()
        if not signal:
            raise ValueError("signal is required")
        return signal


class SupportResistanceSnapshot(MarketDataModel):
    """Latest support/resistance levels and completeness metadata."""

    symbol: str | None
    provider: str | None
    adjusted: bool | None
    data_recency: DataRecency
    start_session_date: date | None
    end_session_date: date | None
    available_candles: int
    required_candles: int
    latest_close: float | None
    latest_high: float | None
    latest_low: float | None
    support_levels: tuple[PriceLevelZone, ...]
    resistance_levels: tuple[PriceLevelZone, ...]
    nearest_support: PriceLevelZone | None
    nearest_resistance: PriceLevelZone | None
    broken_resistance: PriceLevelZone | None
    state: SupportResistanceState
    is_complete: bool
    incomplete_details: tuple[SupportResistanceIncompleteDetail, ...]

    @field_validator("latest_close", "latest_high", "latest_low")
    @classmethod
    def validate_optional_price(cls, value: float | None) -> float | None:
        """Prevent non-finite latest prices from leaving the indicator layer."""
        return _validate_optional_float(value)


class RelativeStrengthConfig(MarketDataModel):
    """Configurable benchmark-relative strength parameters."""

    benchmark_symbols: tuple[str, ...] = ("SPY", "QQQ")
    lookback_periods: tuple[int, ...] = (20,)
    outperformance_threshold: float = 0.0

    @field_validator("benchmark_symbols", mode="before")
    @classmethod
    def validate_benchmark_symbols(cls, value: object) -> tuple[str, ...]:
        """Normalize and de-duplicate benchmark symbols."""
        if isinstance(value, str):
            raw_symbols: tuple[object, ...] = (value,)
        elif isinstance(value, (list, tuple)):
            raw_symbols = tuple(value)
        else:
            raise ValueError("benchmark_symbols must be a symbol or sequence of symbols")

        normalized: list[str] = []
        seen: set[str] = set()
        for raw_symbol in raw_symbols:
            symbol = normalize_symbol(raw_symbol)
            if symbol not in seen:
                normalized.append(symbol)
                seen.add(symbol)
        if not normalized:
            raise ValueError("benchmark_symbols must include at least one symbol")
        return tuple(normalized)

    @field_validator("lookback_periods")
    @classmethod
    def validate_lookback_periods(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        """Require positive, unique relative-strength lookbacks."""
        if not value:
            raise ValueError("lookback_periods must include at least one period")
        if any(period <= 0 for period in value):
            raise ValueError("lookback_periods must contain only positive periods")
        return tuple(sorted(set(value)))

    @field_validator("outperformance_threshold")
    @classmethod
    def validate_threshold(cls, value: float) -> float:
        """Require a finite relative-strength threshold."""
        return _validate_required_float(value)


class RelativeStrengthIncompleteDetail(MarketDataModel):
    """Explanation for an unavailable benchmark comparison."""

    benchmark_symbol: str
    lookback_period: int
    reason: RelativeStrengthIncompleteReason
    required_candles: int
    available_candles: int
    message: str | None = None

    @field_validator("benchmark_symbol", mode="before")
    @classmethod
    def validate_benchmark_symbol(cls, value: object) -> str:
        """Normalize benchmark symbols in incomplete details."""
        return normalize_symbol(value)

    @field_validator("lookback_period", "required_candles")
    @classmethod
    def validate_positive_count(cls, value: int) -> int:
        """Require positive period/count metadata."""
        if value <= 0:
            raise ValueError("relative-strength counts must be positive")
        return value

    @field_validator("available_candles")
    @classmethod
    def validate_available_candles(cls, value: int) -> int:
        """Require non-negative available-candle counts."""
        if value < 0:
            raise ValueError("available_candles must be non-negative")
        return value


class BenchmarkRelativeStrength(MarketDataModel):
    """Ticker performance compared with one benchmark over one lookback window."""

    benchmark_symbol: str
    lookback_period: int
    end_session_date: date | None
    start_session_date: date | None
    ticker_return: float | None
    benchmark_return: float | None
    excess_return: float | None
    label: RelativeStrengthLabel
    incomplete_detail: RelativeStrengthIncompleteDetail | None = None

    @field_validator("benchmark_symbol", mode="before")
    @classmethod
    def validate_benchmark_symbol(cls, value: object) -> str:
        """Normalize benchmark symbols in comparison output."""
        return normalize_symbol(value)

    @field_validator("lookback_period")
    @classmethod
    def validate_lookback_period(cls, value: int) -> int:
        """Require a positive relative-strength lookback period."""
        if value <= 0:
            raise ValueError("lookback_period must be positive")
        return value

    @field_validator("ticker_return", "benchmark_return", "excess_return")
    @classmethod
    def validate_optional_return(cls, value: float | None) -> float | None:
        """Prevent non-finite return values from leaving the indicator layer."""
        return _validate_optional_float(value)


class RelativeStrengthSnapshot(MarketDataModel):
    """Benchmark-relative strength comparisons and completeness metadata."""

    symbol: str | None
    provider: str | None
    adjusted: bool | None
    data_recency: DataRecency
    start_session_date: date | None
    end_session_date: date | None
    available_candles: int
    benchmark_symbols: tuple[str, ...]
    lookback_periods: tuple[int, ...]
    comparisons: tuple[BenchmarkRelativeStrength, ...]
    overall_label: RelativeStrengthLabel
    is_complete: bool
    incomplete_details: tuple[RelativeStrengthIncompleteDetail, ...]


_DEFAULT_SUPPORT_RESISTANCE_CONFIG = SupportResistanceConfig()
_DEFAULT_RELATIVE_STRENGTH_CONFIG = RelativeStrengthConfig()


@dataclass(frozen=True)
class _Pivot:
    kind: PriceLevelKind
    price: float
    session_date: date


def calculate_support_resistance(
    candles: Sequence[DailyCandle],
    config: SupportResistanceConfig = _DEFAULT_SUPPORT_RESISTANCE_CONFIG,
) -> SupportResistanceSnapshot:
    """Calculate recent support/resistance zones from normalized daily candles."""
    sorted_candles = _prepare_candles(candles, collection_name="candles")
    required_candles = _support_resistance_required_candles(config)
    if not sorted_candles:
        return _no_support_resistance_candles_snapshot(required_candles)

    latest_candle = sorted_candles[-1]
    latest_close = _to_finite_float(latest_candle.close, "close")
    latest_high = _to_finite_float(latest_candle.high, "high")
    latest_low = _to_finite_float(latest_candle.low, "low")

    if len(sorted_candles) < required_candles:
        return _incomplete_support_resistance_snapshot(
            candles=sorted_candles,
            required_candles=required_candles,
            latest_close=latest_close,
            latest_high=latest_high,
            latest_low=latest_low,
            detail=SupportResistanceIncompleteDetail(
                signal="support_resistance",
                reason=SupportResistanceIncompleteReason.INSUFFICIENT_HISTORY,
                required_candles=required_candles,
                available_candles=len(sorted_candles),
                message="Not enough completed daily candles to confirm swing levels.",
            ),
        )

    lookback_candles = sorted_candles[-config.lookback_period :]
    pivots = _find_pivots(lookback_candles, config)
    supports = _level_zones(
        (pivot for pivot in pivots if pivot.kind is PriceLevelKind.SUPPORT),
        config=config,
        latest_close=latest_close,
    )
    resistances = _level_zones(
        (pivot for pivot in pivots if pivot.kind is PriceLevelKind.RESISTANCE),
        config=config,
        latest_close=latest_close,
    )

    nearest_support = _nearest_support(supports, latest_close)
    nearest_resistance = _nearest_resistance(resistances, latest_close)
    broken_resistance = _broken_resistance(resistances, latest_close, config)
    state = _support_resistance_state(
        nearest_support=nearest_support,
        nearest_resistance=nearest_resistance,
        broken_resistance=broken_resistance,
        resistances=resistances,
        latest_close=latest_close,
        latest_high=latest_high,
        config=config,
    )

    incomplete_details: tuple[SupportResistanceIncompleteDetail, ...] = ()
    if not supports and not resistances:
        incomplete_details = (
            SupportResistanceIncompleteDetail(
                signal="support_resistance",
                reason=SupportResistanceIncompleteReason.NO_SWING_LEVELS,
                required_candles=required_candles,
                available_candles=len(sorted_candles),
                message="No confirmed swing support or resistance levels were found.",
            ),
        )

    return SupportResistanceSnapshot(
        symbol=latest_candle.symbol,
        provider=latest_candle.provider,
        adjusted=latest_candle.adjusted,
        data_recency=latest_candle.data_recency,
        start_session_date=lookback_candles[0].session_date,
        end_session_date=latest_candle.session_date,
        available_candles=len(sorted_candles),
        required_candles=required_candles,
        latest_close=latest_close,
        latest_high=latest_high,
        latest_low=latest_low,
        support_levels=supports,
        resistance_levels=resistances,
        nearest_support=nearest_support,
        nearest_resistance=nearest_resistance,
        broken_resistance=broken_resistance,
        state=state,
        is_complete=not incomplete_details,
        incomplete_details=incomplete_details,
    )


def calculate_relative_strength(
    ticker_candles: Sequence[DailyCandle],
    benchmark_candles_by_symbol: Mapping[str, Sequence[DailyCandle]],
    config: RelativeStrengthConfig = _DEFAULT_RELATIVE_STRENGTH_CONFIG,
) -> RelativeStrengthSnapshot:
    """Calculate ticker returns relative to configured benchmark candles."""
    sorted_ticker_candles = _prepare_candles(
        ticker_candles,
        collection_name="ticker_candles",
    )
    benchmark_candles = _normalize_benchmark_mapping(benchmark_candles_by_symbol)
    comparisons: list[BenchmarkRelativeStrength] = []
    incomplete_details: list[RelativeStrengthIncompleteDetail] = []

    if not sorted_ticker_candles:
        for benchmark_symbol in config.benchmark_symbols:
            for lookback_period in config.lookback_periods:
                detail = _relative_strength_detail(
                    benchmark_symbol=benchmark_symbol,
                    lookback_period=lookback_period,
                    reason=RelativeStrengthIncompleteReason.NO_TICKER_CANDLES,
                    required_candles=lookback_period + 1,
                    available_candles=0,
                    message="No ticker daily candles were provided.",
                )
                incomplete_details.append(detail)
                comparisons.append(_incomplete_comparison(detail))
        return RelativeStrengthSnapshot(
            symbol=None,
            provider=None,
            adjusted=None,
            data_recency=DataRecency.UNKNOWN,
            start_session_date=None,
            end_session_date=None,
            available_candles=0,
            benchmark_symbols=config.benchmark_symbols,
            lookback_periods=config.lookback_periods,
            comparisons=tuple(comparisons),
            overall_label=RelativeStrengthLabel.INCOMPLETE,
            is_complete=False,
            incomplete_details=tuple(incomplete_details),
        )

    latest_ticker_candle = sorted_ticker_candles[-1]
    ticker_closes_by_date = {
        candle.session_date: _to_finite_float(candle.close, "close")
        for candle in sorted_ticker_candles
    }

    for benchmark_symbol in config.benchmark_symbols:
        raw_benchmark_candles = benchmark_candles.get(benchmark_symbol)
        if not raw_benchmark_candles:
            for lookback_period in config.lookback_periods:
                detail = _relative_strength_detail(
                    benchmark_symbol=benchmark_symbol,
                    lookback_period=lookback_period,
                    reason=RelativeStrengthIncompleteReason.MISSING_BENCHMARK,
                    required_candles=lookback_period + 1,
                    available_candles=0,
                    message=f"No benchmark candles were provided for {benchmark_symbol}.",
                )
                incomplete_details.append(detail)
                comparisons.append(_incomplete_comparison(detail))
            continue

        sorted_benchmark_candles = _prepare_candles(
            raw_benchmark_candles,
            collection_name=f"benchmark_candles[{benchmark_symbol}]",
        )
        _validate_benchmark_basis(
            sorted_benchmark_candles,
            expected_symbol=benchmark_symbol,
            ticker_candle=latest_ticker_candle,
        )
        benchmark_closes_by_date = {
            candle.session_date: _to_finite_float(candle.close, "close")
            for candle in sorted_benchmark_candles
        }

        for lookback_period in config.lookback_periods:
            comparison = _relative_strength_comparison(
                ticker_candles=sorted_ticker_candles,
                ticker_closes_by_date=ticker_closes_by_date,
                benchmark_candles=sorted_benchmark_candles,
                benchmark_closes_by_date=benchmark_closes_by_date,
                benchmark_symbol=benchmark_symbol,
                lookback_period=lookback_period,
                config=config,
            )
            comparisons.append(comparison)
            if comparison.incomplete_detail is not None:
                incomplete_details.append(comparison.incomplete_detail)

    complete_labels = [
        comparison.label
        for comparison in comparisons
        if comparison.label is not RelativeStrengthLabel.INCOMPLETE
    ]

    return RelativeStrengthSnapshot(
        symbol=latest_ticker_candle.symbol,
        provider=latest_ticker_candle.provider,
        adjusted=latest_ticker_candle.adjusted,
        data_recency=latest_ticker_candle.data_recency,
        start_session_date=sorted_ticker_candles[0].session_date,
        end_session_date=latest_ticker_candle.session_date,
        available_candles=len(sorted_ticker_candles),
        benchmark_symbols=config.benchmark_symbols,
        lookback_periods=config.lookback_periods,
        comparisons=tuple(comparisons),
        overall_label=_overall_relative_strength_label(complete_labels),
        is_complete=not incomplete_details,
        incomplete_details=tuple(incomplete_details),
    )


def _find_pivots(
    candles: Sequence[DailyCandle],
    config: SupportResistanceConfig,
) -> tuple[_Pivot, ...]:
    high_values = [_to_finite_float(candle.high, "high") for candle in candles]
    low_values = [_to_finite_float(candle.low, "low") for candle in candles]
    pivots: list[_Pivot] = []

    for index in range(config.pivot_left, len(candles) - config.pivot_right):
        left_start = index - config.pivot_left
        right_end = index + config.pivot_right + 1
        low = low_values[index]
        high = high_values[index]

        left_lows = low_values[left_start:index]
        right_lows = low_values[index + 1 : right_end]
        neighboring_lows = (*left_lows, *right_lows)
        if (
            low <= min(left_lows)
            and low <= min(right_lows)
            and any(low < neighbor_low for neighbor_low in neighboring_lows)
        ):
            pivots.append(
                _Pivot(
                    kind=PriceLevelKind.SUPPORT,
                    price=low,
                    session_date=candles[index].session_date,
                )
            )

        left_highs = high_values[left_start:index]
        right_highs = high_values[index + 1 : right_end]
        neighboring_highs = (*left_highs, *right_highs)
        if (
            high >= max(left_highs)
            and high >= max(right_highs)
            and any(high > neighbor_high for neighbor_high in neighboring_highs)
        ):
            pivots.append(
                _Pivot(
                    kind=PriceLevelKind.RESISTANCE,
                    price=high,
                    session_date=candles[index].session_date,
                )
            )

    return tuple(pivots)


def _level_zones(
    pivots: Iterable[_Pivot],
    *,
    config: SupportResistanceConfig,
    latest_close: float,
) -> tuple[PriceLevelZone, ...]:
    clusters: list[list[_Pivot]] = []
    for pivot in sorted(pivots, key=lambda item: item.price):
        cluster = _matching_cluster(pivot, clusters, config.zone_percent)
        if cluster is None:
            clusters.append([pivot])
        else:
            cluster.append(pivot)

    zones = tuple(_zone_from_cluster(cluster, config, latest_close) for cluster in clusters)
    ranked_zones = sorted(
        zones,
        key=lambda zone: (zone.touch_count, zone.last_touched_session_date),
        reverse=True,
    )
    return tuple(ranked_zones[: config.max_levels])


def _matching_cluster(
    pivot: _Pivot,
    clusters: Sequence[Sequence[_Pivot]],
    zone_percent: float,
) -> list[_Pivot] | None:
    for cluster in clusters:
        average_price = sum(item.price for item in cluster) / len(cluster)
        if average_price == 0:
            continue
        if abs(pivot.price - average_price) / average_price <= zone_percent:
            return cast(list[_Pivot], cluster)
    return None


def _zone_from_cluster(
    cluster: Sequence[_Pivot],
    config: SupportResistanceConfig,
    latest_close: float,
) -> PriceLevelZone:
    price = sum(pivot.price for pivot in cluster) / len(cluster)
    zone_low = price * (1 - config.zone_percent)
    zone_high = price * (1 + config.zone_percent)
    return PriceLevelZone(
        kind=cluster[0].kind,
        price=_public_required_value(price),
        zone_low=_public_required_value(zone_low),
        zone_high=_public_required_value(zone_high),
        touch_count=len(cluster),
        last_touched_session_date=max(pivot.session_date for pivot in cluster),
        distance_from_latest_close_percent=_public_optional_value((latest_close - price) / price),
    )


def _nearest_support(
    support_levels: Sequence[PriceLevelZone],
    latest_close: float,
) -> PriceLevelZone | None:
    candidates = [level for level in support_levels if level.zone_low <= latest_close]
    if not candidates:
        return None
    return min(candidates, key=lambda level: abs(latest_close - level.price))


def _nearest_resistance(
    resistance_levels: Sequence[PriceLevelZone],
    latest_close: float,
) -> PriceLevelZone | None:
    candidates = [level for level in resistance_levels if level.zone_high >= latest_close]
    if not candidates:
        return None
    return min(candidates, key=lambda level: abs(level.price - latest_close))


def _broken_resistance(
    resistance_levels: Sequence[PriceLevelZone],
    latest_close: float,
    config: SupportResistanceConfig,
) -> PriceLevelZone | None:
    candidates = [
        level
        for level in resistance_levels
        if latest_close > level.zone_high * (1 + config.breakout_buffer_percent)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda level: abs(latest_close - level.price))


def _support_resistance_state(
    *,
    nearest_support: PriceLevelZone | None,
    nearest_resistance: PriceLevelZone | None,
    broken_resistance: PriceLevelZone | None,
    resistances: Sequence[PriceLevelZone],
    latest_close: float,
    latest_high: float,
    config: SupportResistanceConfig,
) -> SupportResistanceState:
    if broken_resistance is not None:
        return SupportResistanceState.BREAKOUT

    if _failed_resistance(resistances, latest_close, latest_high) is not None:
        return SupportResistanceState.FAILED_RESISTANCE

    if nearest_support is not None and _is_near_support(
        nearest_support,
        latest_close,
        config,
    ):
        return SupportResistanceState.PULLBACK_NEAR_SUPPORT

    if nearest_support is not None and nearest_resistance is not None:
        return SupportResistanceState.BETWEEN_LEVELS

    return SupportResistanceState.NO_CLEAR_LEVEL


def _failed_resistance(
    resistance_levels: Sequence[PriceLevelZone],
    latest_close: float,
    latest_high: float,
) -> PriceLevelZone | None:
    candidates = [
        level
        for level in resistance_levels
        if latest_high >= level.zone_low and latest_close < level.zone_low
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda level: abs(latest_high - level.price))


def _is_near_support(
    support: PriceLevelZone,
    latest_close: float,
    config: SupportResistanceConfig,
) -> bool:
    if latest_close < support.zone_low:
        return False
    if latest_close <= support.zone_high:
        return True
    return (latest_close - support.zone_high) / support.zone_high <= config.proximity_percent


def _relative_strength_comparison(
    *,
    ticker_candles: Sequence[DailyCandle],
    ticker_closes_by_date: Mapping[date, float],
    benchmark_candles: Sequence[DailyCandle],
    benchmark_closes_by_date: Mapping[date, float],
    benchmark_symbol: str,
    lookback_period: int,
    config: RelativeStrengthConfig,
) -> BenchmarkRelativeStrength:
    required_candles = lookback_period + 1
    end_date = ticker_candles[-1].session_date

    if len(ticker_candles) < required_candles:
        detail = _relative_strength_detail(
            benchmark_symbol=benchmark_symbol,
            lookback_period=lookback_period,
            reason=RelativeStrengthIncompleteReason.INSUFFICIENT_TICKER_HISTORY,
            required_candles=required_candles,
            available_candles=len(ticker_candles),
            message="Not enough ticker candles for the relative-strength lookback.",
        )
        return _incomplete_comparison(detail)

    start_date = ticker_candles[-required_candles].session_date
    ticker_start_close = ticker_closes_by_date[start_date]
    ticker_end_close = ticker_closes_by_date[end_date]

    if len(benchmark_candles) < 2:
        detail = _relative_strength_detail(
            benchmark_symbol=benchmark_symbol,
            lookback_period=lookback_period,
            reason=RelativeStrengthIncompleteReason.INSUFFICIENT_BENCHMARK_HISTORY,
            required_candles=2,
            available_candles=len(benchmark_candles),
            message=f"Not enough {benchmark_symbol} candles for a start/end return.",
        )
        return _incomplete_comparison(detail)

    benchmark_start_close = benchmark_closes_by_date.get(start_date)
    benchmark_end_close = benchmark_closes_by_date.get(end_date)

    if benchmark_start_close is None or benchmark_end_close is None:
        detail = _relative_strength_detail(
            benchmark_symbol=benchmark_symbol,
            lookback_period=lookback_period,
            reason=RelativeStrengthIncompleteReason.NO_OVERLAPPING_DATES,
            required_candles=required_candles,
            available_candles=len(benchmark_candles),
            message=f"{benchmark_symbol} is missing the ticker start or end session date.",
        )
        return _incomplete_comparison(detail)

    if ticker_start_close <= 0 or benchmark_start_close <= 0:
        detail = _relative_strength_detail(
            benchmark_symbol=benchmark_symbol,
            lookback_period=lookback_period,
            reason=RelativeStrengthIncompleteReason.INVALID_START_PRICE,
            required_candles=required_candles,
            available_candles=min(len(ticker_candles), len(benchmark_candles)),
            message="Ticker and benchmark start closes must be positive.",
        )
        return _incomplete_comparison(detail)

    ticker_return = (ticker_end_close / ticker_start_close) - 1
    benchmark_return = (benchmark_end_close / benchmark_start_close) - 1
    excess_return = ticker_return - benchmark_return
    label = (
        RelativeStrengthLabel.OUTPERFORMING
        if excess_return > config.outperformance_threshold
        else RelativeStrengthLabel.UNDERPERFORMING
    )

    return BenchmarkRelativeStrength(
        benchmark_symbol=benchmark_symbol,
        lookback_period=lookback_period,
        end_session_date=end_date,
        start_session_date=start_date,
        ticker_return=_public_optional_value(ticker_return),
        benchmark_return=_public_optional_value(benchmark_return),
        excess_return=_public_optional_value(excess_return),
        label=label,
        incomplete_detail=None,
    )


def _overall_relative_strength_label(
    complete_labels: Sequence[RelativeStrengthLabel],
) -> RelativeStrengthLabel:
    if not complete_labels:
        return RelativeStrengthLabel.INCOMPLETE
    if all(label is RelativeStrengthLabel.OUTPERFORMING for label in complete_labels):
        return RelativeStrengthLabel.OUTPERFORMING
    if all(label is RelativeStrengthLabel.UNDERPERFORMING for label in complete_labels):
        return RelativeStrengthLabel.UNDERPERFORMING
    return RelativeStrengthLabel.MIXED


def _incomplete_comparison(
    detail: RelativeStrengthIncompleteDetail,
) -> BenchmarkRelativeStrength:
    return BenchmarkRelativeStrength(
        benchmark_symbol=detail.benchmark_symbol,
        lookback_period=detail.lookback_period,
        end_session_date=None,
        start_session_date=None,
        ticker_return=None,
        benchmark_return=None,
        excess_return=None,
        label=RelativeStrengthLabel.INCOMPLETE,
        incomplete_detail=detail,
    )


def _relative_strength_detail(
    *,
    benchmark_symbol: str,
    lookback_period: int,
    reason: RelativeStrengthIncompleteReason,
    required_candles: int,
    available_candles: int,
    message: str,
) -> RelativeStrengthIncompleteDetail:
    return RelativeStrengthIncompleteDetail(
        benchmark_symbol=benchmark_symbol,
        lookback_period=lookback_period,
        reason=reason,
        required_candles=required_candles,
        available_candles=available_candles,
        message=message,
    )


def _normalize_benchmark_mapping(
    candles_by_symbol: Mapping[str, Sequence[DailyCandle]],
) -> dict[str, Sequence[DailyCandle]]:
    normalized: dict[str, Sequence[DailyCandle]] = {}
    for raw_symbol, candles in candles_by_symbol.items():
        symbol = normalize_symbol(raw_symbol)
        if symbol in normalized:
            raise ValueError("benchmark_candles_by_symbol must not contain duplicate symbols")
        normalized[symbol] = candles
    return normalized


def _validate_benchmark_basis(
    candles: Sequence[DailyCandle],
    *,
    expected_symbol: str,
    ticker_candle: DailyCandle,
) -> None:
    if not candles:
        return
    benchmark_candle = candles[-1]
    if benchmark_candle.symbol != expected_symbol:
        raise ValueError("benchmark candles must match their mapping symbol")
    if benchmark_candle.provider != ticker_candle.provider:
        raise ValueError("ticker and benchmark candles must use the same provider")
    if benchmark_candle.adjusted != ticker_candle.adjusted:
        raise ValueError("ticker and benchmark candles must use the same adjustment basis")


def _prepare_candles(
    candles: Sequence[DailyCandle],
    *,
    collection_name: str,
) -> tuple[DailyCandle, ...]:
    raw_candles = tuple(candles)
    for candle in raw_candles:
        if not isinstance(candle, DailyCandle):
            raise ValueError(f"{collection_name} must contain DailyCandle objects")

    sorted_candles = tuple(sorted(raw_candles, key=lambda candle: candle.session_date))
    if not sorted_candles:
        return ()

    symbols = {candle.symbol for candle in sorted_candles}
    if len(symbols) > 1:
        raise ValueError(f"{collection_name} must not mix symbols")

    providers = {candle.provider for candle in sorted_candles}
    if len(providers) > 1:
        raise ValueError(f"{collection_name} must not mix providers")

    adjusted_values = {candle.adjusted for candle in sorted_candles}
    if len(adjusted_values) > 1:
        raise ValueError(f"{collection_name} must not mix adjusted and unadjusted bars")

    session_dates: set[date] = set()
    timestamps_by_session: dict[object, date] = {}
    for candle in sorted_candles:
        if candle.session_date in session_dates:
            raise ValueError(f"{collection_name} must not contain duplicate session_date values")
        session_dates.add(candle.session_date)

        timestamp_session = timestamps_by_session.get(candle.timestamp)
        if timestamp_session is not None and timestamp_session != candle.session_date:
            raise ValueError(
                f"{collection_name} must not reuse one timestamp for different sessions"
            )
        timestamps_by_session[candle.timestamp] = candle.session_date

        _to_finite_float(candle.open, "open")
        _to_finite_float(candle.high, "high")
        _to_finite_float(candle.low, "low")
        _to_finite_float(candle.close, "close")

    return sorted_candles


def _support_resistance_required_candles(config: SupportResistanceConfig) -> int:
    return config.pivot_left + config.pivot_right + 1


def _no_support_resistance_candles_snapshot(
    required_candles: int,
) -> SupportResistanceSnapshot:
    return SupportResistanceSnapshot(
        symbol=None,
        provider=None,
        adjusted=None,
        data_recency=DataRecency.UNKNOWN,
        start_session_date=None,
        end_session_date=None,
        available_candles=0,
        required_candles=required_candles,
        latest_close=None,
        latest_high=None,
        latest_low=None,
        support_levels=(),
        resistance_levels=(),
        nearest_support=None,
        nearest_resistance=None,
        broken_resistance=None,
        state=SupportResistanceState.INCOMPLETE,
        is_complete=False,
        incomplete_details=(
            SupportResistanceIncompleteDetail(
                signal="support_resistance",
                reason=SupportResistanceIncompleteReason.NO_CANDLES,
                required_candles=required_candles,
                available_candles=0,
                message="No daily candles were provided.",
            ),
        ),
    )


def _incomplete_support_resistance_snapshot(
    *,
    candles: Sequence[DailyCandle],
    required_candles: int,
    latest_close: float,
    latest_high: float,
    latest_low: float,
    detail: SupportResistanceIncompleteDetail,
) -> SupportResistanceSnapshot:
    latest_candle = candles[-1]
    return SupportResistanceSnapshot(
        symbol=latest_candle.symbol,
        provider=latest_candle.provider,
        adjusted=latest_candle.adjusted,
        data_recency=latest_candle.data_recency,
        start_session_date=candles[0].session_date,
        end_session_date=latest_candle.session_date,
        available_candles=len(candles),
        required_candles=required_candles,
        latest_close=latest_close,
        latest_high=latest_high,
        latest_low=latest_low,
        support_levels=(),
        resistance_levels=(),
        nearest_support=None,
        nearest_resistance=None,
        broken_resistance=None,
        state=SupportResistanceState.INCOMPLETE,
        is_complete=False,
        incomplete_details=(detail,),
    )


def _to_finite_float(value: object, field_name: str) -> float:
    try:
        float_value = float(cast(Any, value))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if not math.isfinite(float_value):
        raise ValueError(f"{field_name} must be finite")
    return float_value


def _public_required_value(value: object) -> float:
    return _validate_required_float(_to_finite_float(value, "value"))


def _public_optional_value(value: object) -> float | None:
    if value is None:
        return None
    try:
        float_value = float(cast(Any, value))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("signal value must be finite") from exc
    if math.isnan(float_value):
        return None
    if math.isinf(float_value):
        raise ValueError("signal value must be finite")
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
    "BenchmarkRelativeStrength",
    "PriceLevelKind",
    "PriceLevelZone",
    "RelativeStrengthConfig",
    "RelativeStrengthIncompleteDetail",
    "RelativeStrengthIncompleteReason",
    "RelativeStrengthLabel",
    "RelativeStrengthSnapshot",
    "SupportResistanceConfig",
    "SupportResistanceIncompleteDetail",
    "SupportResistanceIncompleteReason",
    "SupportResistanceSnapshot",
    "SupportResistanceState",
    "calculate_relative_strength",
    "calculate_support_resistance",
]

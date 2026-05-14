"""Provider-free indicator snapshot refresh service."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import date, datetime
from typing import TYPE_CHECKING

from app.indicators.signals import (
    _DEFAULT_RELATIVE_STRENGTH_CONFIG,
    _DEFAULT_SUPPORT_RESISTANCE_CONFIG,
    RelativeStrengthConfig,
    RelativeStrengthSnapshot,
    SupportResistanceConfig,
    SupportResistanceSnapshot,
    calculate_relative_strength,
    calculate_support_resistance,
)
from app.indicators.snapshots import (
    INDICATOR_CALCULATION_VERSION,
    IndicatorRefreshFailure,
    IndicatorRefreshSummary,
    IndicatorSnapshotCreate,
    IndicatorSnapshotIncompleteDetail,
)
from app.indicators.technical import (
    _DEFAULT_INDICATOR_CONFIG,
    IndicatorConfig,
    TechnicalIndicatorSnapshot,
    calculate_technical_indicators,
)
from app.market_data.schemas import DailyCandle, DataRecency, normalize_symbol

if TYPE_CHECKING:
    from app.persistence.repositories import DailyCandleRepository, IndicatorSnapshotRepository

logger = logging.getLogger(__name__)


def refresh_indicator_snapshots(
    *,
    symbols: Sequence[str],
    candle_repository: DailyCandleRepository,
    snapshot_repository: IndicatorSnapshotRepository,
    calculated_at: datetime,
    provider: str | None = None,
    adjusted: bool = True,
    candle_limit: int = 260,
    calculation_version: str = INDICATOR_CALCULATION_VERSION,
    indicator_config: IndicatorConfig = _DEFAULT_INDICATOR_CONFIG,
    support_resistance_config: SupportResistanceConfig = _DEFAULT_SUPPORT_RESISTANCE_CONFIG,
    relative_strength_config: RelativeStrengthConfig = _DEFAULT_RELATIVE_STRENGTH_CONFIG,
) -> IndicatorRefreshSummary:
    """Recompute and persist indicator snapshots from cached daily candles."""
    _validate_calculated_at(calculated_at)
    if candle_limit <= 0:
        raise ValueError("candle_limit must be greater than 0")

    requested_symbols = _normalize_symbols(symbols)
    created_snapshot_ids: list[int] = []
    failures: list[IndicatorRefreshFailure] = []
    calculation_date = calculated_at.date()

    for symbol in requested_symbols:
        try:
            ticker_candles = candle_repository.get_recent(
                symbol,
                limit=candle_limit,
                provider=provider,
                adjusted=adjusted,
                end_date=calculation_date,
            )
            benchmark_candles = _load_benchmark_candles(
                candle_repository=candle_repository,
                relative_strength_config=relative_strength_config,
                candle_limit=candle_limit,
                provider=provider,
                adjusted=adjusted,
                end_date=calculation_date,
            )

            technical_snapshot = calculate_technical_indicators(
                ticker_candles,
                indicator_config,
            )
            support_resistance_snapshot = calculate_support_resistance(
                ticker_candles,
                support_resistance_config,
            )
            relative_strength_snapshot = calculate_relative_strength(
                ticker_candles,
                benchmark_candles,
                relative_strength_config,
            )
            snapshot = _build_snapshot_create(
                symbol=symbol,
                provider=provider,
                adjusted=adjusted,
                calculated_at=calculated_at,
                calculation_date=calculation_date,
                calculation_version=calculation_version,
                ticker_candles=ticker_candles,
                technical_snapshot=technical_snapshot,
                support_resistance_snapshot=support_resistance_snapshot,
                relative_strength_snapshot=relative_strength_snapshot,
                relative_strength_config=relative_strength_config,
            )
            record = snapshot_repository.create(snapshot)
        except Exception as exc:
            failure = _failure(
                symbol=symbol,
                provider=provider,
                calculation_date=calculation_date,
                calculation_version=calculation_version,
                exc=exc,
            )
            _log_failure(failure)
            failures.append(failure)
            continue

        created_snapshot_ids.append(record.id)

    return IndicatorRefreshSummary(
        requested_symbols=requested_symbols,
        succeeded_count=len(created_snapshot_ids),
        failed_count=len(failures),
        created_snapshot_ids=tuple(created_snapshot_ids),
        failures=tuple(failures),
    )


def _load_benchmark_candles(
    *,
    candle_repository: DailyCandleRepository,
    relative_strength_config: RelativeStrengthConfig,
    candle_limit: int,
    provider: str | None,
    adjusted: bool,
    end_date: date,
) -> dict[str, tuple[DailyCandle, ...]]:
    candles_by_symbol: dict[str, tuple[DailyCandle, ...]] = {}
    for benchmark_symbol in relative_strength_config.benchmark_symbols:
        candles_by_symbol[benchmark_symbol] = candle_repository.get_recent(
            benchmark_symbol,
            limit=candle_limit,
            provider=provider,
            adjusted=adjusted,
            end_date=end_date,
        )
    return candles_by_symbol


def _build_snapshot_create(
    *,
    symbol: str,
    provider: str | None,
    adjusted: bool,
    calculated_at: datetime,
    calculation_date: date,
    calculation_version: str,
    ticker_candles: Sequence[DailyCandle],
    technical_snapshot: TechnicalIndicatorSnapshot,
    support_resistance_snapshot: SupportResistanceSnapshot,
    relative_strength_snapshot: RelativeStrengthSnapshot,
    relative_strength_config: RelativeStrengthConfig,
) -> IndicatorSnapshotCreate:
    input_start_session_date = ticker_candles[0].session_date if ticker_candles else None
    input_end_session_date = ticker_candles[-1].session_date if ticker_candles else None
    relative_required_candles = max(relative_strength_config.lookback_periods) + 1
    required_candles = max(
        technical_snapshot.required_candles,
        support_resistance_snapshot.required_candles,
        relative_required_candles,
    )
    incomplete_details = _incomplete_details(
        technical_snapshot=technical_snapshot,
        support_resistance_snapshot=support_resistance_snapshot,
        relative_strength_snapshot=relative_strength_snapshot,
    )

    return IndicatorSnapshotCreate(
        symbol=_first_text(
            technical_snapshot.symbol,
            support_resistance_snapshot.symbol,
            relative_strength_snapshot.symbol,
            symbol,
        ),
        provider=_first_text(
            technical_snapshot.provider,
            support_resistance_snapshot.provider,
            relative_strength_snapshot.provider,
            provider,
            "unknown",
        ),
        calculation_date=calculation_date,
        calculated_at=calculated_at,
        calculation_version=calculation_version,
        adjusted=_first_bool(
            technical_snapshot.adjusted,
            support_resistance_snapshot.adjusted,
            relative_strength_snapshot.adjusted,
            adjusted,
        ),
        data_recency=_first_data_recency(
            technical_snapshot.data_recency,
            support_resistance_snapshot.data_recency,
            relative_strength_snapshot.data_recency,
        ),
        input_start_session_date=input_start_session_date,
        input_end_session_date=input_end_session_date,
        available_candles=len(ticker_candles),
        required_candles=required_candles,
        is_complete=(
            technical_snapshot.is_complete
            and support_resistance_snapshot.is_complete
            and relative_strength_snapshot.is_complete
        ),
        technical_is_complete=technical_snapshot.is_complete,
        support_resistance_is_complete=support_resistance_snapshot.is_complete,
        relative_strength_is_complete=relative_strength_snapshot.is_complete,
        benchmark_symbols=relative_strength_snapshot.benchmark_symbols,
        relative_strength_lookback_periods=relative_strength_snapshot.lookback_periods,
        technical_snapshot=technical_snapshot,
        support_resistance_snapshot=support_resistance_snapshot,
        relative_strength_snapshot=relative_strength_snapshot,
        incomplete_details=incomplete_details,
    )


def _incomplete_details(
    *,
    technical_snapshot: TechnicalIndicatorSnapshot,
    support_resistance_snapshot: SupportResistanceSnapshot,
    relative_strength_snapshot: RelativeStrengthSnapshot,
) -> tuple[IndicatorSnapshotIncompleteDetail, ...]:
    details: list[IndicatorSnapshotIncompleteDetail] = []
    for technical_detail in technical_snapshot.incomplete_details:
        details.append(
            IndicatorSnapshotIncompleteDetail(
                section="technical",
                detail=technical_detail.model_dump(mode="json"),
            )
        )
    for support_resistance_detail in support_resistance_snapshot.incomplete_details:
        details.append(
            IndicatorSnapshotIncompleteDetail(
                section="support_resistance",
                detail=support_resistance_detail.model_dump(mode="json"),
            )
        )
    for relative_strength_detail in relative_strength_snapshot.incomplete_details:
        details.append(
            IndicatorSnapshotIncompleteDetail(
                section="relative_strength",
                detail=relative_strength_detail.model_dump(mode="json"),
            )
        )
    return tuple(details)


def _failure(
    *,
    symbol: str,
    provider: str | None,
    calculation_date: date,
    calculation_version: str,
    exc: Exception,
) -> IndicatorRefreshFailure:
    return IndicatorRefreshFailure(
        symbol=symbol,
        provider=provider,
        calculation_date=calculation_date,
        calculation_version=calculation_version,
        error_type=exc.__class__.__name__,
        message="Indicator refresh failed.",
    )


def _log_failure(failure: IndicatorRefreshFailure) -> None:
    logger.warning(
        "Indicator refresh failed symbol=%s provider=%s calculation_date=%s "
        "calculation_version=%s error_type=%s error_message=%s",
        failure.symbol,
        failure.provider or "any",
        failure.calculation_date.isoformat(),
        failure.calculation_version,
        failure.error_type,
        failure.message,
    )


def _normalize_symbols(symbols: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_symbol in symbols:
        symbol = normalize_symbol(raw_symbol)
        if symbol not in seen:
            normalized.append(symbol)
            seen.add(symbol)
    return tuple(normalized)


def _validate_calculated_at(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("calculated_at must be timezone-aware")


def _first_text(*values: str | None) -> str:
    for value in values:
        if value:
            return value
    raise ValueError("at least one text value is required")


def _first_bool(*values: bool | None) -> bool:
    for value in values:
        if value is not None:
            return value
    raise ValueError("at least one boolean value is required")


def _first_data_recency(*values: DataRecency) -> DataRecency:
    for value in values:
        if value is not DataRecency.UNKNOWN:
            return value
    return DataRecency.UNKNOWN


__all__ = ["refresh_indicator_snapshots"]

"""Persisted indicator snapshot contracts."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Self

from pydantic import field_validator, model_validator

from app.indicators.signals import RelativeStrengthSnapshot, SupportResistanceSnapshot
from app.indicators.technical import TechnicalIndicatorSnapshot
from app.market_data.schemas import (
    DataRecency,
    MarketDataModel,
    normalize_required_text,
    normalize_symbol,
)

INDICATOR_CALCULATION_VERSION = "indicator-v1"
IndicatorSnapshotSection = Literal["technical", "support_resistance", "relative_strength"]


class IndicatorSnapshotIncompleteDetail(MarketDataModel):
    """Section-tagged incomplete detail persisted with an indicator snapshot."""

    section: IndicatorSnapshotSection
    detail: dict[str, Any]


class IndicatorSnapshotCreate(MarketDataModel):
    """Write contract for one persisted indicator snapshot."""

    symbol: str
    provider: str
    calculation_date: date
    calculated_at: datetime
    calculation_version: str = INDICATOR_CALCULATION_VERSION
    adjusted: bool
    data_recency: DataRecency
    input_start_session_date: date | None
    input_end_session_date: date | None
    available_candles: int
    required_candles: int
    is_complete: bool
    technical_is_complete: bool
    support_resistance_is_complete: bool
    relative_strength_is_complete: bool
    benchmark_symbols: tuple[str, ...] = ()
    relative_strength_lookback_periods: tuple[int, ...] = ()
    technical_snapshot: TechnicalIndicatorSnapshot
    support_resistance_snapshot: SupportResistanceSnapshot
    relative_strength_snapshot: RelativeStrengthSnapshot
    incomplete_details: tuple[IndicatorSnapshotIncompleteDetail, ...] = ()

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> str:
        """Normalize supported ticker symbols."""
        return normalize_symbol(value)

    @field_validator("provider", "calculation_version", mode="before")
    @classmethod
    def validate_required_text(cls, value: object, info: object) -> str:
        """Require non-empty provider and version labels."""
        field_name = getattr(info, "field_name", None) or "field"
        return normalize_required_text(value, str(field_name))

    @field_validator("calculated_at")
    @classmethod
    def validate_calculated_at(cls, value: datetime) -> datetime:
        """Require a timezone-aware calculation timestamp."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("calculated_at must be timezone-aware")
        return value

    @field_validator("available_candles", "required_candles")
    @classmethod
    def validate_non_negative_count(cls, value: int) -> int:
        """Require non-negative persisted candle-count metadata."""
        if value < 0:
            raise ValueError("candle counts must be non-negative")
        return value

    @field_validator("benchmark_symbols", mode="before")
    @classmethod
    def validate_benchmark_symbols(cls, value: object) -> tuple[str, ...]:
        """Normalize and de-duplicate benchmark symbols."""
        if value is None:
            return ()
        if isinstance(value, str):
            raw_values: tuple[object, ...] = (value,)
        elif isinstance(value, (list, tuple)):
            raw_values = tuple(value)
        else:
            raise ValueError("benchmark_symbols must be a symbol or sequence of symbols")

        normalized: list[str] = []
        seen: set[str] = set()
        for raw_value in raw_values:
            symbol = normalize_symbol(raw_value)
            if symbol not in seen:
                normalized.append(symbol)
                seen.add(symbol)
        return tuple(normalized)

    @field_validator("relative_strength_lookback_periods")
    @classmethod
    def validate_lookback_periods(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        """Require positive relative-strength lookback metadata."""
        if any(period <= 0 for period in value):
            raise ValueError("relative_strength_lookback_periods must be positive")
        return tuple(sorted(set(value)))

    @model_validator(mode="after")
    def validate_input_range(self) -> Self:
        """Require coherent input date range metadata when both dates are present."""
        if (
            self.input_start_session_date is not None
            and self.input_end_session_date is not None
            and self.input_start_session_date > self.input_end_session_date
        ):
            raise ValueError("input_start_session_date must be on or before input_end_session_date")
        return self


class IndicatorSnapshot(IndicatorSnapshotCreate):
    """Read contract for one persisted indicator snapshot."""

    id: int
    created_at: datetime

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: int) -> int:
        """Require a positive persisted record id."""
        if value <= 0:
            raise ValueError("id must be positive")
        return value

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        """Require a timezone-aware creation timestamp."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value


class IndicatorRefreshFailure(MarketDataModel):
    """Per-symbol failure returned by the indicator refresh service."""

    symbol: str
    provider: str | None = None
    calculation_date: date
    calculation_version: str = INDICATOR_CALCULATION_VERSION
    error_type: str
    message: str

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> str:
        """Normalize failed ticker symbols."""
        return normalize_symbol(value)

    @field_validator("provider", mode="before")
    @classmethod
    def validate_provider(cls, value: object) -> str | None:
        """Normalize optional provider labels."""
        if value is None:
            return None
        return normalize_required_text(value, "provider")

    @field_validator("calculation_version", "error_type", "message", mode="before")
    @classmethod
    def validate_text(cls, value: object, info: object) -> str:
        """Require non-empty failure context text."""
        field_name = getattr(info, "field_name", None) or "field"
        return normalize_required_text(value, str(field_name))


class IndicatorRefreshSummary(MarketDataModel):
    """Summary returned after an indicator snapshot refresh run."""

    requested_symbols: tuple[str, ...]
    succeeded_count: int
    failed_count: int
    created_snapshot_ids: tuple[int, ...] = ()
    failures: tuple[IndicatorRefreshFailure, ...] = ()

    @field_validator("requested_symbols", mode="before")
    @classmethod
    def validate_requested_symbols(cls, value: object) -> tuple[str, ...]:
        """Normalize and de-duplicate requested ticker symbols."""
        if isinstance(value, str):
            raw_values: tuple[object, ...] = (value,)
        elif isinstance(value, (list, tuple)):
            raw_values = tuple(value)
        else:
            raise ValueError("requested_symbols must be a symbol or sequence of symbols")

        normalized: list[str] = []
        seen: set[str] = set()
        for raw_value in raw_values:
            symbol = normalize_symbol(raw_value)
            if symbol not in seen:
                normalized.append(symbol)
                seen.add(symbol)
        return tuple(normalized)

    @field_validator("succeeded_count", "failed_count")
    @classmethod
    def validate_non_negative_count(cls, value: int) -> int:
        """Require non-negative refresh counters."""
        if value < 0:
            raise ValueError("refresh counts must be non-negative")
        return value

    @field_validator("created_snapshot_ids")
    @classmethod
    def validate_created_snapshot_ids(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        """Require positive created snapshot ids."""
        if any(snapshot_id <= 0 for snapshot_id in value):
            raise ValueError("created_snapshot_ids must contain positive ids")
        return value

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        """Ensure summary counters match detailed result collections."""
        if self.succeeded_count != len(self.created_snapshot_ids):
            raise ValueError("succeeded_count must match created_snapshot_ids")
        if self.failed_count != len(self.failures):
            raise ValueError("failed_count must match failures")
        if self.succeeded_count + self.failed_count != len(self.requested_symbols):
            raise ValueError("refresh counts must match requested_symbols")
        return self


__all__ = [
    "INDICATOR_CALCULATION_VERSION",
    "IndicatorRefreshFailure",
    "IndicatorRefreshSummary",
    "IndicatorSnapshot",
    "IndicatorSnapshotCreate",
    "IndicatorSnapshotIncompleteDetail",
    "IndicatorSnapshotSection",
]

"""Indicator snapshot repository tests."""

from __future__ import annotations

from collections.abc import Generator, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import cast

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.indicators.signals import (
    RelativeStrengthConfig,
    RelativeStrengthSnapshot,
    SupportResistanceConfig,
    SupportResistanceSnapshot,
    calculate_relative_strength,
    calculate_support_resistance,
)
from app.indicators.snapshots import (
    INDICATOR_CALCULATION_VERSION,
    IndicatorSnapshotCreate,
    IndicatorSnapshotIncompleteDetail,
)
from app.indicators.technical import (
    IndicatorConfig,
    TechnicalIndicatorSnapshot,
    calculate_technical_indicators,
)
from app.market_data.schemas import DailyCandle
from app.persistence.base import Base
from app.persistence.models import IndicatorSnapshotRecord
from app.persistence.repositories import IndicatorSnapshotRepository

START_DATE = date(2026, 5, 1)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Return a fresh in-memory SQLite session with persistence metadata."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_indicator_snapshot_repository_creates_snapshot_record(db_session: Session) -> None:
    repository = IndicatorSnapshotRepository(db_session)
    calculated_at = datetime(2026, 5, 8, 21, 0, tzinfo=UTC)

    record = repository.create(indicator_snapshot(calculated_at=calculated_at))

    assert isinstance(record, IndicatorSnapshotRecord)
    assert record.id > 0
    assert record.symbol == "AAPL"
    assert record.provider == "fixture"
    assert record.calculation_date == date(2026, 5, 8)
    assert record.calculated_at.tzinfo is not None
    assert record.calculation_version == INDICATOR_CALCULATION_VERSION
    assert record.input_start_session_date == START_DATE
    assert record.input_end_session_date == START_DATE + timedelta(days=2)
    assert record.available_candles == 3
    assert record.benchmark_symbols == ["SPY"]
    assert record.relative_strength_lookback_periods == [1]
    assert record.technical_snapshot["symbol"] == "AAPL"
    assert record.relative_strength_snapshot["benchmark_symbols"] == ["SPY"]
    assert db_session.scalar(select(func.count()).select_from(IndicatorSnapshotRecord)) == 1


def test_indicator_snapshot_repository_returns_latest_snapshot_by_date_and_run(
    db_session: Session,
) -> None:
    repository = IndicatorSnapshotRepository(db_session)
    first = repository.create(
        indicator_snapshot(calculated_at=datetime(2026, 5, 8, 20, 0, tzinfo=UTC))
    )
    second = repository.create(
        indicator_snapshot(calculated_at=datetime(2026, 5, 8, 21, 0, tzinfo=UTC))
    )
    third = repository.create(
        indicator_snapshot(calculated_at=datetime(2026, 5, 9, 20, 0, tzinfo=UTC))
    )

    latest = repository.get_latest("aapl", provider="fixture")

    assert latest is not None
    assert latest.id == third.id
    assert latest.id != first.id
    assert latest.id != second.id
    assert repository.get_latest("MSFT") is None


def test_indicator_snapshot_repository_filters_by_version_provider_and_adjusted(
    db_session: Session,
) -> None:
    repository = IndicatorSnapshotRepository(db_session)
    v1 = repository.create(
        indicator_snapshot(
            calculated_at=datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
            calculation_version="indicator-v1",
        )
    )
    v2 = repository.create(
        indicator_snapshot(
            calculated_at=datetime(2026, 5, 9, 20, 0, tzinfo=UTC),
            calculation_version="indicator-v2",
        )
    )
    other_provider = repository.create(
        indicator_snapshot(
            provider="other",
            calculated_at=datetime(2026, 5, 10, 20, 0, tzinfo=UTC),
            calculation_version="indicator-v2",
        )
    )
    unadjusted = repository.create(
        indicator_snapshot(
            adjusted=False,
            calculated_at=datetime(2026, 5, 11, 20, 0, tzinfo=UTC),
            calculation_version="indicator-v2",
        )
    )

    latest_v1 = repository.get_latest_for_version(
        "aapl",
        "indicator-v1",
        provider="fixture",
    )
    latest_v2 = repository.get_latest(
        "aapl",
        provider="fixture",
        calculation_version="indicator-v2",
    )

    assert latest_v1 is not None
    assert latest_v1.id == v1.id
    assert latest_v2 is not None
    assert latest_v2.id == v2.id
    latest_other_provider = repository.get_latest("AAPL", provider="other")
    latest_unadjusted = repository.get_latest("AAPL", adjusted=False)

    assert latest_other_provider is not None
    assert latest_other_provider.id == other_provider.id
    assert latest_unadjusted is not None
    assert latest_unadjusted.id == unadjusted.id
    assert repository.get_latest_for_version("AAPL", "missing-version") is None


def test_indicator_snapshot_repository_persists_incomplete_details(
    db_session: Session,
) -> None:
    repository = IndicatorSnapshotRepository(db_session)

    record = repository.create(
        indicator_snapshot(
            closes=(10,),
            calculated_at=datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
        )
    )

    assert record.is_complete is False
    assert record.technical_is_complete is False
    assert record.support_resistance_is_complete is False
    assert record.relative_strength_is_complete is False
    assert {detail["section"] for detail in record.incomplete_details} == {
        "technical",
        "support_resistance",
        "relative_strength",
    }
    technical_details = [
        detail for detail in record.incomplete_details if detail["section"] == "technical"
    ]
    assert technical_details
    technical_detail_payload = cast(dict[str, object], technical_details[0]["detail"])
    assert technical_detail_payload["reason"] == "insufficient_history"


def indicator_snapshot(
    *,
    symbol: str = "AAPL",
    provider: str = "fixture",
    adjusted: bool = True,
    closes: Sequence[object] = (10, 11, 12),
    calculated_at: datetime,
    calculation_version: str = INDICATOR_CALCULATION_VERSION,
) -> IndicatorSnapshotCreate:
    """Build a persisted indicator snapshot from deterministic calculations."""
    candles = candle_series(closes, symbol=symbol, provider=provider, adjusted=adjusted)
    benchmark_candles = candle_series(
        tuple(100 + index for index, _ in enumerate(closes)),
        symbol="SPY",
        provider=provider,
        adjusted=adjusted,
    )
    indicator_config = compact_indicator_config()
    support_config = SupportResistanceConfig(
        lookback_period=3,
        pivot_left=1,
        pivot_right=1,
        zone_percent=0.01,
        proximity_percent=0.03,
        breakout_buffer_percent=0.005,
        max_levels=3,
    )
    relative_config = RelativeStrengthConfig(benchmark_symbols=("SPY",), lookback_periods=(1,))
    technical = calculate_technical_indicators(candles, indicator_config)
    support_resistance = calculate_support_resistance(candles, support_config)
    relative_strength = calculate_relative_strength(
        candles,
        {"SPY": benchmark_candles},
        relative_config,
    )
    incomplete_details = combined_incomplete_details(
        technical=technical,
        support_resistance=support_resistance,
        relative_strength=relative_strength,
    )

    return IndicatorSnapshotCreate(
        symbol=symbol,
        provider=provider,
        calculation_date=calculated_at.date(),
        calculated_at=calculated_at,
        calculation_version=calculation_version,
        adjusted=adjusted,
        data_recency=technical.data_recency,
        input_start_session_date=candles[0].session_date if candles else None,
        input_end_session_date=candles[-1].session_date if candles else None,
        available_candles=len(candles),
        required_candles=max(
            technical.required_candles,
            support_resistance.required_candles,
            max(relative_config.lookback_periods) + 1,
        ),
        is_complete=technical.is_complete
        and support_resistance.is_complete
        and relative_strength.is_complete,
        technical_is_complete=technical.is_complete,
        support_resistance_is_complete=support_resistance.is_complete,
        relative_strength_is_complete=relative_strength.is_complete,
        benchmark_symbols=relative_strength.benchmark_symbols,
        relative_strength_lookback_periods=relative_strength.lookback_periods,
        technical_snapshot=technical,
        support_resistance_snapshot=support_resistance,
        relative_strength_snapshot=relative_strength,
        incomplete_details=incomplete_details,
    )


def candle_series(
    closes: Sequence[object],
    *,
    symbol: str,
    provider: str,
    adjusted: bool = True,
) -> tuple[DailyCandle, ...]:
    """Build sequential normalized daily candles."""
    return tuple(
        candle(
            symbol=symbol,
            provider=provider,
            adjusted=adjusted,
            session_date=START_DATE + timedelta(days=index),
            close=close,
        )
        for index, close in enumerate(closes)
    )


def candle(**overrides: object) -> DailyCandle:
    """Build a normalized daily candle."""
    session_date = cast(date, overrides.get("session_date", START_DATE))
    close = decimal_value(overrides.get("close", "100"))
    open_price = decimal_value(overrides.get("open", close))
    high = decimal_value(overrides.get("high", max(open_price, close) + Decimal("1")))
    low = decimal_value(overrides.get("low", min(open_price, close) - Decimal("1")))
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
        "open": decimal_text(open_price),
        "high": decimal_text(high),
        "low": decimal_text(low),
        "close": decimal_text(close),
        "volume": 100,
        "adjusted": True,
        "provider": "fixture",
        "data_recency": "delayed",
    }
    payload.update(overrides)
    return DailyCandle.model_validate(payload)


def compact_indicator_config() -> IndicatorConfig:
    """Build a compact config for persistence fixtures."""
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


def combined_incomplete_details(
    *,
    technical: TechnicalIndicatorSnapshot,
    support_resistance: SupportResistanceSnapshot,
    relative_strength: RelativeStrengthSnapshot,
) -> tuple[IndicatorSnapshotIncompleteDetail, ...]:
    """Build section-tagged incomplete details for test snapshots."""
    details: list[IndicatorSnapshotIncompleteDetail] = []
    for technical_detail in technical.incomplete_details:
        details.append(
            IndicatorSnapshotIncompleteDetail(
                section="technical",
                detail=technical_detail.model_dump(mode="json"),
            )
        )
    for support_resistance_detail in support_resistance.incomplete_details:
        details.append(
            IndicatorSnapshotIncompleteDetail(
                section="support_resistance",
                detail=support_resistance_detail.model_dump(mode="json"),
            )
        )
    for relative_strength_detail in relative_strength.incomplete_details:
        details.append(
            IndicatorSnapshotIncompleteDetail(
                section="relative_strength",
                detail=relative_strength_detail.model_dump(mode="json"),
            )
        )
    return tuple(details)


def decimal_value(value: object) -> Decimal:
    """Return a Decimal for fixture numeric inputs."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def decimal_text(value: Decimal) -> str:
    """Return a plain decimal string."""
    return format(value, "f")

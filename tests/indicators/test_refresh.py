"""Indicator snapshot refresh service tests."""

from __future__ import annotations

import logging
from collections.abc import Generator, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any, NoReturn, cast

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.indicators.refresh import refresh_indicator_snapshots
from app.indicators.signals import RelativeStrengthConfig, SupportResistanceConfig
from app.indicators.snapshots import (
    INDICATOR_CALCULATION_VERSION,
    IndicatorSnapshotCreate,
)
from app.indicators.technical import IndicatorConfig
from app.market_data.schemas import DailyCandle
from app.persistence.base import Base
from app.persistence.repositories import DailyCandleRepository, IndicatorSnapshotRepository

START_DATE = date(2026, 5, 1)
RETRIEVED_AT = datetime(2026, 5, 8, 21, 0, tzinfo=UTC)


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


def test_refresh_indicator_snapshots_persists_snapshot_from_cached_candles(
    db_session: Session,
) -> None:
    candle_repository = DailyCandleRepository(db_session)
    snapshot_repository = IndicatorSnapshotRepository(db_session)
    candle_repository.upsert_many(
        candle_series((10, 11, 12), symbol="AAPL"),
        retrieved_at=RETRIEVED_AT,
    )
    candle_repository.upsert_many(
        candle_series((100, 101, 102), symbol="SPY"),
        retrieved_at=RETRIEVED_AT,
    )
    candle_repository.upsert_many(
        candle_series((200, 201, 202), symbol="QQQ"),
        retrieved_at=RETRIEVED_AT,
    )

    summary = refresh_indicator_snapshots(
        symbols=("aapl", "AAPL"),
        candle_repository=candle_repository,
        snapshot_repository=snapshot_repository,
        calculated_at=datetime(2026, 5, 8, 22, 0, tzinfo=UTC),
        provider="fixture",
        candle_limit=10,
        indicator_config=compact_indicator_config(),
        support_resistance_config=compact_support_resistance_config(),
        relative_strength_config=RelativeStrengthConfig(
            benchmark_symbols=("SPY", "QQQ"),
            lookback_periods=(1,),
        ),
    )

    record = snapshot_repository.get_latest("AAPL", provider="fixture")

    assert summary.requested_symbols == ("AAPL",)
    assert summary.succeeded_count == 1
    assert summary.failed_count == 0
    assert len(summary.created_snapshot_ids) == 1
    assert record is not None
    assert record.id == summary.created_snapshot_ids[0]
    assert record.calculation_version == INDICATOR_CALCULATION_VERSION
    assert record.input_start_session_date == START_DATE
    assert record.input_end_session_date == START_DATE + timedelta(days=2)
    assert record.available_candles == 3
    assert record.technical_is_complete is True
    assert record.relative_strength_is_complete is True
    assert record.benchmark_symbols == ["SPY", "QQQ"]
    latest_technical = cast(dict[str, object], record.technical_snapshot["latest"])
    assert latest_technical["close"] == 12.0
    assert record.support_resistance_snapshot["symbol"] == "AAPL"
    assert record.relative_strength_snapshot["benchmark_symbols"] == ["SPY", "QQQ"]


def test_refresh_missing_benchmark_persists_relative_strength_incomplete_state(
    db_session: Session,
) -> None:
    candle_repository = DailyCandleRepository(db_session)
    snapshot_repository = IndicatorSnapshotRepository(db_session)
    candle_repository.upsert_many(
        candle_series((10, 11, 12), symbol="AAPL"),
        retrieved_at=RETRIEVED_AT,
    )

    summary = refresh_indicator_snapshots(
        symbols=("AAPL",),
        candle_repository=candle_repository,
        snapshot_repository=snapshot_repository,
        calculated_at=datetime(2026, 5, 8, 22, 0, tzinfo=UTC),
        provider="fixture",
        candle_limit=10,
        indicator_config=compact_indicator_config(),
        support_resistance_config=compact_support_resistance_config(),
        relative_strength_config=RelativeStrengthConfig(
            benchmark_symbols=("SPY",),
            lookback_periods=(1,),
        ),
    )

    record = snapshot_repository.get_latest("AAPL", provider="fixture")

    assert summary.succeeded_count == 1
    assert summary.failed_count == 0
    assert record is not None
    assert record.relative_strength_is_complete is False
    assert record.relative_strength_snapshot["overall_label"] == "incomplete"
    assert any(is_missing_benchmark_detail(detail) for detail in record.incomplete_details)


def test_refresh_failure_logs_context_without_secrets(
    db_session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    candle_repository = DailyCandleRepository(db_session)
    candle_repository.upsert_many(
        candle_series((10, 11, 12), symbol="AAPL"),
        retrieved_at=RETRIEVED_AT,
    )
    candle_repository.upsert_many(
        candle_series((100, 101, 102), symbol="SPY"),
        retrieved_at=RETRIEVED_AT,
    )
    snapshot_repository = cast(IndicatorSnapshotRepository, FailingSnapshotRepository())

    with caplog.at_level(logging.WARNING, logger="app.indicators.refresh"):
        summary = refresh_indicator_snapshots(
            symbols=("AAPL",),
            candle_repository=candle_repository,
            snapshot_repository=snapshot_repository,
            calculated_at=datetime(2026, 5, 8, 22, 0, tzinfo=UTC),
            provider="fixture",
            candle_limit=10,
            indicator_config=compact_indicator_config(),
            support_resistance_config=compact_support_resistance_config(),
            relative_strength_config=RelativeStrengthConfig(
                benchmark_symbols=("SPY",),
                lookback_periods=(1,),
            ),
        )

    assert summary.succeeded_count == 0
    assert summary.failed_count == 1
    assert summary.failures[0].error_type == "ValueError"
    assert summary.failures[0].message == "Indicator refresh failed."
    assert "symbol=AAPL" in caplog.text
    assert "provider=fixture" in caplog.text
    assert "calculation_date=2026-05-08" in caplog.text
    assert f"calculation_version={INDICATOR_CALCULATION_VERSION}" in caplog.text
    for forbidden_fragment in (
        "key",
        "token",
        "secret",
        "password",
        "Authorization",
        "apiKey",
        "database_url",
        "hunter2",
        "abc123",
        "bearer-token",
        "postgresql://example",
    ):
        assert forbidden_fragment not in caplog.text
        assert forbidden_fragment not in summary.failures[0].message


def test_refresh_malformed_cached_candles_fail_one_symbol_and_log_context(
    db_session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    candle_repository = DailyCandleRepository(db_session)
    snapshot_repository = IndicatorSnapshotRepository(db_session)
    candle_repository.upsert_many(
        candle_series((10, 11, 12), symbol="AAPL", provider="fixture"),
        retrieved_at=RETRIEVED_AT,
    )
    candle_repository.upsert_many(
        candle_series((10, 11, 12), symbol="AAPL", provider="other"),
        retrieved_at=RETRIEVED_AT,
    )
    candle_repository.upsert_many(
        candle_series((100, 101, 102), symbol="SPY", provider="fixture"),
        retrieved_at=RETRIEVED_AT,
    )

    with caplog.at_level(logging.WARNING, logger="app.indicators.refresh"):
        summary = refresh_indicator_snapshots(
            symbols=("AAPL",),
            candle_repository=candle_repository,
            snapshot_repository=snapshot_repository,
            calculated_at=datetime(2026, 5, 8, 22, 0, tzinfo=UTC),
            provider=None,
            candle_limit=10,
            indicator_config=compact_indicator_config(),
            support_resistance_config=compact_support_resistance_config(),
            relative_strength_config=RelativeStrengthConfig(
                benchmark_symbols=("SPY",),
                lookback_periods=(1,),
            ),
        )

    assert summary.succeeded_count == 0
    assert summary.failed_count == 1
    assert snapshot_repository.get_latest("AAPL", adjusted=True) is None
    assert "symbol=AAPL" in caplog.text
    assert "provider=any" in caplog.text
    assert "calculation_date=2026-05-08" in caplog.text
    for forbidden_fragment in (
        "token",
        "secret",
        "password",
        "Authorization",
        "apiKey",
        "database_url",
    ):
        assert forbidden_fragment not in caplog.text


class FailingSnapshotRepository:
    """Repository double that raises a sensitive-looking persistence error."""

    def create(self, snapshot: IndicatorSnapshotCreate) -> NoReturn:
        """Raise instead of persisting a snapshot."""
        raise ValueError(
            "apiKey=abc123 password=hunter2 Authorization=Bearer bearer-token "
            "database_url=postgresql://example"
        )


def is_missing_benchmark_detail(detail: dict[str, object]) -> bool:
    """Return whether a persisted incomplete detail describes a missing benchmark."""
    detail_payload = cast(dict[str, Any], detail["detail"])
    return (
        detail["section"] == "relative_strength" and detail_payload["reason"] == "missing_benchmark"
    )


def candle_series(
    closes: Sequence[object],
    *,
    symbol: str,
    provider: str = "fixture",
) -> tuple[DailyCandle, ...]:
    """Build sequential normalized daily candles."""
    return tuple(
        candle(
            symbol=symbol,
            provider=provider,
            session_date=START_DATE + timedelta(days=index),
            close=close,
        )
        for index, close in enumerate(closes)
    )


def candle(**overrides: object) -> DailyCandle:
    """Build a normalized daily candle."""
    session_date = overrides.get("session_date", START_DATE)
    if not isinstance(session_date, date):
        raise TypeError("session_date must be a date")
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
    """Build a compact config for refresh fixtures."""
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
    """Build a compact support/resistance config for refresh fixtures."""
    return SupportResistanceConfig(
        lookback_period=3,
        pivot_left=1,
        pivot_right=1,
        zone_percent=0.01,
        proximity_percent=0.03,
        breakout_buffer_percent=0.005,
        max_levels=3,
    )


def decimal_value(value: object) -> Decimal:
    """Return a Decimal for fixture numeric inputs."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def decimal_text(value: Decimal) -> str:
    """Return a plain decimal string."""
    return format(value, "f")

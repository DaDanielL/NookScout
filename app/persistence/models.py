"""SQLAlchemy ORM models for normalized persistence records."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base
from app.persistence.types import AwareDateTime, utc_now


class IngestionRunStatus(StrEnum):
    """Lifecycle states for market-data ingestion runs."""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class IngestionRunType(StrEnum):
    """Known market-data ingestion run types."""

    TICKER_REFERENCE = "ticker_reference"
    DAILY_CANDLES = "daily_candles"
    QUOTE_SNAPSHOT = "quote_snapshot"
    MARKET_DATA_REFRESH = "market_data_refresh"


class TickerRecord(Base):
    """Current normalized ticker reference data for one symbol/provider pair."""

    __tablename__ = "tickers"
    __table_args__ = (
        UniqueConstraint("symbol", "provider", name="uq_tickers_symbol_provider"),
        Index("ix_tickers_symbol_provider", "symbol", "provider"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(30), nullable=False)
    primary_exchange: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_otc: Mapped[bool] = mapped_column(Boolean, nullable=False)
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)
    average_daily_volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    as_of: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    data_recency: Mapped[str] = mapped_column(String(30), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        AwareDateTime(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class DailyCandleRecord(Base):
    """Normalized daily OHLCV candle for one symbol/provider/session."""

    __tablename__ = "daily_candles"
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "provider",
            "session_date",
            "adjusted",
            name="uq_daily_candles_symbol_provider_session_adjusted",
        ),
        Index("ix_daily_candles_symbol_session_date", "symbol", "session_date"),
        Index(
            "ix_daily_candles_symbol_provider_session_date",
            "symbol",
            "provider",
            "session_date",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    vwap: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    trade_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    adjusted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    data_recency: Mapped[str] = mapped_column(String(30), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        AwareDateTime(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class QuoteSnapshotRecord(Base):
    """Normalized quote snapshot for one symbol/provider/as-of instant."""

    __tablename__ = "quote_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "provider",
            "as_of",
            name="uq_quote_snapshots_symbol_provider_as_of",
        ),
        Index(
            "ix_quote_snapshots_symbol_provider_retrieved_at",
            "symbol",
            "provider",
            "retrieved_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    last_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    bid_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    ask_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    day_open: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    day_high: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    day_low: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    previous_close: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    day_volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    as_of: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    data_recency: Mapped[str] = mapped_column(String(30), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), default=utc_now, nullable=False)


class IndicatorSnapshotRecord(Base):
    """Versioned deterministic indicator snapshot for one symbol/calculation run."""

    __tablename__ = "indicator_snapshots"
    __table_args__ = (
        Index(
            "ix_indicator_snapshots_symbol_provider_calculation_date",
            "symbol",
            "provider",
            "calculation_date",
        ),
        Index(
            "ix_indicator_snapshots_symbol_provider_version_date",
            "symbol",
            "provider",
            "calculation_version",
            "calculation_date",
        ),
        Index(
            "ix_indicator_snapshots_version_calculated_at",
            "calculation_version",
            "calculated_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    calculation_date: Mapped[date] = mapped_column(Date, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    calculation_version: Mapped[str] = mapped_column(String(80), nullable=False)
    adjusted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    data_recency: Mapped[str] = mapped_column(String(30), nullable=False)
    input_start_session_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    input_end_session_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    available_candles: Mapped[int] = mapped_column(Integer, nullable=False)
    required_candles: Mapped[int] = mapped_column(Integer, nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False)
    technical_is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False)
    support_resistance_is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False)
    relative_strength_is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False)
    benchmark_symbols: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    relative_strength_lookback_periods: Mapped[list[int] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    technical_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    support_resistance_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    relative_strength_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    incomplete_details: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), default=utc_now, nullable=False)


class IngestionRunRecord(Base):
    """Metadata for a local market-data ingestion run."""

    __tablename__ = "ingestion_runs"
    __table_args__ = (
        Index(
            "ix_ingestion_runs_provider_run_type_started_at",
            "provider",
            "run_type",
            "started_at",
        ),
        Index("ix_ingestion_runs_status_started_at", "status", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    run_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=IngestionRunStatus.RUNNING.value,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(AwareDateTime(), nullable=True)
    requested_symbols: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    succeeded_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        AwareDateTime(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


__all__ = [
    "DailyCandleRecord",
    "IndicatorSnapshotRecord",
    "IngestionRunRecord",
    "IngestionRunStatus",
    "IngestionRunType",
    "QuoteSnapshotRecord",
    "TickerRecord",
]

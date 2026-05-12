"""Persistence repository tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.market_data.schemas import DailyCandle, Quote, TickerReference
from app.persistence.base import Base
from app.persistence.models import (
    DailyCandleRecord,
    IngestionRunRecord,
    IngestionRunStatus,
    IngestionRunType,
    QuoteSnapshotRecord,
    TickerRecord,
)
from app.persistence.repositories import (
    DailyCandleRepository,
    IngestionRunRepository,
    QuoteSnapshotRepository,
    TickerRepository,
)


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


def quote_payload(**overrides: object) -> dict[str, object]:
    """Return a valid normalized quote payload with optional overrides."""
    payload: dict[str, object] = {
        "symbol": "AAPL",
        "last_price": "187.50",
        "bid_price": "187.45",
        "ask_price": "187.55",
        "day_open": "185.00",
        "day_high": "188.00",
        "day_low": "184.50",
        "previous_close": "184.25",
        "day_volume": 82_000_000,
        "as_of": datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
        "provider": "fixture",
        "data_recency": "delayed",
    }
    payload.update(overrides)
    return payload


def candle_payload(**overrides: object) -> dict[str, object]:
    """Return a valid normalized daily candle payload with optional overrides."""
    payload: dict[str, object] = {
        "symbol": "AAPL",
        "session_date": date(2026, 5, 8),
        "timestamp": datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
        "open": "185.00",
        "high": "188.00",
        "low": "184.50",
        "close": "187.50",
        "volume": 82_000_000,
        "vwap": "186.75",
        "trade_count": 1_200_000,
        "adjusted": True,
        "provider": "fixture",
        "data_recency": "delayed",
    }
    payload.update(overrides)
    return payload


def reference_payload(**overrides: object) -> dict[str, object]:
    """Return a valid normalized ticker reference payload with optional overrides."""
    payload: dict[str, object] = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "asset_type": "stock",
        "primary_exchange": "NASDAQ",
        "currency": "USD",
        "is_active": True,
        "is_otc": False,
        "market_cap": "2900000000000",
        "average_daily_volume": 60_000_000,
        "provider": "fixture",
        "as_of": datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
        "data_recency": "delayed",
    }
    payload.update(overrides)
    return payload


def quote(**overrides: object) -> Quote:
    """Build a normalized quote."""
    return Quote.model_validate(quote_payload(**overrides))


def candle(**overrides: object) -> DailyCandle:
    """Build a normalized daily candle."""
    return DailyCandle.model_validate(candle_payload(**overrides))


def reference(**overrides: object) -> TickerReference:
    """Build normalized ticker reference data."""
    return TickerReference.model_validate(reference_payload(**overrides))


def test_ticker_repository_upserts_reference_and_returns_domain_contract(
    db_session: Session,
) -> None:
    repository = TickerRepository(db_session)
    retrieved_at = datetime(2026, 5, 8, 21, 0, tzinfo=UTC)

    record = repository.upsert_reference(reference(symbol="aapl"), retrieved_at=retrieved_at)
    cached = repository.get_reference("aapl")

    assert isinstance(record, TickerRecord)
    assert isinstance(cached, TickerReference)
    assert cached.symbol == "AAPL"
    assert cached.name == "Apple Inc."
    assert cached.market_cap == Decimal("2900000000000.0000")
    assert cached.as_of.tzinfo is not None

    updated = repository.upsert_reference(
        reference(name="Apple Fixture Updated", market_cap="3000000000000"),
        retrieved_at=datetime(2026, 5, 8, 22, 0, tzinfo=UTC),
    )

    assert updated.id == record.id
    updated_cached = repository.get_reference("AAPL", provider="fixture")
    assert updated_cached is not None
    assert updated_cached.name == "Apple Fixture Updated"
    assert repository.get_reference("MSFT") is None
    assert repository.get_reference("AAPL", provider="other") is None
    assert db_session.scalar(select(func.count()).select_from(TickerRecord)) == 1


def test_daily_candle_repository_upserts_and_returns_ordered_domain_contracts(
    db_session: Session,
) -> None:
    repository = DailyCandleRepository(db_session)
    retrieved_at = datetime(2026, 5, 8, 21, 0, tzinfo=UTC)
    candles = (
        candle(
            session_date=date(2026, 5, 7),
            timestamp=datetime(2026, 5, 7, 20, 0, tzinfo=UTC),
            close="186.00",
        ),
        candle(session_date=date(2026, 5, 8), timestamp=datetime(2026, 5, 8, 20, 0, tzinfo=UTC)),
    )

    written_count = repository.upsert_many(candles, retrieved_at=retrieved_at)
    repository.upsert_many(
        (
            candle(
                session_date=date(2026, 5, 8),
                timestamp=datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
                close="188.00",
                high="189.00",
            ),
        ),
        retrieved_at=datetime(2026, 5, 8, 22, 0, tzinfo=UTC),
    )

    cached = repository.get_range(
        "aapl",
        date(2026, 5, 7),
        date(2026, 5, 8),
        provider="fixture",
    )

    assert written_count == 2
    assert all(isinstance(item, DailyCandle) for item in cached)
    assert [item.session_date for item in cached] == [date(2026, 5, 7), date(2026, 5, 8)]
    assert [item.close for item in cached] == [Decimal("186.000000"), Decimal("188.000000")]
    assert cached[0].timestamp.tzinfo is not None
    assert repository.get_range("AAPL", date(2026, 5, 7), date(2026, 5, 8), adjusted=False) == ()
    assert repository.get_range("AAPL", date(2026, 5, 1), date(2026, 5, 2)) == ()
    assert repository.get_range("AAPL", date(2026, 5, 9), date(2026, 5, 8)) == ()
    assert db_session.scalar(select(func.count()).select_from(DailyCandleRecord)) == 2


def test_quote_snapshot_repository_upserts_and_returns_latest_domain_contract(
    db_session: Session,
) -> None:
    repository = QuoteSnapshotRepository(db_session)
    retrieved_at = datetime(2026, 5, 8, 21, 0, tzinfo=UTC)
    first_quote = quote()

    record = repository.upsert_snapshot(first_quote, retrieved_at=retrieved_at)
    updated_record = repository.upsert_snapshot(
        quote(last_price="187.75", day_high="188.50"),
        retrieved_at=datetime(2026, 5, 8, 21, 5, tzinfo=UTC),
    )
    repository.upsert_snapshot(
        quote(
            last_price="188.50",
            day_high="189.00",
            as_of=datetime(2026, 5, 8, 21, 0, tzinfo=UTC),
        ),
        retrieved_at=datetime(2026, 5, 8, 21, 10, tzinfo=UTC),
    )

    latest = repository.get_latest("aapl", provider="fixture")

    assert isinstance(record, QuoteSnapshotRecord)
    assert updated_record.id == record.id
    assert isinstance(latest, Quote)
    assert latest.last_price == Decimal("188.500000")
    assert latest.as_of.tzinfo is not None
    assert repository.get_latest("MSFT") is None
    assert repository.get_latest("AAPL", provider="other") is None
    assert db_session.scalar(select(func.count()).select_from(QuoteSnapshotRecord)) == 2


def test_ingestion_run_repository_tracks_success_and_failure_status(
    db_session: Session,
) -> None:
    repository = IngestionRunRepository(db_session)
    started_at = datetime(2026, 5, 8, 21, 0, tzinfo=UTC)
    run = repository.start(
        "fixture",
        IngestionRunType.MARKET_DATA_REFRESH.value,
        started_at=started_at,
        requested_symbols=("aapl", "msft"),
    )

    assert isinstance(run, IngestionRunRecord)
    assert run.status == IngestionRunStatus.RUNNING.value
    assert run.requested_symbols == ["AAPL", "MSFT"]
    assert run.succeeded_count == 0
    assert run.failed_count == 0

    succeeded = repository.mark_succeeded(
        run.id,
        finished_at=datetime(2026, 5, 8, 21, 5, tzinfo=UTC),
        succeeded_count=2,
    )

    assert succeeded.status == IngestionRunStatus.SUCCEEDED.value
    assert succeeded.finished_at is not None
    assert succeeded.succeeded_count == 2
    assert succeeded.failed_count == 0
    assert succeeded.error_message is None
    persisted_success = repository.get(run.id)
    assert persisted_success is not None
    assert persisted_success.status == IngestionRunStatus.SUCCEEDED.value

    failed_run = repository.start(
        "fixture",
        IngestionRunType.DAILY_CANDLES.value,
        started_at=datetime(2026, 5, 8, 22, 0, tzinfo=UTC),
    )
    failed = repository.mark_failed(
        failed_run.id,
        finished_at=datetime(2026, 5, 8, 22, 5, tzinfo=UTC),
        error_message="Provider timeout",
        succeeded_count=1,
        failed_count=3,
    )

    assert failed.status == IngestionRunStatus.FAILED.value
    assert failed.finished_at is not None
    assert failed.succeeded_count == 1
    assert failed.failed_count == 3
    assert failed.error_message == "Provider timeout"
    assert repository.get(999_999) is None

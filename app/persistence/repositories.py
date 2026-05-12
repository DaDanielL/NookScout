"""Repository classes for normalized market-data cache records."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.market_data.schemas import (
    DailyCandle,
    Quote,
    TickerReference,
    normalize_required_text,
    normalize_symbol,
)
from app.persistence.models import (
    DailyCandleRecord,
    IngestionRunRecord,
    IngestionRunStatus,
    QuoteSnapshotRecord,
    TickerRecord,
)


class PersistenceError(Exception):
    """Base exception for persistence-layer failures."""


class IngestionRunNotFoundError(PersistenceError):
    """Raised when an ingestion run update targets a missing run."""


class TickerRepository:
    """Persist and read normalized ticker reference data."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_reference(
        self,
        reference: TickerReference,
        *,
        retrieved_at: datetime,
    ) -> TickerRecord:
        """Insert or update current ticker reference data for one symbol/provider."""
        record = self._session.scalar(
            select(TickerRecord).where(
                TickerRecord.symbol == reference.symbol,
                TickerRecord.provider == reference.provider,
            )
        )
        if record is None:
            record = TickerRecord(symbol=reference.symbol, provider=reference.provider)
            self._session.add(record)

        record.name = reference.name
        record.asset_type = reference.asset_type.value
        record.primary_exchange = reference.primary_exchange
        record.currency = reference.currency
        record.is_active = reference.is_active
        record.is_otc = reference.is_otc
        record.market_cap = reference.market_cap
        record.average_daily_volume = reference.average_daily_volume
        record.as_of = reference.as_of
        record.data_recency = reference.data_recency.value
        record.retrieved_at = retrieved_at
        self._session.flush()
        return record

    def get_reference(
        self,
        symbol: str,
        *,
        provider: str | None = None,
    ) -> TickerReference | None:
        """Return cached ticker reference data, or None on cache miss."""
        statement = select(TickerRecord).where(TickerRecord.symbol == normalize_symbol(symbol))
        if provider is not None:
            statement = statement.where(
                TickerRecord.provider == _normalize_text(provider, "provider")
            )
        statement = statement.order_by(TickerRecord.retrieved_at.desc(), TickerRecord.id.desc())

        record = self._session.scalar(statement)
        if record is None:
            return None
        return _ticker_reference_from_record(record)


class DailyCandleRepository:
    """Persist and read normalized daily candles."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(
        self,
        candles: Sequence[DailyCandle],
        *,
        retrieved_at: datetime,
    ) -> int:
        """Insert or update normalized daily candles."""
        for candle in candles:
            record = self._session.scalar(
                select(DailyCandleRecord).where(
                    DailyCandleRecord.symbol == candle.symbol,
                    DailyCandleRecord.provider == candle.provider,
                    DailyCandleRecord.session_date == candle.session_date,
                    DailyCandleRecord.adjusted == candle.adjusted,
                )
            )
            if record is None:
                record = DailyCandleRecord(
                    symbol=candle.symbol,
                    provider=candle.provider,
                    session_date=candle.session_date,
                    adjusted=candle.adjusted,
                )
                self._session.add(record)

            record.timestamp = candle.timestamp
            record.open = candle.open
            record.high = candle.high
            record.low = candle.low
            record.close = candle.close
            record.volume = candle.volume
            record.vwap = candle.vwap
            record.trade_count = candle.trade_count
            record.data_recency = candle.data_recency.value
            record.retrieved_at = retrieved_at

        self._session.flush()
        return len(candles)

    def get_range(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        *,
        provider: str | None = None,
        adjusted: bool = True,
    ) -> tuple[DailyCandle, ...]:
        """Return ordered cached daily candles for an inclusive date range."""
        if start_date > end_date:
            return ()

        statement = (
            select(DailyCandleRecord)
            .where(
                DailyCandleRecord.symbol == normalize_symbol(symbol),
                DailyCandleRecord.session_date >= start_date,
                DailyCandleRecord.session_date <= end_date,
                DailyCandleRecord.adjusted == adjusted,
            )
            .order_by(DailyCandleRecord.session_date.asc(), DailyCandleRecord.id.asc())
        )
        if provider is not None:
            statement = statement.where(
                DailyCandleRecord.provider == _normalize_text(provider, "provider")
            )

        records = self._session.scalars(statement).all()
        return tuple(_daily_candle_from_record(record) for record in records)


class QuoteSnapshotRepository:
    """Persist and read normalized quote snapshots."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_snapshot(
        self,
        quote: Quote,
        *,
        retrieved_at: datetime,
    ) -> QuoteSnapshotRecord:
        """Insert or update a quote snapshot for one symbol/provider/as-of instant."""
        record = self._session.scalar(
            select(QuoteSnapshotRecord).where(
                QuoteSnapshotRecord.symbol == quote.symbol,
                QuoteSnapshotRecord.provider == quote.provider,
                QuoteSnapshotRecord.as_of == quote.as_of,
            )
        )
        if record is None:
            record = QuoteSnapshotRecord(
                symbol=quote.symbol,
                provider=quote.provider,
                as_of=quote.as_of,
            )
            self._session.add(record)

        record.last_price = quote.last_price
        record.bid_price = quote.bid_price
        record.ask_price = quote.ask_price
        record.day_open = quote.day_open
        record.day_high = quote.day_high
        record.day_low = quote.day_low
        record.previous_close = quote.previous_close
        record.day_volume = quote.day_volume
        record.data_recency = quote.data_recency.value
        record.retrieved_at = retrieved_at
        self._session.flush()
        return record

    def get_latest(
        self,
        symbol: str,
        *,
        provider: str | None = None,
    ) -> Quote | None:
        """Return the latest cached quote snapshot, or None on cache miss."""
        statement = select(QuoteSnapshotRecord).where(
            QuoteSnapshotRecord.symbol == normalize_symbol(symbol)
        )
        if provider is not None:
            statement = statement.where(
                QuoteSnapshotRecord.provider == _normalize_text(provider, "provider")
            )
        statement = statement.order_by(
            QuoteSnapshotRecord.as_of.desc(),
            QuoteSnapshotRecord.retrieved_at.desc(),
            QuoteSnapshotRecord.id.desc(),
        )

        record = self._session.scalar(statement)
        if record is None:
            return None
        return _quote_from_record(record)


class IngestionRunRepository:
    """Persist local market-data ingestion run metadata."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def start(
        self,
        provider: str,
        run_type: str,
        *,
        started_at: datetime,
        requested_symbols: Sequence[str] = (),
    ) -> IngestionRunRecord:
        """Start and persist a running ingestion record."""
        symbols = [normalize_symbol(symbol) for symbol in requested_symbols]
        record = IngestionRunRecord(
            provider=_normalize_text(provider, "provider"),
            run_type=_normalize_text(run_type, "run_type"),
            status=IngestionRunStatus.RUNNING.value,
            started_at=started_at,
            requested_symbols=symbols or None,
            succeeded_count=0,
            failed_count=0,
            error_message=None,
        )
        self._session.add(record)
        self._session.flush()
        return record

    def mark_succeeded(
        self,
        run_id: int,
        *,
        finished_at: datetime,
        succeeded_count: int,
        failed_count: int = 0,
    ) -> IngestionRunRecord:
        """Mark an ingestion run as succeeded."""
        _validate_non_negative_count(succeeded_count, "succeeded_count")
        _validate_non_negative_count(failed_count, "failed_count")
        record = self._require_run(run_id)
        record.status = IngestionRunStatus.SUCCEEDED.value
        record.finished_at = finished_at
        record.succeeded_count = succeeded_count
        record.failed_count = failed_count
        record.error_message = None
        self._session.flush()
        return record

    def mark_failed(
        self,
        run_id: int,
        *,
        finished_at: datetime,
        error_message: str,
        succeeded_count: int = 0,
        failed_count: int = 0,
    ) -> IngestionRunRecord:
        """Mark an ingestion run as failed with a preserved error message."""
        _validate_non_negative_count(succeeded_count, "succeeded_count")
        _validate_non_negative_count(failed_count, "failed_count")
        record = self._require_run(run_id)
        record.status = IngestionRunStatus.FAILED.value
        record.finished_at = finished_at
        record.succeeded_count = succeeded_count
        record.failed_count = failed_count
        record.error_message = _normalize_text(error_message, "error_message")
        self._session.flush()
        return record

    def get(self, run_id: int) -> IngestionRunRecord | None:
        """Return an ingestion run by id, or None when it does not exist."""
        return self._session.get(IngestionRunRecord, run_id)

    def _require_run(self, run_id: int) -> IngestionRunRecord:
        record = self.get(run_id)
        if record is None:
            raise IngestionRunNotFoundError(f"Ingestion run {run_id} was not found.")
        return record


def _ticker_reference_from_record(record: TickerRecord) -> TickerReference:
    return TickerReference.model_validate(
        {
            "symbol": record.symbol,
            "name": record.name,
            "asset_type": record.asset_type,
            "primary_exchange": record.primary_exchange,
            "currency": record.currency,
            "is_active": record.is_active,
            "is_otc": record.is_otc,
            "market_cap": record.market_cap,
            "average_daily_volume": record.average_daily_volume,
            "provider": record.provider,
            "as_of": record.as_of,
            "data_recency": record.data_recency,
        }
    )


def _daily_candle_from_record(record: DailyCandleRecord) -> DailyCandle:
    return DailyCandle.model_validate(
        {
            "symbol": record.symbol,
            "session_date": record.session_date,
            "timestamp": record.timestamp,
            "open": record.open,
            "high": record.high,
            "low": record.low,
            "close": record.close,
            "volume": record.volume,
            "vwap": record.vwap,
            "trade_count": record.trade_count,
            "adjusted": record.adjusted,
            "provider": record.provider,
            "data_recency": record.data_recency,
        }
    )


def _quote_from_record(record: QuoteSnapshotRecord) -> Quote:
    return Quote.model_validate(
        {
            "symbol": record.symbol,
            "last_price": record.last_price,
            "bid_price": record.bid_price,
            "ask_price": record.ask_price,
            "day_open": record.day_open,
            "day_high": record.day_high,
            "day_low": record.day_low,
            "previous_close": record.previous_close,
            "day_volume": record.day_volume,
            "as_of": record.as_of,
            "provider": record.provider,
            "data_recency": record.data_recency,
        }
    )


def _normalize_text(value: object, field_name: str) -> str:
    return normalize_required_text(value, field_name)


def _validate_non_negative_count(value: int, field_name: str) -> None:
    if value < 0:
        raise PersistenceError(f"{field_name} must be greater than or equal to 0")


__all__ = [
    "DailyCandleRepository",
    "IngestionRunNotFoundError",
    "IngestionRunRepository",
    "PersistenceError",
    "QuoteSnapshotRepository",
    "TickerRepository",
]

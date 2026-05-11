"""Market data schema validation tests."""

from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.market_data.schemas import (
    EXCHANGE_TIMEZONE,
    AssetType,
    DailyCandle,
    DataRecency,
    ProviderCapabilities,
    Quote,
    TickerReference,
)


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
        "currency": "usd",
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


def test_valid_quote_payload_normalizes_symbol_timestamp_and_recency() -> None:
    quote = Quote.model_validate(quote_payload(symbol="aapl"))

    assert quote.symbol == "AAPL"
    assert quote.last_price == Decimal("187.50")
    assert quote.data_recency is DataRecency.DELAYED
    assert quote.as_of.tzinfo == EXCHANGE_TIMEZONE
    assert quote.as_of.hour == 16


def test_valid_daily_candle_reference_and_capabilities_payloads() -> None:
    candle = DailyCandle.model_validate(candle_payload(symbol="spy"))
    reference = TickerReference.model_validate(reference_payload())
    capabilities = ProviderCapabilities.model_validate(
        {
            "provider": "fixture",
            "supports_quotes": True,
            "supports_snapshots": True,
            "supports_daily_candles": True,
            "supports_reference_data": True,
            "supports_adjusted_daily_candles": True,
            "supported_recency": ["delayed", "end_of_day"],
            "delayed_minutes": 15,
            "max_history_years": 5,
            "warnings": [" delayed data ", ""],
        }
    )

    assert candle.symbol == "SPY"
    assert candle.timestamp.tzinfo == EXCHANGE_TIMEZONE
    assert reference.asset_type is AssetType.STOCK
    assert reference.currency == "USD"
    assert capabilities.supported_recency == (DataRecency.DELAYED, DataRecency.END_OF_DAY)
    assert capabilities.warnings == ("delayed data",)


@pytest.mark.parametrize(
    ("input_symbol", "expected_symbol"),
    [
        ("aapl", "AAPL"),
        (" spy ", "SPY"),
        ("brk.b", "BRK.B"),
        ("brk-b", "BRK-B"),
    ],
)
def test_symbols_are_normalized_for_common_us_ticker_forms(
    input_symbol: str,
    expected_symbol: str,
) -> None:
    quote = Quote.model_validate(quote_payload(symbol=input_symbol))

    assert quote.symbol == expected_symbol


@pytest.mark.parametrize("symbol", ["", "BRK B", "AAPL$", "TOOLONGSYMBOL"])
def test_invalid_symbols_raise_validation_error(symbol: str) -> None:
    with pytest.raises(ValidationError):
        Quote.model_validate(quote_payload(symbol=symbol))


def test_missing_required_quote_fields_raise_validation_error() -> None:
    with pytest.raises(ValidationError):
        Quote.model_validate({"symbol": "AAPL", "provider": "fixture"})


def test_naive_candle_timestamp_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        DailyCandle.model_validate(candle_payload(timestamp=datetime(2026, 5, 8, 16, 0)))


def test_aware_candle_timestamp_normalizes_to_exchange_timezone() -> None:
    candle = DailyCandle.model_validate(
        candle_payload(timestamp=datetime(2026, 5, 8, 20, 0, tzinfo=UTC))
    )

    assert candle.timestamp.tzinfo == EXCHANGE_TIMEZONE
    assert candle.timestamp.hour == 16


def test_daily_candle_session_date_must_match_exchange_timestamp_date() -> None:
    with pytest.raises(ValidationError):
        DailyCandle.model_validate(
            candle_payload(
                session_date=date(2026, 5, 8),
                timestamp=datetime(2026, 5, 9, 20, 0, tzinfo=UTC),
            )
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"primary_exchange": "   "},
        {"provider": ""},
        {"currency": "US1"},
    ],
)
def test_invalid_reference_data_fields_raise_validation_error(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        TickerReference.model_validate(reference_payload(**overrides))


@pytest.mark.parametrize(
    "overrides",
    [
        {"high": "184.00"},
        {"low": "188.50"},
    ],
)
def test_invalid_candle_ohlc_relationships_raise_validation_error(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        DailyCandle.model_validate(candle_payload(**overrides))


@pytest.mark.parametrize(
    "model_payload",
    [
        lambda: Quote.model_validate(quote_payload(last_price="0")),
        lambda: DailyCandle.model_validate(candle_payload(volume=-1)),
        lambda: TickerReference.model_validate(reference_payload(average_daily_volume=-1)),
        lambda: ProviderCapabilities.model_validate(
            {
                "provider": "fixture",
                "supports_quotes": True,
                "supports_snapshots": True,
                "supports_daily_candles": True,
                "supports_reference_data": True,
                "supported_recency": ["end_of_day"],
                "delayed_minutes": 15,
            }
        ),
    ],
)
def test_invalid_numeric_and_delay_metadata_raise_validation_error(
    model_payload: Callable[[], object],
) -> None:
    with pytest.raises(ValidationError):
        model_payload()

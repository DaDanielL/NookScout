"""Predefined universe endpoint tests."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_market_data_provider
from app.core.settings import Settings
from app.main import create_app
from app.market_data.base import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    SymbolNotFoundError,
)
from app.market_data.schemas import (
    DailyCandle,
    DataRecency,
    ProviderCapabilities,
    Quote,
    TickerReference,
)
from tests.conftest import build_test_settings


class FakeApiMarketDataProvider:
    """Deterministic provider for predefined-universe API tests."""

    def __init__(
        self,
        *,
        references: dict[str, TickerReference | Exception] | None = None,
        quotes: dict[str, Quote | Exception] | None = None,
        candles: dict[str, Sequence[DailyCandle] | Exception] | None = None,
    ) -> None:
        self.references = references or {}
        self.quotes = quotes or {}
        self.candles = candles or {}
        self.calls: list[str] = []

    @property
    def provider_name(self) -> str:
        """Return fixture provider metadata."""
        return "fixture"

    def capabilities(self) -> ProviderCapabilities:
        """Return fixed provider capabilities."""
        return ProviderCapabilities(
            provider=self.provider_name,
            supports_quotes=True,
            supports_snapshots=True,
            supports_daily_candles=True,
            supports_reference_data=True,
            supported_recency=(DataRecency.DELAYED,),
        )

    def get_quote(self, symbol: str) -> Quote:
        """Return a normalized quote or configured exception."""
        self.calls.append(f"quote:{symbol}")
        value = self.quotes.get(symbol)
        if value is None:
            raise SymbolNotFoundError(f"{symbol} quote is missing")
        if isinstance(value, Exception):
            raise value
        return value

    def get_quotes(self, symbols: Sequence[str]) -> Sequence[Quote]:
        """Return normalized quotes for multiple symbols."""
        return tuple(self.get_quote(symbol) for symbol in symbols)

    def get_daily_candles(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[DailyCandle]:
        """Return normalized daily candles or configured exception."""
        self.calls.append(f"candles:{symbol}")
        value = self.candles.get(symbol)
        if value is None:
            raise SymbolNotFoundError(f"{symbol} candles are missing")
        if isinstance(value, Exception):
            raise value
        return tuple(value)

    def get_ticker_reference(self, symbol: str) -> TickerReference:
        """Return normalized reference data or configured exception."""
        self.calls.append(f"reference:{symbol}")
        value = self.references.get(symbol)
        if value is None:
            raise SymbolNotFoundError(f"{symbol} reference is missing")
        if isinstance(value, Exception):
            raise value
        return value


@contextmanager
def universe_client(
    settings: Settings,
    provider: FakeApiMarketDataProvider,
) -> Iterator[TestClient]:
    """Return a TestClient with the market-data provider overridden."""
    application = create_app(settings)
    application.dependency_overrides[get_market_data_provider] = lambda: provider
    with TestClient(application) as client:
        yield client
    application.dependency_overrides.clear()


def quote_payload(**overrides: object) -> dict[str, object]:
    """Return a valid normalized quote payload with optional overrides."""
    payload: dict[str, object] = {
        "symbol": "AAPL",
        "last_price": "187.50",
        "previous_close": "184.25",
        "as_of": datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
        "provider": "fixture",
        "data_recency": "delayed",
    }
    payload.update(overrides)
    return payload


def reference_payload(**overrides: object) -> dict[str, object]:
    """Return a valid normalized ticker reference payload with optional overrides."""
    symbol = str(overrides.get("symbol", "AAPL"))
    payload: dict[str, object] = {
        "symbol": symbol,
        "name": f"{symbol.upper()} Fixture Company",
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


def reference(**overrides: object) -> TickerReference:
    """Build normalized ticker reference data."""
    return TickerReference.model_validate(reference_payload(**overrides))


def settings_with_symbols(*symbols: str) -> Settings:
    """Build deterministic API test settings."""
    return build_test_settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        market_data_provider="massive",
        predefined_universe_symbols=symbols,
        liquidity_min_price=Decimal("5"),
        liquidity_min_average_daily_volume=1_000_000,
        liquidity_min_dollar_volume=Decimal("20000000"),
        liquidity_min_market_cap=Decimal("1000000000"),
        liquidity_allowed_exchanges=("XNAS", "XNYS", "NASDAQ", "NYSE"),
        liquidity_average_volume_lookback_days=90,
    )


def test_predefined_universe_endpoint_returns_results_and_applied_rules() -> None:
    provider = FakeApiMarketDataProvider(
        references={
            "AAPL": reference(symbol="AAPL"),
            "LOWP": reference(symbol="LOWP"),
        },
        quotes={
            "AAPL": quote(symbol="AAPL"),
            "LOWP": quote(symbol="LOWP", last_price="4.99"),
        },
    )

    with universe_client(settings_with_symbols("AAPL", "LOWP"), provider) as client:
        response = client.get("/universe/predefined")

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidate_symbols"] == ["AAPL", "LOWP"]
    assert payload["candidate_count"] == 2
    assert payload["eligible_count"] == 1
    assert payload["ineligible_count"] == 1
    assert payload["applied_rules"]["min_price"] == "5"
    assert payload["applied_rules"]["min_average_daily_volume"] == 1_000_000
    assert payload["applied_rules"]["min_dollar_volume"] == "20000000"
    assert payload["eligible"][0]["symbol"] == "AAPL"
    assert payload["eligible"][0]["provider"] == "fixture"
    assert payload["eligible"][0]["data_recency"] == "delayed"
    assert payload["eligible"][0]["price"] == "187.50"
    assert payload["ineligible"][0]["symbol"] == "LOWP"
    assert payload["ineligible"][0]["exclusion_reasons"] == ["low_price"]
    assert payload["evaluated_at"]
    assert payload["eligible"][0]["quote_as_of"]
    assert payload["eligible"][0]["reference_as_of"]

    forbidden_fragments = ("key", "token", "secret", "password", "database_url")
    for field_name in _field_names(payload):
        assert not any(fragment in field_name.lower() for fragment in forbidden_fragments)


def test_predefined_universe_endpoint_returns_empty_response_without_provider_calls() -> None:
    provider = FakeApiMarketDataProvider()

    with universe_client(settings_with_symbols(), provider) as client:
        response = client.get("/universe/predefined")

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidate_symbols"] == []
    assert payload["candidate_count"] == 0
    assert payload["eligible"] == []
    assert payload["ineligible"] == []
    assert provider.calls == []


@pytest.mark.parametrize(
    ("provider_error", "expected_status"),
    [
        (ProviderAuthenticationError("bad credentials"), 401),
        (ProviderRateLimitError("too many requests"), 429),
        (ProviderUnavailableError("provider down"), 503),
    ],
)
def test_predefined_universe_endpoint_maps_provider_errors_to_http_statuses(
    provider_error: Exception,
    expected_status: int,
) -> None:
    provider = FakeApiMarketDataProvider(references={"AAPL": provider_error})

    with universe_client(settings_with_symbols("AAPL"), provider) as client:
        response = client.get("/universe/predefined")

    assert response.status_code == expected_status


def _field_names(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _field_names(child)
    elif isinstance(value, list):
        for item in value:
            yield from _field_names(item)

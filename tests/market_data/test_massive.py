"""Massive market data adapter tests."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.core.settings import Settings
from app.market_data.base import (
    IncompleteMarketDataError,
    MarketDataProvider,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    SymbolNotFoundError,
)
from app.market_data.massive import MassiveMarketDataProvider
from app.market_data.schemas import AssetType, DataRecency

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "market_data"
BASE_URL = "https://api.polygon.io"
API_KEY = "fixture-secret-key"

RouteHandler = Callable[[httpx.Request], httpx.Response]
RouteValue = httpx.Response | RouteHandler


def load_fixture(name: str) -> dict[str, Any]:
    """Load a compact Massive-shaped JSON fixture."""
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def fixture_response(name: str) -> httpx.Response:
    """Return an HTTP response containing a fixture payload."""
    return httpx.Response(200, json=load_fixture(name))


def provider_with_routes(
    routes: Mapping[str, RouteValue],
    *,
    api_key: str | None = API_KEY,
    max_retries: int = 0,
) -> tuple[MassiveMarketDataProvider, list[httpx.Request]]:
    """Create a provider backed by MockTransport and capture outgoing requests."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        route = routes.get(request.url.path)
        if route is None:
            return httpx.Response(404, json={"status": "NOT_FOUND"})
        return route(request) if callable(route) else route

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = MassiveMarketDataProvider(
        api_key=api_key,
        base_url=BASE_URL,
        data_recency=DataRecency.DELAYED,
        timeout_seconds=5,
        max_retries=max_retries,
        client=client,
        sleep=lambda _: None,
    )
    return provider, requests


def test_provider_from_settings_satisfies_protocol_and_reports_capabilities(
    test_settings: Settings,
) -> None:
    settings = test_settings.model_copy(update={"massive_api_key": SecretStr(API_KEY)})
    provider = MassiveMarketDataProvider.from_settings(
        settings,
        client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(500))),
        sleep=lambda _: None,
    )

    capabilities = provider.capabilities()

    assert isinstance(provider, MarketDataProvider)
    assert provider.provider_name == "massive"
    assert capabilities.provider == "massive"
    assert capabilities.supports_quotes is True
    assert capabilities.supports_snapshots is True
    assert capabilities.supports_daily_candles is True
    assert capabilities.supports_reference_data is True
    assert capabilities.supports_adjusted_daily_candles is True
    assert capabilities.supported_recency == (DataRecency.DELAYED, DataRecency.END_OF_DAY)
    assert capabilities.delayed_minutes == 15


def test_get_quote_returns_normalized_quote_and_uses_authorization_header() -> None:
    provider, requests = provider_with_routes(
        {
            "/v2/snapshot/locale/us/markets/stocks/tickers/AAPL": fixture_response(
                "massive_single_snapshot_aapl.json"
            )
        }
    )

    quote = provider.get_quote("aapl")

    assert quote.symbol == "AAPL"
    assert quote.last_price == Decimal("191.25")
    assert quote.previous_close == Decimal("187.5")
    assert quote.day_open == Decimal("188.0")
    assert quote.day_high == Decimal("192.0")
    assert quote.day_low == Decimal("187.0")
    assert quote.day_volume == 65_000_000
    assert quote.as_of.hour == 16
    assert quote.provider == "massive"
    assert quote.data_recency is DataRecency.DELAYED

    request = requests[0]
    assert request.headers["authorization"] == f"Bearer {API_KEY}"
    assert "apiKey" not in request.url.query.decode()


def test_get_quotes_preserves_requested_order_and_uses_batch_query_params() -> None:
    provider, requests = provider_with_routes(
        {
            "/v2/snapshot/locale/us/markets/stocks/tickers": fixture_response(
                "massive_full_snapshot_batch.json"
            )
        }
    )

    quotes = provider.get_quotes(["msft", "aapl"])

    assert [quote.symbol for quote in quotes] == ["MSFT", "AAPL"]
    assert [quote.last_price for quote in quotes] == [Decimal("425.3"), Decimal("191.25")]

    query_params = requests[0].url.params
    assert query_params["tickers"] == "MSFT,AAPL"
    assert query_params["include_otc"] == "false"


def test_get_quotes_reports_missing_symbols() -> None:
    provider, _ = provider_with_routes(
        {
            "/v2/snapshot/locale/us/markets/stocks/tickers": fixture_response(
                "massive_full_snapshot_batch.json"
            )
        }
    )

    with pytest.raises(SymbolNotFoundError):
        provider.get_quotes(["AAPL", "TSLA"])


def test_get_daily_candles_returns_normalized_candles() -> None:
    provider, requests = provider_with_routes(
        {
            "/v2/aggs/ticker/AAPL/range/1/day/2026-05-07/2026-05-08": fixture_response(
                "massive_daily_aggs_aapl.json"
            )
        }
    )

    candles = provider.get_daily_candles("aapl", date(2026, 5, 7), date(2026, 5, 8))

    assert len(candles) == 2
    assert candles[0].symbol == "AAPL"
    assert candles[0].session_date == date(2026, 5, 7)
    assert candles[0].open == Decimal("185.0")
    assert candles[0].high == Decimal("190.0")
    assert candles[0].low == Decimal("184.0")
    assert candles[0].close == Decimal("189.0")
    assert candles[0].volume == 70_000_000
    assert candles[0].vwap == Decimal("187.5")
    assert candles[0].trade_count == 550_000
    assert candles[0].adjusted is True
    assert candles[0].timestamp.hour == 0

    query_params = requests[0].url.params
    assert query_params["adjusted"] == "true"
    assert query_params["sort"] == "asc"
    assert query_params["limit"] == "50000"


def test_get_daily_candles_returns_empty_tuple_for_valid_empty_results() -> None:
    provider, _ = provider_with_routes(
        {
            "/v2/aggs/ticker/AAPL/range/1/day/2026-05-07/2026-05-08": httpx.Response(
                200,
                json={
                    "status": "OK",
                    "ticker": "AAPL",
                    "adjusted": True,
                    "results": [],
                    "resultsCount": 0,
                },
            )
        }
    )

    assert provider.get_daily_candles("AAPL", date(2026, 5, 7), date(2026, 5, 8)) == ()


def test_get_ticker_reference_returns_normalized_reference_data() -> None:
    provider, _ = provider_with_routes(
        {"/v3/reference/tickers/AAPL": fixture_response("massive_ticker_overview_aapl.json")}
    )

    reference = provider.get_ticker_reference("aapl")

    assert reference.symbol == "AAPL"
    assert reference.name == "Apple Inc."
    assert reference.asset_type is AssetType.STOCK
    assert reference.primary_exchange == "XNAS"
    assert reference.currency == "USD"
    assert reference.is_active is True
    assert reference.is_otc is False
    assert reference.market_cap == Decimal("2900000000000")
    assert reference.average_daily_volume is None
    assert reference.as_of.hour == 16


def test_missing_api_key_raises_authentication_error_before_request() -> None:
    provider, requests = provider_with_routes(
        {
            "/v2/snapshot/locale/us/markets/stocks/tickers/AAPL": fixture_response(
                "massive_single_snapshot_aapl.json"
            )
        },
        api_key=None,
    )

    with pytest.raises(ProviderAuthenticationError):
        provider.get_quote("AAPL")

    assert requests == []


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (401, ProviderAuthenticationError),
        (403, ProviderAuthenticationError),
        (404, SymbolNotFoundError),
        (429, ProviderRateLimitError),
        (500, ProviderUnavailableError),
    ],
)
def test_http_status_codes_map_to_typed_provider_errors(
    status_code: int,
    expected_error: type[Exception],
) -> None:
    provider, _ = provider_with_routes(
        {
            "/v2/snapshot/locale/us/markets/stocks/tickers/AAPL": httpx.Response(
                status_code,
                json={"status": "ERROR"},
            )
        }
    )

    with pytest.raises(expected_error):
        provider.get_quote("AAPL")


def test_transient_server_errors_are_retried_before_success() -> None:
    call_count = 0

    def flaky_route(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(503, json={"status": "ERROR"})
        return fixture_response("massive_single_snapshot_aapl.json")

    provider, requests = provider_with_routes(
        {"/v2/snapshot/locale/us/markets/stocks/tickers/AAPL": flaky_route},
        max_retries=1,
    )

    quote = provider.get_quote("AAPL")

    assert quote.symbol == "AAPL"
    assert len(requests) == 2


def test_transport_failures_map_to_provider_unavailable_after_retry() -> None:
    def failing_route(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    provider, requests = provider_with_routes(
        {"/v2/snapshot/locale/us/markets/stocks/tickers/AAPL": failing_route},
        max_retries=1,
    )

    with pytest.raises(ProviderUnavailableError):
        provider.get_quote("AAPL")

    assert len(requests) == 2


def test_malformed_json_maps_to_incomplete_market_data() -> None:
    provider, _ = provider_with_routes(
        {
            "/v2/snapshot/locale/us/markets/stocks/tickers/AAPL": httpx.Response(
                200,
                content=b"{",
            )
        }
    )

    with pytest.raises(IncompleteMarketDataError):
        provider.get_quote("AAPL")


def test_unexpected_root_status_maps_to_incomplete_market_data() -> None:
    provider, _ = provider_with_routes(
        {
            "/v2/snapshot/locale/us/markets/stocks/tickers/AAPL": httpx.Response(
                200,
                json={"status": "ERROR", "ticker": {}},
            )
        }
    )

    with pytest.raises(IncompleteMarketDataError):
        provider.get_quote("AAPL")


def test_missing_required_provider_fields_map_to_incomplete_market_data() -> None:
    provider, _ = provider_with_routes(
        {
            "/v2/snapshot/locale/us/markets/stocks/tickers/AAPL": httpx.Response(
                200,
                json={"status": "OK", "ticker": {"ticker": "AAPL"}},
            )
        }
    )

    with pytest.raises(IncompleteMarketDataError):
        provider.get_quote("AAPL")


def test_logs_include_context_without_secrets_headers_or_full_urls(
    caplog: pytest.LogCaptureFixture,
) -> None:
    provider, _ = provider_with_routes(
        {
            "/v2/snapshot/locale/us/markets/stocks/tickers/AAPL": fixture_response(
                "massive_single_snapshot_aapl.json"
            )
        }
    )

    with caplog.at_level(logging.INFO, logger="app.market_data.massive"):
        provider.get_quote("AAPL")

    assert "operation=get_quote" in caplog.text
    assert "symbol_context=AAPL" in caplog.text
    assert "path=/v2/snapshot/locale/us/markets/stocks/tickers/AAPL" in caplog.text
    assert "status_code=200" in caplog.text
    assert API_KEY not in caplog.text
    assert "Authorization" not in caplog.text
    assert "apiKey" not in caplog.text
    assert BASE_URL not in caplog.text

"""Market data provider interface tests."""

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal

from app.market_data.base import (
    IncompleteMarketDataError,
    MarketDataError,
    MarketDataProvider,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    SymbolNotFoundError,
)
from app.market_data.schemas import (
    AssetType,
    DailyCandle,
    DataRecency,
    ProviderCapabilities,
    Quote,
    TickerReference,
)


class FakeMarketDataProvider:
    """Deterministic provider used to prove the normalized boundary."""

    @property
    def provider_name(self) -> str:
        """Return fixture provider metadata."""
        return "fixture"

    def capabilities(self) -> ProviderCapabilities:
        """Return fixed provider capabilities without live provider calls."""
        return ProviderCapabilities(
            provider=self.provider_name,
            supports_quotes=True,
            supports_snapshots=True,
            supports_daily_candles=True,
            supports_reference_data=True,
            supports_adjusted_daily_candles=True,
            supported_recency=(DataRecency.DELAYED, DataRecency.END_OF_DAY),
            delayed_minutes=15,
            max_history_years=5,
            warnings=("Fixture provider uses generated data.",),
        )

    def get_quote(self, symbol: str) -> Quote:
        """Return a normalized quote for one symbol."""
        return Quote(
            symbol=symbol,
            last_price=Decimal("187.50"),
            bid_price=Decimal("187.45"),
            ask_price=Decimal("187.55"),
            day_open=Decimal("185.00"),
            day_high=Decimal("188.00"),
            day_low=Decimal("184.50"),
            previous_close=Decimal("184.25"),
            day_volume=82_000_000,
            as_of=datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
            provider=self.provider_name,
            data_recency=DataRecency.DELAYED,
        )

    def get_quotes(self, symbols: Sequence[str]) -> Sequence[Quote]:
        """Return normalized quotes for multiple symbols."""
        return tuple(self.get_quote(symbol) for symbol in symbols)

    def get_daily_candles(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[DailyCandle]:
        """Return normalized daily candles for the requested range."""
        if start_date > end_date:
            return ()
        return (
            DailyCandle(
                symbol=symbol,
                session_date=start_date,
                timestamp=datetime(
                    start_date.year,
                    start_date.month,
                    start_date.day,
                    20,
                    0,
                    tzinfo=UTC,
                ),
                open=Decimal("185.00"),
                high=Decimal("188.00"),
                low=Decimal("184.50"),
                close=Decimal("187.50"),
                volume=82_000_000,
                vwap=Decimal("186.75"),
                trade_count=1_200_000,
                adjusted=True,
                provider=self.provider_name,
                data_recency=DataRecency.DELAYED,
            ),
        )

    def get_ticker_reference(self, symbol: str) -> TickerReference:
        """Return normalized ticker reference data."""
        return TickerReference(
            symbol=symbol,
            name=f"{symbol.upper()} Fixture Company",
            asset_type=AssetType.STOCK,
            primary_exchange="NASDAQ",
            currency="USD",
            is_active=True,
            is_otc=False,
            market_cap=Decimal("2900000000000"),
            average_daily_volume=60_000_000,
            provider=self.provider_name,
            as_of=datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
            data_recency=DataRecency.DELAYED,
        )


def test_fake_provider_satisfies_market_data_provider_protocol() -> None:
    provider: MarketDataProvider = FakeMarketDataProvider()

    assert isinstance(provider, MarketDataProvider)
    assert provider.provider_name == "fixture"


def test_fake_provider_returns_normalized_capabilities_quote_candles_and_reference() -> None:
    provider: MarketDataProvider = FakeMarketDataProvider()

    capabilities = provider.capabilities()
    quote = provider.get_quote("aapl")
    quotes = provider.get_quotes(["aapl", "brk.b"])
    candles = provider.get_daily_candles("spy", date(2026, 5, 8), date(2026, 5, 8))
    reference = provider.get_ticker_reference("spy")

    assert capabilities.supports_daily_candles is True
    assert capabilities.delayed_minutes == 15
    assert quote.symbol == "AAPL"
    assert [item.symbol for item in quotes] == ["AAPL", "BRK.B"]
    assert candles[0].symbol == "SPY"
    assert reference.symbol == "SPY"
    assert reference.provider == "fixture"


def test_market_data_errors_share_common_base_type() -> None:
    for error_type in (
        ProviderUnavailableError,
        ProviderAuthenticationError,
        ProviderRateLimitError,
        SymbolNotFoundError,
        IncompleteMarketDataError,
    ):
        assert issubclass(error_type, MarketDataError)

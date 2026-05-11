"""Provider-neutral market data adapter interface."""

from collections.abc import Sequence
from datetime import date
from typing import Protocol, runtime_checkable

from app.market_data.schemas import DailyCandle, ProviderCapabilities, Quote, TickerReference


class MarketDataError(Exception):
    """Base exception for market-data adapter failures."""


class ProviderUnavailableError(MarketDataError):
    """Raised when a provider cannot serve requests due to downtime or connectivity."""


class ProviderAuthenticationError(MarketDataError):
    """Raised when provider credentials are missing, invalid, or unauthorized."""


class ProviderRateLimitError(MarketDataError):
    """Raised when a provider rejects a request due to rate limits."""


class SymbolNotFoundError(MarketDataError):
    """Raised when a provider cannot resolve a requested ticker symbol."""


class IncompleteMarketDataError(MarketDataError):
    """Raised when a provider response lacks fields required by normalized schemas."""


@runtime_checkable
class MarketDataProvider(Protocol):
    """Provider boundary that returns only normalized market-data contracts."""

    @property
    def provider_name(self) -> str:
        """Return the provider identifier used in normalized payload metadata."""

    def capabilities(self) -> ProviderCapabilities:
        """Return provider-neutral capability metadata."""

    def get_quote(self, symbol: str) -> Quote:
        """Return a normalized quote or current snapshot for one symbol."""

    def get_quotes(self, symbols: Sequence[str]) -> Sequence[Quote]:
        """Return normalized quotes or snapshots for multiple symbols."""

    def get_daily_candles(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[DailyCandle]:
        """Return normalized daily candles for a symbol and inclusive date range."""

    def get_ticker_reference(self, symbol: str) -> TickerReference:
        """Return normalized reference data for one symbol."""


__all__ = [
    "IncompleteMarketDataError",
    "MarketDataError",
    "MarketDataProvider",
    "ProviderAuthenticationError",
    "ProviderRateLimitError",
    "ProviderUnavailableError",
    "SymbolNotFoundError",
]

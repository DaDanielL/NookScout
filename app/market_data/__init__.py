"""Provider-neutral market data contracts and adapters."""

from app.market_data.base import (
    IncompleteMarketDataError,
    MarketDataError,
    MarketDataProvider,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    SymbolNotFoundError,
)
from app.market_data.massive import MassiveMarketDataProvider
from app.market_data.schemas import (
    AssetType,
    DailyCandle,
    DataRecency,
    ProviderCapabilities,
    Quote,
    TickerReference,
)

__all__ = [
    "AssetType",
    "DailyCandle",
    "DataRecency",
    "IncompleteMarketDataError",
    "MarketDataError",
    "MarketDataProvider",
    "MassiveMarketDataProvider",
    "ProviderAuthenticationError",
    "ProviderCapabilities",
    "ProviderRateLimitError",
    "ProviderUnavailableError",
    "Quote",
    "SymbolNotFoundError",
    "TickerReference",
]

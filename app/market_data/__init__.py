"""Provider-neutral market data contracts and adapters."""

from typing import TYPE_CHECKING

from app.market_data.base import (
    IncompleteMarketDataError,
    MarketDataError,
    MarketDataProvider,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    SymbolNotFoundError,
)
from app.market_data.liquidity import (
    LiquidityEvaluation,
    LiquidityExclusionReason,
    LiquidityInputs,
    LiquidityRules,
    evaluate_liquidity,
)
from app.market_data.schemas import (
    AssetType,
    DailyCandle,
    DataRecency,
    ProviderCapabilities,
    Quote,
    TickerReference,
)
from app.market_data.universe import (
    UniverseEvaluation,
    UniverseSymbolResult,
    empty_universe_evaluation,
    evaluate_predefined_universe,
)

if TYPE_CHECKING:
    from app.market_data.massive import MassiveMarketDataProvider


def __getattr__(name: str) -> object:
    """Lazily expose provider-specific adapters without loading them during settings import."""
    if name == "MassiveMarketDataProvider":
        from app.market_data.massive import MassiveMarketDataProvider

        return MassiveMarketDataProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AssetType",
    "DailyCandle",
    "DataRecency",
    "IncompleteMarketDataError",
    "LiquidityEvaluation",
    "LiquidityExclusionReason",
    "LiquidityInputs",
    "LiquidityRules",
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
    "UniverseEvaluation",
    "UniverseSymbolResult",
    "empty_universe_evaluation",
    "evaluate_liquidity",
    "evaluate_predefined_universe",
]

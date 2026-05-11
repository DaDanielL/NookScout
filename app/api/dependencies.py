"""Shared FastAPI dependencies."""

from collections.abc import Iterator
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request

from app.core.settings import Settings, get_settings
from app.market_data.base import MarketDataProvider
from app.market_data.massive import MassiveMarketDataProvider


def get_app_settings(request: Request) -> Settings:
    """Return application-scoped settings for request handlers."""
    if hasattr(request.app.state, "settings"):
        return cast(Settings, request.app.state.settings)
    return get_settings()


def get_market_data_provider(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> Iterator[MarketDataProvider]:
    """Return the configured market-data provider for one request."""
    if settings.market_data_provider != "massive":
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported market data provider: {settings.market_data_provider}",
        )

    provider = MassiveMarketDataProvider.from_settings(settings)
    try:
        yield provider
    finally:
        provider.close()

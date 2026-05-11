"""Predefined universe endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_app_settings, get_market_data_provider
from app.api.schemas import UniverseResponse
from app.core.settings import Settings
from app.market_data.base import (
    MarketDataProvider,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.market_data.liquidity import LiquidityRules
from app.market_data.universe import empty_universe_evaluation, evaluate_predefined_universe

router = APIRouter(prefix="/universe", tags=["universe"])


@router.get("/predefined", response_model=UniverseResponse)
def predefined_universe(
    settings: Annotated[Settings, Depends(get_app_settings)],
    provider: Annotated[MarketDataProvider, Depends(get_market_data_provider)],
) -> UniverseResponse:
    """Return liquidity-filtered predefined universe results."""
    rules = LiquidityRules.from_settings(settings)
    evaluated_at = datetime.now(settings.timezone_info)

    if not settings.predefined_universe_symbols:
        return UniverseResponse.from_domain(
            empty_universe_evaluation(rules=rules, evaluated_at=evaluated_at)
        )

    try:
        evaluation = evaluate_predefined_universe(
            provider,
            settings.predefined_universe_symbols,
            rules,
            as_of=evaluated_at,
            average_volume_lookback_days=settings.liquidity_average_volume_lookback_days,
        )
    except ProviderAuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail="Market data provider authentication failed.",
        ) from exc
    except ProviderRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail="Market data provider rate limit reached.",
        ) from exc
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail="Market data provider is unavailable.") from exc

    return UniverseResponse.from_domain(evaluation)

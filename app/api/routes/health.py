"""Health check endpoint."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_app_settings
from app.api.schemas import HealthResponse
from app.core.settings import Settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Annotated[Settings, Depends(get_app_settings)]) -> HealthResponse:
    """Return non-secret operational health metadata."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.environment,
        market_data_provider=settings.market_data_provider,
        timezone=settings.timezone,
        checked_at=datetime.now(settings.timezone_info),
    )

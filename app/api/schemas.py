"""API response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Non-secret health response returned by the backend."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]
    app_name: str
    environment: str
    market_data_provider: str
    timezone: str
    checked_at: datetime

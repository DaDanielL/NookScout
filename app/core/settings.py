"""Typed application settings."""

from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "development", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Local-first NookScout settings loaded from env vars and optional `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        validate_default=True,
    )

    app_name: str = Field(default="NookScout", validation_alias="NOOKSCOUT_APP_NAME")
    environment: Environment = Field(default="local", validation_alias="NOOKSCOUT_ENVIRONMENT")
    log_level: LogLevel = Field(default="INFO", validation_alias="NOOKSCOUT_LOG_LEVEL")
    timezone: str = Field(default="America/New_York", validation_alias="NOOKSCOUT_TIMEZONE")
    database_url: str = Field(
        default="postgresql+psycopg://nookscout:nookscout@localhost:5432/nookscout",
        validation_alias="NOOKSCOUT_DATABASE_URL",
    )

    market_data_provider: str = Field(
        default="massive",
        validation_alias="NOOKSCOUT_MARKET_DATA_PROVIDER",
    )
    massive_api_key: SecretStr | None = Field(default=None, validation_alias="MASSIVE_API_KEY")
    massive_api_base_url: str = Field(
        default="https://api.polygon.io",
        validation_alias="MASSIVE_API_BASE_URL",
    )
    massive_stocks_plan: str = Field(default="starter", validation_alias="MASSIVE_STOCKS_PLAN")
    massive_data_recency: str = Field(default="delayed", validation_alias="MASSIVE_DATA_RECENCY")
    massive_request_timeout_seconds: int = Field(
        default=30,
        ge=1,
        validation_alias="MASSIVE_REQUEST_TIMEOUT_SECONDS",
    )
    massive_max_retries: int = Field(default=3, ge=0, validation_alias="MASSIVE_MAX_RETRIES")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        """Ensure configured timezone is available on this system."""
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown timezone: {value}") from exc
        return value

    @property
    def timezone_info(self) -> ZoneInfo:
        """Return the configured timezone as a `ZoneInfo` object."""
        return ZoneInfo(self.timezone)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings for application runtime."""
    return Settings()

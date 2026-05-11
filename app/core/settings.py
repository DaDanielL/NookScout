"""Typed application settings."""

from collections.abc import Iterable
from decimal import Decimal
from functools import lru_cache
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from app.market_data.schemas import normalize_symbol

Environment = Literal["local", "test", "development", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _parse_csv_values(value: object) -> tuple[str, ...]:
    """Parse string or sequence settings into normalized non-empty text values."""
    if value is None:
        return ()
    if isinstance(value, str):
        raw_values: Iterable[object] = value.split(",")
    elif isinstance(value, (list, tuple)):
        raw_values = value
    else:
        raise ValueError("value must be a comma-separated string or sequence")

    normalized: list[str] = []
    for raw_value in raw_values:
        if not isinstance(raw_value, str):
            raise ValueError("all values must be strings")
        text = raw_value.strip()
        if not text:
            continue
        normalized.append(text)
    return tuple(normalized)


def _dedupe_preserving_order(values: tuple[str, ...]) -> tuple[str, ...]:
    """Remove duplicates after normalization while preserving the user's order."""
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    return tuple(deduped)


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

    predefined_universe_symbols: Annotated[tuple[str, ...], NoDecode] = Field(
        default=(),
        validation_alias="NOOKSCOUT_PREDEFINED_UNIVERSE_SYMBOLS",
    )
    liquidity_min_price: Decimal = Field(
        default=Decimal("5"),
        gt=0,
        validation_alias="NOOKSCOUT_LIQUIDITY_MIN_PRICE",
    )
    liquidity_min_average_daily_volume: int = Field(
        default=1_000_000,
        gt=0,
        validation_alias="NOOKSCOUT_LIQUIDITY_MIN_AVERAGE_DAILY_VOLUME",
    )
    liquidity_min_dollar_volume: Decimal = Field(
        default=Decimal("20000000"),
        gt=0,
        validation_alias="NOOKSCOUT_LIQUIDITY_MIN_DOLLAR_VOLUME",
    )
    liquidity_min_market_cap: Decimal = Field(
        default=Decimal("1000000000"),
        gt=0,
        validation_alias="NOOKSCOUT_LIQUIDITY_MIN_MARKET_CAP",
    )
    liquidity_allowed_exchanges: Annotated[tuple[str, ...], NoDecode] = Field(
        default=("XNAS", "XNYS", "NASDAQ", "NYSE"),
        validation_alias="NOOKSCOUT_LIQUIDITY_ALLOWED_EXCHANGES",
    )
    liquidity_average_volume_lookback_days: int = Field(
        default=90,
        gt=0,
        validation_alias="NOOKSCOUT_LIQUIDITY_AVERAGE_VOLUME_LOOKBACK_DAYS",
    )

    @field_validator("predefined_universe_symbols", mode="before")
    @classmethod
    def parse_predefined_universe_symbols(cls, value: object) -> tuple[str, ...]:
        """Parse and normalize configured universe ticker symbols."""
        symbols = tuple(normalize_symbol(symbol) for symbol in _parse_csv_values(value))
        return _dedupe_preserving_order(symbols)

    @field_validator("liquidity_allowed_exchanges", mode="before")
    @classmethod
    def parse_liquidity_allowed_exchanges(cls, value: object) -> tuple[str, ...]:
        """Parse allowed exchange labels and MICs while preserving configured order."""
        exchanges = tuple(exchange.upper() for exchange in _parse_csv_values(value))
        return _dedupe_preserving_order(exchanges)

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

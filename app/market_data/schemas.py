"""Provider-neutral market data schemas."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

EXCHANGE_TIMEZONE = ZoneInfo("America/New_York")
_SYMBOL_PATTERN = re.compile(r"^[A-Z]{1,5}(?:[.-][A-Z]{1,2})?$")
_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")

PositiveDecimal = Annotated[Decimal, Field(gt=0)]
NonNegativeDecimal = Annotated[Decimal, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class DataRecency(StrEnum):
    """Provider-neutral market data freshness labels."""

    REAL_TIME = "real_time"
    DELAYED = "delayed"
    END_OF_DAY = "end_of_day"
    UNKNOWN = "unknown"


class AssetType(StrEnum):
    """Normalized security types needed by market-data consumers."""

    STOCK = "stock"
    ETF = "etf"
    ADR = "adr"
    FUND = "fund"
    UNKNOWN = "unknown"


class MarketDataModel(BaseModel):
    """Base model for immutable normalized market-data contracts."""

    model_config = ConfigDict(frozen=True)


def normalize_symbol(value: object) -> str:
    """Normalize and validate a U.S. equity-style ticker symbol."""
    if not isinstance(value, str):
        raise ValueError("symbol must be a string")

    symbol = value.strip().upper()
    if not symbol:
        raise ValueError("symbol is required")
    if len(symbol) > 10 or _SYMBOL_PATTERN.fullmatch(symbol) is None:
        raise ValueError("symbol must use letters and optional dot or hyphen share-class suffix")
    return symbol


def normalize_required_text(value: object, field_name: str) -> str:
    """Normalize a required string field while preserving provider-neutral wording."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def normalize_currency(value: object) -> str:
    """Normalize an ISO-style currency code."""
    currency = normalize_required_text(value, "currency").upper()
    if _CURRENCY_PATTERN.fullmatch(currency) is None:
        raise ValueError("currency must be a three-letter code")
    return currency


def normalize_exchange_timestamp(value: datetime) -> datetime:
    """Require an aware timestamp and convert it to the U.S. equities exchange timezone."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("market timestamps must be timezone-aware")
    return value.astimezone(EXCHANGE_TIMEZONE)


class Quote(MarketDataModel):
    """Normalized current price or snapshot data for one ticker."""

    symbol: str
    last_price: PositiveDecimal
    bid_price: PositiveDecimal | None = None
    ask_price: PositiveDecimal | None = None
    day_open: PositiveDecimal | None = None
    day_high: PositiveDecimal | None = None
    day_low: PositiveDecimal | None = None
    previous_close: PositiveDecimal
    day_volume: NonNegativeInt | None = None
    as_of: datetime
    provider: str
    data_recency: DataRecency = DataRecency.UNKNOWN

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> str:
        """Normalize supported ticker symbols."""
        return normalize_symbol(value)

    @field_validator("provider", mode="before")
    @classmethod
    def validate_provider(cls, value: object) -> str:
        """Require a provider label without exposing provider-specific payloads."""
        return normalize_required_text(value, "provider")

    @field_validator("as_of")
    @classmethod
    def validate_as_of(cls, value: datetime) -> datetime:
        """Normalize quote timestamps to exchange context."""
        return normalize_exchange_timestamp(value)

    @model_validator(mode="after")
    def validate_quote_relationships(self) -> Self:
        """Validate internal quote/snapshot price relationships when fields are present."""
        if (
            self.bid_price is not None
            and self.ask_price is not None
            and self.ask_price < self.bid_price
        ):
            raise ValueError("ask_price must be greater than or equal to bid_price")

        if self.day_high is not None and self.day_low is not None and self.day_low > self.day_high:
            raise ValueError("day_low must be less than or equal to day_high")

        if self.day_high is not None:
            intraday_prices = (self.last_price, self.day_open, self.day_low)
            if any(price is not None and price > self.day_high for price in intraday_prices):
                raise ValueError("day_high must be greater than or equal to intraday prices")

        if self.day_low is not None:
            intraday_prices = (self.last_price, self.day_open, self.day_high)
            if any(price is not None and price < self.day_low for price in intraday_prices):
                raise ValueError("day_low must be less than or equal to intraday prices")

        return self


class DailyCandle(MarketDataModel):
    """Normalized daily OHLCV candle.

    The timestamp is the exchange-local daily bar timestamp, typically the session close,
    normalized to America/New_York. It must agree with the exchange-local session date.
    """

    symbol: str
    session_date: date = Field(
        description="Exchange-local trading session date for this daily candle."
    )
    timestamp: datetime = Field(
        description="Timezone-aware daily bar timestamp normalized to America/New_York."
    )
    open: PositiveDecimal
    high: PositiveDecimal
    low: PositiveDecimal
    close: PositiveDecimal
    volume: NonNegativeInt
    vwap: PositiveDecimal | None = None
    trade_count: NonNegativeInt | None = None
    adjusted: bool = True
    provider: str
    data_recency: DataRecency = DataRecency.UNKNOWN

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> str:
        """Normalize supported ticker symbols."""
        return normalize_symbol(value)

    @field_validator("provider", mode="before")
    @classmethod
    def validate_provider(cls, value: object) -> str:
        """Require a provider label without exposing provider-specific payloads."""
        return normalize_required_text(value, "provider")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        """Normalize candle timestamps to exchange context."""
        return normalize_exchange_timestamp(value)

    @model_validator(mode="after")
    def validate_candle_relationships(self) -> Self:
        """Reject malformed candles before they reach indicators or scoring."""
        if self.timestamp.date() != self.session_date:
            raise ValueError("session_date must match timestamp date in exchange timezone")

        if self.high < max(self.open, self.low, self.close):
            raise ValueError("high must be greater than or equal to open, low, and close")
        if self.low > min(self.open, self.high, self.close):
            raise ValueError("low must be less than or equal to open, high, and close")
        return self


class TickerReference(MarketDataModel):
    """Normalized ticker metadata needed for liquidity filtering."""

    symbol: str
    name: str
    asset_type: AssetType
    primary_exchange: str
    currency: str
    is_active: bool
    is_otc: bool
    market_cap: NonNegativeDecimal | None
    average_daily_volume: NonNegativeInt | None
    provider: str
    as_of: datetime
    data_recency: DataRecency = DataRecency.UNKNOWN

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> str:
        """Normalize supported ticker symbols."""
        return normalize_symbol(value)

    @field_validator("name", "primary_exchange", "provider", mode="before")
    @classmethod
    def validate_required_text(cls, value: object, info: ValidationInfo) -> str:
        """Require key reference text fields."""
        return normalize_required_text(value, info.field_name or "field")

    @field_validator("currency", mode="before")
    @classmethod
    def validate_currency(cls, value: object) -> str:
        """Normalize currency metadata."""
        return normalize_currency(value)

    @field_validator("as_of")
    @classmethod
    def validate_as_of(cls, value: datetime) -> datetime:
        """Normalize reference-data timestamps to exchange context."""
        return normalize_exchange_timestamp(value)


class ProviderCapabilities(MarketDataModel):
    """Provider-neutral feature metadata for adapters and UI warnings."""

    provider: str
    supports_quotes: bool
    supports_snapshots: bool
    supports_daily_candles: bool
    supports_reference_data: bool
    supports_adjusted_daily_candles: bool = False
    supported_recency: tuple[DataRecency, ...] = (DataRecency.UNKNOWN,)
    delayed_minutes: NonNegativeInt | None = None
    max_history_years: PositiveInt | None = None
    warnings: tuple[str, ...] = ()

    @field_validator("provider", mode="before")
    @classmethod
    def validate_provider(cls, value: object) -> str:
        """Require a provider label without exposing provider-specific payloads."""
        return normalize_required_text(value, "provider")

    @field_validator("supported_recency")
    @classmethod
    def validate_supported_recency(cls, value: tuple[DataRecency, ...]) -> tuple[DataRecency, ...]:
        """Require at least one freshness label."""
        if not value:
            raise ValueError("supported_recency must include at least one value")
        return tuple(dict.fromkeys(value))

    @field_validator("warnings", mode="before")
    @classmethod
    def normalize_warnings(cls, value: object) -> tuple[str, ...]:
        """Normalize optional provider warning messages."""
        if value is None:
            return ()
        if isinstance(value, str):
            values: tuple[object, ...] = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("warnings must be a sequence of strings")
            values = tuple(value)

        warnings: list[str] = []
        for warning in values:
            if not isinstance(warning, str):
                raise ValueError("warnings must be strings")
            cleaned = warning.strip()
            if cleaned:
                warnings.append(cleaned)
        return tuple(warnings)

    @model_validator(mode="after")
    def validate_capability_metadata(self) -> Self:
        """Keep delayed-data metadata consistent with supported recency."""
        if self.delayed_minutes is not None and DataRecency.DELAYED not in self.supported_recency:
            raise ValueError("delayed_minutes requires delayed supported_recency")
        return self


__all__ = [
    "AssetType",
    "DailyCandle",
    "DataRecency",
    "EXCHANGE_TIMEZONE",
    "ProviderCapabilities",
    "Quote",
    "TickerReference",
    "normalize_exchange_timestamp",
    "normalize_symbol",
]

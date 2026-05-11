"""Provider-neutral liquidity rule evaluation."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import Field, field_validator

from app.market_data.schemas import (
    AssetType,
    DailyCandle,
    MarketDataModel,
    NonNegativeDecimal,
    PositiveDecimal,
    PositiveInt,
    Quote,
    TickerReference,
    normalize_currency,
    normalize_required_text,
    normalize_symbol,
)

if TYPE_CHECKING:
    from app.core.settings import Settings


class LiquidityExclusionReason(StrEnum):
    """Reasons a configured symbol is not eligible for Scout Mode setup discovery."""

    MISSING_REFERENCE_DATA = "missing_reference_data"
    INACTIVE_SECURITY = "inactive_security"
    OTC_SECURITY = "otc_security"
    UNSUPPORTED_ASSET_TYPE = "unsupported_asset_type"
    UNSUPPORTED_CURRENCY = "unsupported_currency"
    UNSUPPORTED_EXCHANGE = "unsupported_exchange"
    MISSING_PRICE = "missing_price"
    LOW_PRICE = "low_price"
    MISSING_AVERAGE_DAILY_VOLUME = "missing_average_daily_volume"
    LOW_AVERAGE_DAILY_VOLUME = "low_average_daily_volume"
    MISSING_MARKET_CAP = "missing_market_cap"
    LOW_MARKET_CAP = "low_market_cap"
    MISSING_DOLLAR_VOLUME = "missing_dollar_volume"
    LOW_DOLLAR_VOLUME = "low_dollar_volume"


class LiquidityRules(MarketDataModel):
    """Configurable liquidity thresholds for predefined universe eligibility."""

    min_price: PositiveDecimal
    min_average_daily_volume: PositiveInt
    min_dollar_volume: PositiveDecimal
    min_market_cap: PositiveDecimal
    allowed_exchanges: tuple[str, ...]
    average_volume_lookback_days: PositiveInt
    allowed_asset_types: tuple[AssetType, ...] = (AssetType.STOCK,)
    allowed_currencies: tuple[str, ...] = ("USD",)
    exclude_otc: bool = True

    @classmethod
    def from_settings(cls, settings: Settings) -> LiquidityRules:
        """Build liquidity rules from application settings."""
        return cls(
            min_price=settings.liquidity_min_price,
            min_average_daily_volume=settings.liquidity_min_average_daily_volume,
            min_dollar_volume=settings.liquidity_min_dollar_volume,
            min_market_cap=settings.liquidity_min_market_cap,
            allowed_exchanges=settings.liquidity_allowed_exchanges,
            average_volume_lookback_days=settings.liquidity_average_volume_lookback_days,
        )

    @field_validator("allowed_exchanges", mode="before")
    @classmethod
    def validate_allowed_exchanges(cls, value: object) -> tuple[str, ...]:
        """Normalize exchange labels and MICs used by reference-data contracts."""
        return _normalize_text_tuple(value, field_name="allowed_exchanges")

    @field_validator("allowed_currencies", mode="before")
    @classmethod
    def validate_allowed_currencies(cls, value: object) -> tuple[str, ...]:
        """Normalize currency codes used by reference-data contracts."""
        if isinstance(value, str):
            raw_values: tuple[object, ...] = (value,)
        elif isinstance(value, (list, tuple)):
            raw_values = tuple(value)
        else:
            raise ValueError("allowed_currencies must be a string or sequence")

        currencies: list[str] = []
        seen: set[str] = set()
        for raw_value in raw_values:
            currency = normalize_currency(raw_value)
            if currency not in seen:
                currencies.append(currency)
                seen.add(currency)
        return tuple(currencies)


class LiquidityInputs(MarketDataModel):
    """Normalized market-data inputs needed to evaluate liquidity rules."""

    symbol: str
    quote: Quote | None = None
    reference: TickerReference | None = None
    daily_candles: tuple[DailyCandle, ...] = Field(default=())

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> str:
        """Normalize supported ticker symbols."""
        return normalize_symbol(value)


class LiquidityEvaluation(MarketDataModel):
    """Result of applying liquidity rules to one configured symbol."""

    symbol: str
    is_eligible: bool
    exclusion_reasons: tuple[LiquidityExclusionReason, ...]
    price: PositiveDecimal | None
    average_daily_volume: NonNegativeDecimal | None
    dollar_volume: NonNegativeDecimal | None
    market_cap: NonNegativeDecimal | None
    exchange: str | None
    asset_type: AssetType | None
    currency: str | None
    is_active: bool | None
    is_otc: bool | None

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> str:
        """Normalize supported ticker symbols."""
        return normalize_symbol(value)


def evaluate_liquidity(
    inputs: LiquidityInputs,
    rules: LiquidityRules,
) -> LiquidityEvaluation:
    """Evaluate one symbol against provider-neutral liquidity rules."""
    reference = inputs.reference
    quote = inputs.quote
    price = quote.last_price if quote is not None else None
    average_daily_volume = _average_daily_volume(reference, inputs.daily_candles)
    dollar_volume = (
        price * average_daily_volume
        if price is not None and average_daily_volume is not None
        else None
    )

    exclusion_reasons: list[LiquidityExclusionReason] = []

    if reference is None:
        exclusion_reasons.append(LiquidityExclusionReason.MISSING_REFERENCE_DATA)
        market_cap = None
        exchange = None
        asset_type = None
        currency = None
        is_active = None
        is_otc = None
    else:
        market_cap = reference.market_cap
        exchange = reference.primary_exchange.upper()
        asset_type = reference.asset_type
        currency = reference.currency
        is_active = reference.is_active
        is_otc = reference.is_otc

        if not reference.is_active:
            exclusion_reasons.append(LiquidityExclusionReason.INACTIVE_SECURITY)
        if rules.exclude_otc and reference.is_otc:
            exclusion_reasons.append(LiquidityExclusionReason.OTC_SECURITY)
        if reference.asset_type not in rules.allowed_asset_types:
            exclusion_reasons.append(LiquidityExclusionReason.UNSUPPORTED_ASSET_TYPE)
        if reference.currency not in rules.allowed_currencies:
            exclusion_reasons.append(LiquidityExclusionReason.UNSUPPORTED_CURRENCY)
        if exchange not in rules.allowed_exchanges:
            exclusion_reasons.append(LiquidityExclusionReason.UNSUPPORTED_EXCHANGE)
        if reference.market_cap is None:
            exclusion_reasons.append(LiquidityExclusionReason.MISSING_MARKET_CAP)
        elif reference.market_cap < rules.min_market_cap:
            exclusion_reasons.append(LiquidityExclusionReason.LOW_MARKET_CAP)

    if price is None:
        exclusion_reasons.append(LiquidityExclusionReason.MISSING_PRICE)
    elif price < rules.min_price:
        exclusion_reasons.append(LiquidityExclusionReason.LOW_PRICE)

    if average_daily_volume is None:
        exclusion_reasons.append(LiquidityExclusionReason.MISSING_AVERAGE_DAILY_VOLUME)
    elif average_daily_volume < rules.min_average_daily_volume:
        exclusion_reasons.append(LiquidityExclusionReason.LOW_AVERAGE_DAILY_VOLUME)

    if dollar_volume is None:
        exclusion_reasons.append(LiquidityExclusionReason.MISSING_DOLLAR_VOLUME)
    elif dollar_volume < rules.min_dollar_volume:
        exclusion_reasons.append(LiquidityExclusionReason.LOW_DOLLAR_VOLUME)

    return LiquidityEvaluation(
        symbol=inputs.symbol,
        is_eligible=not exclusion_reasons,
        exclusion_reasons=tuple(exclusion_reasons),
        price=price,
        average_daily_volume=average_daily_volume,
        dollar_volume=dollar_volume,
        market_cap=market_cap,
        exchange=exchange,
        asset_type=asset_type,
        currency=currency,
        is_active=is_active,
        is_otc=is_otc,
    )


def _average_daily_volume(
    reference: TickerReference | None,
    daily_candles: tuple[DailyCandle, ...],
) -> Decimal | None:
    if reference is not None and reference.average_daily_volume is not None:
        return Decimal(reference.average_daily_volume)
    if not daily_candles:
        return None
    total_volume = sum(candle.volume for candle in daily_candles)
    return Decimal(total_volume) / Decimal(len(daily_candles))


def _normalize_text_tuple(value: object, *, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        raw_values: tuple[object, ...] = (value,)
    elif isinstance(value, (list, tuple)):
        raw_values = tuple(value)
    else:
        raise ValueError(f"{field_name} must be a string or sequence")

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in raw_values:
        text = normalize_required_text(raw_value, field_name).upper()
        if text not in seen:
            normalized.append(text)
            seen.add(text)
    return tuple(normalized)


__all__ = [
    "LiquidityEvaluation",
    "LiquidityExclusionReason",
    "LiquidityInputs",
    "LiquidityRules",
    "evaluate_liquidity",
]

"""API response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer

from app.market_data.liquidity import LiquidityRules
from app.market_data.universe import UniverseEvaluation, UniverseSymbolResult


class HealthResponse(BaseModel):
    """Non-secret health response returned by the backend."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]
    app_name: str
    environment: str
    market_data_provider: str
    timezone: str
    checked_at: datetime


class LiquidityRulesResponse(BaseModel):
    """Liquidity rules applied to a predefined universe response."""

    model_config = ConfigDict(frozen=True)

    min_price: Decimal
    min_average_daily_volume: int
    min_dollar_volume: Decimal
    min_market_cap: Decimal
    allowed_exchanges: tuple[str, ...]
    average_volume_lookback_days: int
    allowed_asset_types: tuple[str, ...]
    allowed_currencies: tuple[str, ...]
    exclude_otc: bool

    @classmethod
    def from_domain(cls, rules: LiquidityRules) -> "LiquidityRulesResponse":
        """Build an API response DTO from domain liquidity rules."""
        return cls(
            min_price=rules.min_price,
            min_average_daily_volume=rules.min_average_daily_volume,
            min_dollar_volume=rules.min_dollar_volume,
            min_market_cap=rules.min_market_cap,
            allowed_exchanges=rules.allowed_exchanges,
            average_volume_lookback_days=rules.average_volume_lookback_days,
            allowed_asset_types=tuple(asset_type.value for asset_type in rules.allowed_asset_types),
            allowed_currencies=rules.allowed_currencies,
            exclude_otc=rules.exclude_otc,
        )

    @field_serializer("min_price", "min_dollar_volume", "min_market_cap")
    def serialize_decimal(self, value: Decimal) -> str:
        """Serialize Decimal thresholds as stable JSON strings."""
        return str(value)


class UniverseSymbolResponse(BaseModel):
    """API response DTO for one predefined universe symbol."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    name: str | None
    is_eligible: bool
    exclusion_reasons: tuple[str, ...]
    price: Decimal | None
    average_daily_volume: Decimal | None
    dollar_volume: Decimal | None
    market_cap: Decimal | None
    exchange: str | None
    asset_type: str | None
    currency: str | None
    provider: str | None
    data_recency: str
    quote_as_of: datetime | None
    reference_as_of: datetime | None

    @classmethod
    def from_domain(cls, result: UniverseSymbolResult) -> "UniverseSymbolResponse":
        """Build an API response DTO from a universe symbol result."""
        return cls(
            symbol=result.symbol,
            name=result.name,
            is_eligible=result.is_eligible,
            exclusion_reasons=tuple(reason.value for reason in result.exclusion_reasons),
            price=result.price,
            average_daily_volume=result.average_daily_volume,
            dollar_volume=result.dollar_volume,
            market_cap=result.market_cap,
            exchange=result.exchange,
            asset_type=result.asset_type.value if result.asset_type is not None else None,
            currency=result.currency,
            provider=result.provider,
            data_recency=result.data_recency.value,
            quote_as_of=result.quote_as_of,
            reference_as_of=result.reference_as_of,
        )

    @field_serializer("price", "average_daily_volume", "dollar_volume", "market_cap")
    def serialize_optional_decimal(self, value: Decimal | None) -> str | None:
        """Serialize optional Decimal values as stable JSON strings."""
        if value is None:
            return None
        return str(value)


class UniverseResponse(BaseModel):
    """API response DTO for predefined universe evaluation."""

    model_config = ConfigDict(frozen=True)

    evaluated_at: datetime
    applied_rules: LiquidityRulesResponse
    candidate_symbols: tuple[str, ...]
    candidate_count: int
    eligible_count: int
    ineligible_count: int
    eligible: tuple[UniverseSymbolResponse, ...]
    ineligible: tuple[UniverseSymbolResponse, ...]

    @classmethod
    def from_domain(cls, evaluation: UniverseEvaluation) -> "UniverseResponse":
        """Build an API response DTO from a universe evaluation."""
        return cls(
            evaluated_at=evaluation.evaluated_at,
            applied_rules=LiquidityRulesResponse.from_domain(evaluation.rules),
            candidate_symbols=evaluation.candidate_symbols,
            candidate_count=evaluation.candidate_count,
            eligible_count=evaluation.eligible_count,
            ineligible_count=evaluation.ineligible_count,
            eligible=tuple(
                UniverseSymbolResponse.from_domain(item) for item in evaluation.eligible
            ),
            ineligible=tuple(
                UniverseSymbolResponse.from_domain(item) for item in evaluation.ineligible
            ),
        )

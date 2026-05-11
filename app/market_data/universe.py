"""Provider-neutral predefined universe evaluation."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta

from pydantic import field_validator

from app.market_data.base import (
    IncompleteMarketDataError,
    MarketDataProvider,
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
    MarketDataModel,
    NonNegativeDecimal,
    NonNegativeInt,
    PositiveDecimal,
    Quote,
    TickerReference,
    normalize_exchange_timestamp,
    normalize_symbol,
)


class UniverseSymbolResult(MarketDataModel):
    """Predefined universe result for one configured symbol."""

    symbol: str
    name: str | None
    is_eligible: bool
    exclusion_reasons: tuple[LiquidityExclusionReason, ...]
    price: PositiveDecimal | None
    average_daily_volume: NonNegativeDecimal | None
    dollar_volume: NonNegativeDecimal | None
    market_cap: NonNegativeDecimal | None
    exchange: str | None
    asset_type: AssetType | None
    currency: str | None
    provider: str | None
    data_recency: DataRecency = DataRecency.UNKNOWN
    quote_as_of: datetime | None = None
    reference_as_of: datetime | None = None

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> str:
        """Normalize supported ticker symbols."""
        return normalize_symbol(value)


class UniverseEvaluation(MarketDataModel):
    """Eligible and ineligible results for a configured predefined universe."""

    evaluated_at: datetime
    rules: LiquidityRules
    candidate_symbols: tuple[str, ...]
    candidate_count: NonNegativeInt
    eligible_count: NonNegativeInt
    ineligible_count: NonNegativeInt
    eligible: tuple[UniverseSymbolResult, ...]
    ineligible: tuple[UniverseSymbolResult, ...]

    @classmethod
    def from_results(
        cls,
        *,
        evaluated_at: datetime,
        rules: LiquidityRules,
        candidate_symbols: tuple[str, ...],
        eligible: Sequence[UniverseSymbolResult],
        ineligible: Sequence[UniverseSymbolResult],
    ) -> UniverseEvaluation:
        """Build an evaluation with count metadata derived from result collections."""
        return cls(
            evaluated_at=normalize_exchange_timestamp(evaluated_at),
            rules=rules,
            candidate_symbols=candidate_symbols,
            candidate_count=len(candidate_symbols),
            eligible_count=len(eligible),
            ineligible_count=len(ineligible),
            eligible=tuple(eligible),
            ineligible=tuple(ineligible),
        )


def evaluate_predefined_universe(
    provider: MarketDataProvider,
    symbols: Iterable[str],
    rules: LiquidityRules,
    *,
    as_of: datetime,
    average_volume_lookback_days: int,
) -> UniverseEvaluation:
    """Evaluate configured symbols against liquidity rules using normalized provider data."""
    evaluated_at = normalize_exchange_timestamp(as_of)
    candidate_symbols = _normalize_symbols(symbols)
    eligible: list[UniverseSymbolResult] = []
    ineligible: list[UniverseSymbolResult] = []

    for symbol in candidate_symbols:
        reference: TickerReference | None
        quote: Quote | None = None
        daily_candles: tuple[DailyCandle, ...] = ()

        try:
            reference = provider.get_ticker_reference(symbol)
        except (SymbolNotFoundError, IncompleteMarketDataError):
            reference = None
            evaluation = evaluate_liquidity(
                LiquidityInputs(symbol=symbol, quote=None, reference=None),
                rules,
            )
            result = _symbol_result(
                symbol=symbol,
                provider_name=provider.provider_name,
                evaluation=evaluation,
                reference=reference,
                quote=quote,
            )
            ineligible.append(result)
            continue

        try:
            quote = provider.get_quote(symbol)
        except (SymbolNotFoundError, IncompleteMarketDataError):
            quote = None

        if reference.average_daily_volume is None:
            daily_candles = _get_fallback_daily_candles(
                provider=provider,
                symbol=symbol,
                evaluated_at=evaluated_at,
                average_volume_lookback_days=average_volume_lookback_days,
            )

        evaluation = evaluate_liquidity(
            LiquidityInputs(
                symbol=symbol,
                quote=quote,
                reference=reference,
                daily_candles=daily_candles,
            ),
            rules,
        )
        result = _symbol_result(
            symbol=symbol,
            provider_name=provider.provider_name,
            evaluation=evaluation,
            reference=reference,
            quote=quote,
        )
        if result.is_eligible:
            eligible.append(result)
        else:
            ineligible.append(result)

    return UniverseEvaluation.from_results(
        evaluated_at=evaluated_at,
        rules=rules,
        candidate_symbols=candidate_symbols,
        eligible=eligible,
        ineligible=ineligible,
    )


def empty_universe_evaluation(
    *,
    rules: LiquidityRules,
    evaluated_at: datetime,
) -> UniverseEvaluation:
    """Return an empty predefined-universe evaluation without provider calls."""
    return UniverseEvaluation.from_results(
        evaluated_at=evaluated_at,
        rules=rules,
        candidate_symbols=(),
        eligible=(),
        ineligible=(),
    )


def _normalize_symbols(symbols: Iterable[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_symbol in symbols:
        symbol = normalize_symbol(raw_symbol)
        if symbol not in seen:
            normalized.append(symbol)
            seen.add(symbol)
    return tuple(normalized)


def _get_fallback_daily_candles(
    *,
    provider: MarketDataProvider,
    symbol: str,
    evaluated_at: datetime,
    average_volume_lookback_days: int,
) -> tuple[DailyCandle, ...]:
    end_date = evaluated_at.date()
    start_date = end_date - timedelta(days=max(average_volume_lookback_days - 1, 0))
    try:
        return tuple(provider.get_daily_candles(symbol, start_date, end_date))
    except (SymbolNotFoundError, IncompleteMarketDataError):
        return ()


def _symbol_result(
    *,
    symbol: str,
    provider_name: str,
    evaluation: LiquidityEvaluation,
    reference: TickerReference | None,
    quote: Quote | None,
) -> UniverseSymbolResult:
    provider = _first_non_empty_text(
        quote.provider if quote is not None else None,
        reference.provider if reference is not None else None,
        provider_name,
    )
    return UniverseSymbolResult(
        symbol=symbol,
        name=reference.name if reference is not None else None,
        is_eligible=evaluation.is_eligible,
        exclusion_reasons=evaluation.exclusion_reasons,
        price=evaluation.price,
        average_daily_volume=evaluation.average_daily_volume,
        dollar_volume=evaluation.dollar_volume,
        market_cap=evaluation.market_cap,
        exchange=evaluation.exchange,
        asset_type=evaluation.asset_type,
        currency=evaluation.currency,
        provider=provider,
        data_recency=_data_recency(reference=reference, quote=quote),
        quote_as_of=quote.as_of if quote is not None else None,
        reference_as_of=reference.as_of if reference is not None else None,
    )


def _data_recency(
    *,
    reference: TickerReference | None,
    quote: Quote | None,
) -> DataRecency:
    if quote is not None:
        return quote.data_recency
    if reference is not None:
        return reference.data_recency
    return DataRecency.UNKNOWN


def _first_non_empty_text(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


__all__ = [
    "UniverseEvaluation",
    "UniverseSymbolResult",
    "empty_universe_evaluation",
    "evaluate_predefined_universe",
]

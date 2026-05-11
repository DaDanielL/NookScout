"""Predefined universe service tests."""

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.market_data.base import MarketDataProvider, ProviderUnavailableError, SymbolNotFoundError
from app.market_data.liquidity import LiquidityExclusionReason, LiquidityRules
from app.market_data.schemas import (
    DailyCandle,
    DataRecency,
    ProviderCapabilities,
    Quote,
    TickerReference,
)
from app.market_data.universe import UniverseEvaluation, evaluate_predefined_universe


class FakeUniverseProvider:
    """Deterministic provider for predefined-universe service tests."""

    def __init__(
        self,
        *,
        references: dict[str, TickerReference | Exception],
        quotes: dict[str, Quote | Exception],
        candles: dict[str, Sequence[DailyCandle] | Exception] | None = None,
    ) -> None:
        self.references = references
        self.quotes = quotes
        self.candles = candles or {}
        self.reference_calls: list[str] = []
        self.quote_calls: list[str] = []
        self.candle_calls: list[str] = []

    @property
    def provider_name(self) -> str:
        """Return fixture provider metadata."""
        return "fixture"

    def capabilities(self) -> ProviderCapabilities:
        """Return fixed provider capabilities without live provider calls."""
        return ProviderCapabilities(
            provider=self.provider_name,
            supports_quotes=True,
            supports_snapshots=True,
            supports_daily_candles=True,
            supports_reference_data=True,
            supported_recency=(DataRecency.DELAYED,),
        )

    def get_quote(self, symbol: str) -> Quote:
        """Return a normalized quote or configured exception."""
        self.quote_calls.append(symbol)
        value = self.quotes.get(symbol)
        if value is None:
            raise SymbolNotFoundError(f"{symbol} quote is missing")
        if isinstance(value, Exception):
            raise value
        return value

    def get_quotes(self, symbols: Sequence[str]) -> Sequence[Quote]:
        """Return normalized quotes for multiple symbols."""
        return tuple(self.get_quote(symbol) for symbol in symbols)

    def get_daily_candles(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[DailyCandle]:
        """Return normalized daily candles or configured exception."""
        self.candle_calls.append(symbol)
        value = self.candles.get(symbol)
        if value is None:
            raise SymbolNotFoundError(f"{symbol} candles are missing")
        if isinstance(value, Exception):
            raise value
        return tuple(value)

    def get_ticker_reference(self, symbol: str) -> TickerReference:
        """Return normalized reference data or configured exception."""
        self.reference_calls.append(symbol)
        value = self.references.get(symbol)
        if value is None:
            raise SymbolNotFoundError(f"{symbol} reference is missing")
        if isinstance(value, Exception):
            raise value
        return value


def quote_payload(**overrides: object) -> dict[str, object]:
    """Return a valid normalized quote payload with optional overrides."""
    payload: dict[str, object] = {
        "symbol": "AAPL",
        "last_price": "187.50",
        "previous_close": "184.25",
        "as_of": datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
        "provider": "fixture",
        "data_recency": "delayed",
    }
    payload.update(overrides)
    return payload


def reference_payload(**overrides: object) -> dict[str, object]:
    """Return a valid normalized ticker reference payload with optional overrides."""
    symbol = str(overrides.get("symbol", "AAPL"))
    payload: dict[str, object] = {
        "symbol": symbol,
        "name": f"{symbol.upper()} Fixture Company",
        "asset_type": "stock",
        "primary_exchange": "NASDAQ",
        "currency": "USD",
        "is_active": True,
        "is_otc": False,
        "market_cap": "2900000000000",
        "average_daily_volume": 60_000_000,
        "provider": "fixture",
        "as_of": datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
        "data_recency": "delayed",
    }
    payload.update(overrides)
    return payload


def candle_payload(**overrides: object) -> dict[str, object]:
    """Return a valid normalized daily candle payload with optional overrides."""
    payload: dict[str, object] = {
        "symbol": "AAPL",
        "session_date": date(2026, 5, 8),
        "timestamp": datetime(2026, 5, 8, 20, 0, tzinfo=UTC),
        "open": "185.00",
        "high": "188.00",
        "low": "184.50",
        "close": "187.50",
        "volume": 1_500_000,
        "provider": "fixture",
        "data_recency": "delayed",
    }
    payload.update(overrides)
    return payload


def quote(**overrides: object) -> Quote:
    """Build a normalized quote."""
    return Quote.model_validate(quote_payload(**overrides))


def reference(**overrides: object) -> TickerReference:
    """Build normalized ticker reference data."""
    return TickerReference.model_validate(reference_payload(**overrides))


def candle(**overrides: object) -> DailyCandle:
    """Build a normalized daily candle."""
    return DailyCandle.model_validate(candle_payload(**overrides))


def rules(**overrides: object) -> LiquidityRules:
    """Build default liquidity rules with optional overrides."""
    payload: dict[str, object] = {
        "min_price": Decimal("5"),
        "min_average_daily_volume": 1_000_000,
        "min_dollar_volume": Decimal("20000000"),
        "min_market_cap": Decimal("1000000000"),
        "allowed_exchanges": ("XNAS", "XNYS", "NASDAQ", "NYSE"),
        "average_volume_lookback_days": 90,
    }
    payload.update(overrides)
    return LiquidityRules.model_validate(payload)


def evaluate(provider: MarketDataProvider, symbols: Sequence[str]) -> UniverseEvaluation:
    """Evaluate symbols with deterministic timestamp and default rules."""
    return evaluate_predefined_universe(
        provider,
        symbols,
        rules(),
        as_of=datetime(2026, 5, 11, 14, 30, tzinfo=UTC),
        average_volume_lookback_days=90,
    )


def test_universe_returns_eligible_and_ineligible_symbols_with_reasons() -> None:
    provider = FakeUniverseProvider(
        references={
            "AAPL": reference(symbol="AAPL"),
            "LOWP": reference(symbol="LOWP"),
        },
        quotes={
            "AAPL": quote(symbol="AAPL"),
            "LOWP": quote(symbol="LOWP", last_price="4.99"),
        },
    )

    evaluation = evaluate(provider, ("AAPL", "LOWP"))

    assert [result.symbol for result in evaluation.eligible] == ["AAPL"]
    assert [result.symbol for result in evaluation.ineligible] == ["LOWP"]
    assert evaluation.candidate_count == 2
    assert evaluation.eligible_count == 1
    assert evaluation.ineligible_count == 1
    assert evaluation.ineligible[0].exclusion_reasons == (LiquidityExclusionReason.LOW_PRICE,)
    assert provider.candle_calls == []


def test_universe_preserves_configured_order_and_deduplicates_symbols() -> None:
    provider = FakeUniverseProvider(
        references={
            "MSFT": reference(symbol="MSFT"),
            "AAPL": reference(symbol="AAPL"),
            "LOWP": reference(symbol="LOWP"),
        },
        quotes={
            "MSFT": quote(symbol="MSFT"),
            "AAPL": quote(symbol="AAPL"),
            "LOWP": quote(symbol="LOWP", last_price="4.99"),
        },
    )

    evaluation = evaluate(provider, ("msft", "AAPL", "MSFT", "lowp"))

    assert evaluation.candidate_symbols == ("MSFT", "AAPL", "LOWP")
    assert provider.reference_calls == ["MSFT", "AAPL", "LOWP"]
    assert provider.quote_calls == ["MSFT", "AAPL", "LOWP"]


def test_universe_service_reports_liquidity_exclusion_outcomes() -> None:
    provider = FakeUniverseProvider(
        references={
            "LOWV": reference(symbol="LOWV", average_daily_volume=500_000),
            "LOWD": reference(symbol="LOWD", average_daily_volume=1_500_000),
            "LOWP": reference(symbol="LOWP"),
            "OTC": reference(symbol="OTC", is_otc=True),
        },
        quotes={
            "LOWV": quote(symbol="LOWV"),
            "LOWD": quote(symbol="LOWD", last_price="10"),
            "LOWP": quote(symbol="LOWP", last_price="4.99"),
            "OTC": quote(symbol="OTC"),
        },
    )

    evaluation = evaluate(provider, ("LOWV", "LOWD", "LOWP", "OTC", "MISS"))
    reasons_by_symbol = {
        result.symbol: result.exclusion_reasons for result in evaluation.ineligible
    }

    assert reasons_by_symbol["LOWV"] == (LiquidityExclusionReason.LOW_AVERAGE_DAILY_VOLUME,)
    assert reasons_by_symbol["LOWD"] == (LiquidityExclusionReason.LOW_DOLLAR_VOLUME,)
    assert reasons_by_symbol["LOWP"] == (LiquidityExclusionReason.LOW_PRICE,)
    assert LiquidityExclusionReason.OTC_SECURITY in reasons_by_symbol["OTC"]
    assert LiquidityExclusionReason.MISSING_REFERENCE_DATA in reasons_by_symbol["MISS"]


def test_universe_service_uses_candle_fallback_when_reference_volume_is_missing() -> None:
    provider = FakeUniverseProvider(
        references={"AAPL": reference(symbol="AAPL", average_daily_volume=None)},
        quotes={"AAPL": quote(symbol="AAPL")},
        candles={
            "AAPL": (
                candle(symbol="AAPL", volume=1_200_000),
                candle(
                    symbol="AAPL",
                    volume=1_800_000,
                    session_date=date(2026, 5, 7),
                    timestamp=datetime(2026, 5, 7, 20, 0, tzinfo=UTC),
                ),
            )
        },
    )

    evaluation = evaluate(provider, ("AAPL",))

    assert provider.candle_calls == ["AAPL"]
    assert evaluation.eligible[0].average_daily_volume == Decimal("1500000")


def test_universe_service_does_not_swallow_systemic_provider_errors() -> None:
    provider = FakeUniverseProvider(
        references={"AAPL": ProviderUnavailableError("provider down")},
        quotes={},
    )

    with pytest.raises(ProviderUnavailableError):
        evaluate(provider, ("AAPL",))

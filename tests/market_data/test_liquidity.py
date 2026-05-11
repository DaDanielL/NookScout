"""Liquidity rule evaluation tests."""

from datetime import UTC, date, datetime
from decimal import Decimal

from app.market_data.liquidity import (
    LiquidityEvaluation,
    LiquidityExclusionReason,
    LiquidityInputs,
    LiquidityRules,
    evaluate_liquidity,
)
from app.market_data.schemas import AssetType, DailyCandle, Quote, TickerReference


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
    payload: dict[str, object] = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
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


def evaluate(
    *,
    quote_value: Quote | None = None,
    reference_value: TickerReference | None = None,
    candles: tuple[DailyCandle, ...] = (),
    rule_set: LiquidityRules | None = None,
) -> LiquidityEvaluation:
    """Evaluate a symbol with default valid inputs."""
    return evaluate_liquidity(
        LiquidityInputs(
            symbol="AAPL",
            quote=quote() if quote_value is None else quote_value,
            reference=reference() if reference_value is None else reference_value,
            daily_candles=candles,
        ),
        rule_set or rules(),
    )


def test_liquid_stock_is_eligible() -> None:
    evaluation = evaluate()

    assert evaluation.is_eligible is True
    assert evaluation.exclusion_reasons == ()
    assert evaluation.price == Decimal("187.50")
    assert evaluation.average_daily_volume == Decimal("60000000")
    assert evaluation.dollar_volume == Decimal("11250000000")


def test_low_price_is_excluded() -> None:
    evaluation = evaluate(quote_value=quote(last_price="4.99"))

    assert evaluation.is_eligible is False
    assert evaluation.exclusion_reasons == (LiquidityExclusionReason.LOW_PRICE,)


def test_low_average_volume_from_reference_is_excluded() -> None:
    evaluation = evaluate(reference_value=reference(average_daily_volume=500_000))

    assert evaluation.is_eligible is False
    assert evaluation.exclusion_reasons == (LiquidityExclusionReason.LOW_AVERAGE_DAILY_VOLUME,)


def test_average_volume_falls_back_to_daily_candles() -> None:
    evaluation = evaluate(
        reference_value=reference(average_daily_volume=None),
        candles=(
            candle(volume=1_200_000),
            candle(
                volume=1_800_000,
                session_date=date(2026, 5, 7),
                timestamp=datetime(2026, 5, 7, 20, 0, tzinfo=UTC),
            ),
        ),
    )

    assert evaluation.is_eligible is True
    assert evaluation.average_daily_volume == Decimal("1500000")


def test_low_dollar_volume_is_excluded() -> None:
    evaluation = evaluate(
        quote_value=quote(last_price="10"),
        reference_value=reference(average_daily_volume=1_500_000),
    )

    assert evaluation.is_eligible is False
    assert evaluation.exclusion_reasons == (LiquidityExclusionReason.LOW_DOLLAR_VOLUME,)


def test_missing_reference_data_is_excluded() -> None:
    evaluation = evaluate_liquidity(
        LiquidityInputs(symbol="AAPL", quote=quote(), reference=None, daily_candles=(candle(),)),
        rules(),
    )

    assert evaluation.is_eligible is False
    assert LiquidityExclusionReason.MISSING_REFERENCE_DATA in evaluation.exclusion_reasons
    assert evaluation.market_cap is None


def test_otc_security_is_excluded() -> None:
    evaluation = evaluate(reference_value=reference(is_otc=True))

    assert evaluation.is_eligible is False
    assert LiquidityExclusionReason.OTC_SECURITY in evaluation.exclusion_reasons


def test_unsupported_exchange_and_inactive_security_are_excluded() -> None:
    evaluation = evaluate(reference_value=reference(is_active=False, primary_exchange="OTCM"))

    assert evaluation.is_eligible is False
    assert LiquidityExclusionReason.INACTIVE_SECURITY in evaluation.exclusion_reasons
    assert LiquidityExclusionReason.UNSUPPORTED_EXCHANGE in evaluation.exclusion_reasons


def test_unsupported_asset_type_and_currency_are_excluded() -> None:
    evaluation = evaluate(
        reference_value=reference(asset_type=AssetType.ETF, currency="CAD"),
    )

    assert evaluation.is_eligible is False
    assert LiquidityExclusionReason.UNSUPPORTED_ASSET_TYPE in evaluation.exclusion_reasons
    assert LiquidityExclusionReason.UNSUPPORTED_CURRENCY in evaluation.exclusion_reasons

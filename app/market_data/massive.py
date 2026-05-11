"""Massive/Polygon market data provider adapter."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from pydantic import SecretStr, ValidationError

from app.core.settings import Settings
from app.market_data.base import (
    IncompleteMarketDataError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    SymbolNotFoundError,
)
from app.market_data.schemas import (
    EXCHANGE_TIMEZONE,
    AssetType,
    DailyCandle,
    DataRecency,
    ProviderCapabilities,
    Quote,
    TickerReference,
    normalize_symbol,
)

logger = logging.getLogger(__name__)

JsonMapping = Mapping[str, Any]
SleepCallable = Callable[[float], None]

_TRANSIENT_STATUS_CODES = frozenset(range(500, 600))
_ROOT_OK_STATUSES = {"OK", "DELAYED"}


class MassiveMarketDataProvider:
    """Market data adapter that normalizes Massive/Polygon REST payloads."""

    def __init__(
        self,
        *,
        api_key: str | SecretStr | None,
        base_url: str,
        data_recency: DataRecency | str,
        timeout_seconds: int,
        max_retries: int,
        client: httpx.Client | None = None,
        sleep: SleepCallable | None = None,
    ) -> None:
        self._api_key = _extract_api_key(api_key)
        self._base_url = base_url.rstrip("/")
        self._data_recency = _coerce_data_recency(data_recency)
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(0, max_retries)
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._owns_client = client is None
        self._sleep = sleep or time.sleep

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        client: httpx.Client | None = None,
        sleep: SleepCallable | None = None,
    ) -> MassiveMarketDataProvider:
        """Create a provider from application settings without opening connections."""
        return cls(
            api_key=settings.massive_api_key,
            base_url=settings.massive_api_base_url,
            data_recency=settings.massive_data_recency,
            timeout_seconds=settings.massive_request_timeout_seconds,
            max_retries=settings.massive_max_retries,
            client=client,
            sleep=sleep,
        )

    @property
    def provider_name(self) -> str:
        """Return the provider identifier used in normalized payload metadata."""
        return "massive"

    def close(self) -> None:
        """Close the internally owned HTTP client."""
        if self._owns_client:
            self._client.close()

    def capabilities(self) -> ProviderCapabilities:
        """Return provider-neutral capability metadata for Massive Stocks Starter."""
        return ProviderCapabilities(
            provider=self.provider_name,
            supports_quotes=True,
            supports_snapshots=True,
            supports_daily_candles=True,
            supports_reference_data=True,
            supports_adjusted_daily_candles=True,
            supported_recency=(DataRecency.DELAYED, DataRecency.END_OF_DAY),
            delayed_minutes=15,
            max_history_years=5,
            warnings=(
                "Massive Stocks Starter data is delayed and should not be presented as real-time.",
                "Provider-derived data is normalized before use by NookScout domain code.",
            ),
        )

    def get_quote(self, symbol: str) -> Quote:
        """Return a normalized quote or current snapshot for one symbol."""
        normalized_symbol = _normalize_symbol_for_provider(symbol)
        payload = self._request_json(
            operation="get_quote",
            path=f"/v2/snapshot/locale/us/markets/stocks/tickers/{normalized_symbol}",
            params=None,
            symbol_context=normalized_symbol,
        )
        snapshot = _require_mapping(payload, "ticker", "snapshot")
        return self._snapshot_to_quote(snapshot, operation="get_quote")

    def get_quotes(self, symbols: Sequence[str]) -> tuple[Quote, ...]:
        """Return normalized quotes or snapshots for multiple symbols."""
        normalized_symbols = tuple(_normalize_symbol_for_provider(symbol) for symbol in symbols)
        if not normalized_symbols:
            return ()

        payload = self._request_json(
            operation="get_quotes",
            path="/v2/snapshot/locale/us/markets/stocks/tickers",
            params={"tickers": ",".join(normalized_symbols), "include_otc": "false"},
            symbol_context=f"{len(normalized_symbols)} symbols",
        )
        raw_snapshots = payload.get("tickers")
        if not isinstance(raw_snapshots, list):
            raise IncompleteMarketDataError("Massive batch snapshot response is missing tickers.")

        snapshots_by_symbol: dict[str, JsonMapping] = {}
        for raw_snapshot in raw_snapshots:
            if not isinstance(raw_snapshot, Mapping):
                raise IncompleteMarketDataError(
                    "Massive batch snapshot contains a malformed ticker."
                )
            snapshot_symbol = _require_text(raw_snapshot, "ticker", "snapshot ticker")
            snapshots_by_symbol[normalize_symbol(snapshot_symbol)] = raw_snapshot

        missing_symbols = [
            symbol for symbol in normalized_symbols if symbol not in snapshots_by_symbol
        ]
        if missing_symbols:
            missing = ", ".join(missing_symbols)
            raise SymbolNotFoundError(f"Massive snapshot response did not include: {missing}.")

        return tuple(
            self._snapshot_to_quote(snapshots_by_symbol[symbol], operation="get_quotes")
            for symbol in normalized_symbols
        )

    def get_daily_candles(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> tuple[DailyCandle, ...]:
        """Return normalized daily candles for a symbol and inclusive date range."""
        if start_date > end_date:
            raise ValueError("start_date must be on or before end_date")

        normalized_symbol = _normalize_symbol_for_provider(symbol)
        payload = self._request_json(
            operation="get_daily_candles",
            path=(
                f"/v2/aggs/ticker/{normalized_symbol}/range/1/day/"
                f"{start_date.isoformat()}/{end_date.isoformat()}"
            ),
            params={"adjusted": "true", "sort": "asc", "limit": "50000"},
            symbol_context=normalized_symbol,
        )
        raw_results = payload.get("results", ())
        if raw_results is None:
            return ()
        if not isinstance(raw_results, list):
            raise IncompleteMarketDataError("Massive aggregate response has malformed results.")

        adjusted = bool(payload.get("adjusted", True))
        candles: list[DailyCandle] = []
        for raw_bar in raw_results:
            if not isinstance(raw_bar, Mapping):
                raise IncompleteMarketDataError(
                    "Massive aggregate response contains a malformed bar."
                )
            candles.append(self._bar_to_daily_candle(normalized_symbol, raw_bar, adjusted=adjusted))
        return tuple(candles)

    def get_ticker_reference(self, symbol: str) -> TickerReference:
        """Return normalized reference data for one symbol."""
        normalized_symbol = _normalize_symbol_for_provider(symbol)
        payload = self._request_json(
            operation="get_ticker_reference",
            path=f"/v3/reference/tickers/{normalized_symbol}",
            params=None,
            symbol_context=normalized_symbol,
        )
        result = _require_mapping(payload, "results", "ticker reference")
        return self._reference_to_ticker_reference(result)

    def _request_json(
        self,
        *,
        operation: str,
        path: str,
        params: Mapping[str, str] | None,
        symbol_context: str,
    ) -> JsonMapping:
        """Request JSON from Massive while logging only redacted request context."""
        if self._api_key is None:
            raise ProviderAuthenticationError("Massive API key is not configured.")

        headers = {"Authorization": f"Bearer {self._api_key}"}
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 2):
            try:
                response = self._client.get(
                    self._absolute_url(path),
                    params=params,
                    headers=headers,
                    timeout=self._timeout_seconds,
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                self._log_request(
                    operation=operation,
                    symbol_context=symbol_context,
                    path=path,
                    attempt=attempt,
                    status_code=None,
                )
                if attempt <= self._max_retries:
                    self._sleep(_backoff_seconds(attempt))
                    continue
                raise ProviderUnavailableError(
                    f"Massive provider unavailable during {operation}."
                ) from exc

            status_code = response.status_code
            self._log_request(
                operation=operation,
                symbol_context=symbol_context,
                path=path,
                attempt=attempt,
                status_code=status_code,
            )

            if status_code in _TRANSIENT_STATUS_CODES:
                if attempt <= self._max_retries:
                    self._sleep(_backoff_seconds(attempt))
                    continue
                raise ProviderUnavailableError(
                    f"Massive provider returned {status_code} during {operation}."
                )
            if status_code in {401, 403}:
                raise ProviderAuthenticationError(
                    f"Massive rejected credentials during {operation}."
                )
            if status_code == 404:
                raise SymbolNotFoundError(
                    f"Massive could not find symbol data for {symbol_context}."
                )
            if status_code == 429:
                raise ProviderRateLimitError(f"Massive rate limit reached during {operation}.")
            if status_code >= 400:
                raise ProviderUnavailableError(
                    f"Massive provider returned {status_code} during {operation}."
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise IncompleteMarketDataError(
                    f"Massive returned malformed JSON during {operation}."
                ) from exc
            if not isinstance(payload, Mapping):
                raise IncompleteMarketDataError(
                    f"Massive returned a malformed response during {operation}."
                )
            _validate_root_status(payload, operation=operation)
            return payload

        raise ProviderUnavailableError(
            f"Massive provider unavailable during {operation}."
        ) from last_error

    def _snapshot_to_quote(self, snapshot: JsonMapping, *, operation: str) -> Quote:
        try:
            symbol = _require_text(snapshot, "ticker", "snapshot ticker")
            day = _optional_mapping(snapshot, "day")
            previous_day = _require_mapping(snapshot, "prevDay", "previous day snapshot")
            minute = _optional_mapping(snapshot, "min")
            last_trade = _optional_mapping(snapshot, "lastTrade")

            last_price = _first_decimal(
                _optional_value(last_trade, "p"),
                _optional_value(minute, "c"),
                _optional_value(day, "c"),
                field_name="last_price",
            )
            previous_close = _required_decimal(previous_day, "c", "previous_close")
            quote = Quote(
                symbol=symbol,
                last_price=last_price,
                day_open=_optional_decimal(day, "o"),
                day_high=_optional_decimal(day, "h"),
                day_low=_optional_decimal(day, "l"),
                previous_close=previous_close,
                day_volume=_optional_int(day, "v"),
                as_of=_snapshot_timestamp(snapshot, last_trade=last_trade, minute=minute, day=day),
                provider=self.provider_name,
                data_recency=self._data_recency,
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise IncompleteMarketDataError(
                f"Massive snapshot response is incomplete during {operation}."
            ) from exc

        return quote

    def _bar_to_daily_candle(
        self,
        symbol: str,
        raw_bar: JsonMapping,
        *,
        adjusted: bool,
    ) -> DailyCandle:
        try:
            timestamp = _timestamp_to_datetime(_require_value(raw_bar, "t", "aggregate timestamp"))
            exchange_timestamp = timestamp.astimezone(EXCHANGE_TIMEZONE)
            candle = DailyCandle(
                symbol=symbol,
                session_date=exchange_timestamp.date(),
                timestamp=timestamp,
                open=_required_decimal(raw_bar, "o", "open"),
                high=_required_decimal(raw_bar, "h", "high"),
                low=_required_decimal(raw_bar, "l", "low"),
                close=_required_decimal(raw_bar, "c", "close"),
                volume=_required_int(raw_bar, "v", "volume"),
                vwap=_optional_decimal(raw_bar, "vw"),
                trade_count=_optional_int(raw_bar, "n"),
                adjusted=adjusted,
                provider=self.provider_name,
                data_recency=self._data_recency,
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise IncompleteMarketDataError("Massive aggregate bar is incomplete.") from exc

        return candle

    def _reference_to_ticker_reference(self, result: JsonMapping) -> TickerReference:
        try:
            symbol = _require_text(result, "ticker", "reference ticker")
            market = _optional_text(result, "market")
            ticker_reference = TickerReference(
                symbol=symbol,
                name=_require_text(result, "name", "company name"),
                asset_type=_asset_type_from_massive(
                    market=market,
                    raw_type=_optional_text(result, "type"),
                ),
                primary_exchange=_require_text(result, "primary_exchange", "primary exchange"),
                currency=_currency_from_massive(result),
                is_active=_required_bool(result, "active", "active"),
                is_otc=(market or "").lower() == "otc",
                market_cap=_optional_decimal(result, "market_cap"),
                average_daily_volume=None,
                provider=self.provider_name,
                as_of=_reference_as_of(result),
                data_recency=self._data_recency,
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise IncompleteMarketDataError(
                "Massive ticker reference response is incomplete."
            ) from exc

        return ticker_reference

    def _absolute_url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def _log_request(
        self,
        *,
        operation: str,
        symbol_context: str,
        path: str,
        attempt: int,
        status_code: int | None,
    ) -> None:
        logger.info(
            "Massive request operation=%s symbol_context=%s path=%s attempt=%s status_code=%s",
            operation,
            symbol_context,
            path,
            attempt,
            status_code,
        )


def _extract_api_key(api_key: str | SecretStr | None) -> str | None:
    if api_key is None:
        return None
    value = api_key.get_secret_value() if isinstance(api_key, SecretStr) else api_key
    cleaned = value.strip()
    return cleaned or None


def _coerce_data_recency(value: DataRecency | str) -> DataRecency:
    try:
        return value if isinstance(value, DataRecency) else DataRecency(value)
    except ValueError:
        return DataRecency.UNKNOWN


def _normalize_symbol_for_provider(symbol: str) -> str:
    try:
        return normalize_symbol(symbol)
    except ValueError as exc:
        raise SymbolNotFoundError("Invalid ticker symbol.") from exc


def _validate_root_status(payload: JsonMapping, *, operation: str) -> None:
    raw_status = payload.get("status")
    if raw_status is None:
        return
    if not isinstance(raw_status, str) or raw_status.upper() not in _ROOT_OK_STATUSES:
        raise IncompleteMarketDataError(f"Massive returned unexpected status during {operation}.")


def _backoff_seconds(attempt: int) -> float:
    return min(0.25 * 2 ** (attempt - 1), 2.0)


def _require_mapping(payload: JsonMapping, key: str, field_name: str) -> JsonMapping:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} is required")
    return value


def _optional_mapping(payload: JsonMapping, key: str) -> JsonMapping:
    value = payload.get(key)
    return value if isinstance(value, Mapping) else {}


def _require_value(payload: JsonMapping, key: str, field_name: str) -> Any:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"{field_name} is required")
    return value


def _optional_value(payload: JsonMapping, key: str) -> Any:
    return payload.get(key)


def _require_text(payload: JsonMapping, key: str, field_name: str) -> str:
    value = _require_value(payload, key, field_name)
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _optional_text(payload: JsonMapping, key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    text = value.strip()
    return text or None


def _required_bool(payload: JsonMapping, key: str, field_name: str) -> bool:
    value = _require_value(payload, key, field_name)
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a bool")
    return value


def _first_decimal(*values: Any, field_name: str) -> Decimal:
    for value in values:
        if value is not None:
            return _to_decimal(value, field_name)
    raise ValueError(f"{field_name} is required")


def _required_decimal(payload: JsonMapping, key: str, field_name: str) -> Decimal:
    return _to_decimal(_require_value(payload, key, field_name), field_name)


def _optional_decimal(payload: JsonMapping, key: str) -> Decimal | None:
    value = payload.get(key)
    if value is None:
        return None
    return _to_decimal(value, key)


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc


def _required_int(payload: JsonMapping, key: str, field_name: str) -> int:
    value = _require_value(payload, key, field_name)
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    return value


def _optional_int(payload: JsonMapping, key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _snapshot_timestamp(
    snapshot: JsonMapping,
    *,
    last_trade: JsonMapping,
    minute: JsonMapping,
    day: JsonMapping,
) -> datetime:
    for payload, key in (
        (last_trade, "t"),
        (minute, "t"),
        (day, "t"),
        (snapshot, "updated"),
    ):
        value = payload.get(key)
        if value is not None:
            return _timestamp_to_datetime(value)
    raise ValueError("snapshot timestamp is required")


def _timestamp_to_datetime(value: Any) -> datetime:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("timestamp must be numeric")

    absolute_value = abs(value)
    if absolute_value >= 10**17:
        seconds = value / 1_000_000_000
    elif absolute_value >= 10**14:
        seconds = value / 1_000_000
    elif absolute_value >= 10**11:
        seconds = value / 1_000
    else:
        seconds = float(value)
    return datetime.fromtimestamp(seconds, tz=UTC)


def _asset_type_from_massive(*, market: str | None, raw_type: str | None) -> AssetType:
    normalized_type = (raw_type or "").strip().lower()
    if normalized_type in {"cs", "stock", "common stock", "common_stock"}:
        return AssetType.STOCK
    if normalized_type in {"etf"}:
        return AssetType.ETF
    if normalized_type in {"adr", "adrc", "adrp"}:
        return AssetType.ADR
    if normalized_type in {"fund", "mutual fund", "mutual_fund"}:
        return AssetType.FUND
    if raw_type is None and (market or "").lower() == "stocks":
        return AssetType.STOCK
    return AssetType.UNKNOWN


def _currency_from_massive(result: JsonMapping) -> str:
    raw_value = result.get("currency_name") or result.get("currency")
    if raw_value is None:
        raise ValueError("currency is required")
    if not isinstance(raw_value, str):
        raise ValueError("currency must be a string")

    normalized = raw_value.strip().lower()
    common_currencies = {
        "usd": "USD",
        "us dollar": "USD",
        "u.s. dollar": "USD",
        "united states dollar": "USD",
    }
    return common_currencies.get(normalized, normalized.upper())


def _reference_as_of(result: JsonMapping) -> datetime:
    raw_value = result.get("last_updated_utc")
    if raw_value is None:
        return datetime.now(UTC)
    if not isinstance(raw_value, str):
        raise ValueError("last_updated_utc must be a string")

    cleaned = raw_value.strip()
    if cleaned.endswith("Z"):
        cleaned = f"{cleaned[:-1]}+00:00"
    timestamp = datetime.fromisoformat(cleaned)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp


__all__ = ["MassiveMarketDataProvider"]

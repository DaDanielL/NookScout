"""Typed setup scoring contracts and version metadata."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import Field, ValidationInfo, field_validator, model_validator

from app.indicators.signals import RelativeStrengthSnapshot, SupportResistanceSnapshot
from app.indicators.technical import TechnicalIndicatorSnapshot
from app.market_data.schemas import (
    MarketDataModel,
    PositiveDecimal,
    normalize_required_text,
    normalize_symbol,
)

SCORING_VERSION = "scoring-v1"
RATIONALE_VERSION = "rationale-v1"


class SetupLabel(StrEnum):
    """Supported setup and wait-state labels for MVP scoring outputs."""

    BULLISH_BREAKOUT = "bullish_breakout"
    BULLISH_PULLBACK = "bullish_pullback"
    BULLISH_CONTINUATION = "bullish_continuation"
    NO_CLEAR_SETUP = "no_clear_setup"
    AVOID_WAIT = "avoid_wait"
    INCOMPLETE_DATA = "incomplete_data"


class ConfidenceLabel(StrEnum):
    """Educational confidence labels that avoid certainty claims."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class SetupLevelKind(StrEnum):
    """Chart-overlay level roles for a setup idea."""

    CURRENT_PRICE = "current_price"
    ENTRY_ZONE = "entry_zone"
    STOP_INVALIDATION = "stop_invalidation"
    TARGET_ZONE = "target_zone"
    SUPPORT = "support"
    RESISTANCE = "resistance"


class SignalCategory(StrEnum):
    """Signal groups used by scoring, UI explanations, and LLM rationale inputs."""

    TREND = "trend"
    MOMENTUM = "momentum"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    SUPPORT_RESISTANCE = "support_resistance"
    RELATIVE_STRENGTH = "relative_strength"
    RISK_REWARD = "risk_reward"
    DATA_QUALITY = "data_quality"


class SignalPolarity(StrEnum):
    """Direction of a signal's educational interpretation."""

    SUPPORTIVE = "supportive"
    NEUTRAL = "neutral"
    CAUTION = "caution"


TRADE_PLAN_LABELS = frozenset(
    {
        SetupLabel.BULLISH_BREAKOUT,
        SetupLabel.BULLISH_PULLBACK,
        SetupLabel.BULLISH_CONTINUATION,
    }
)


class SetupScoringInput(MarketDataModel):
    """Indicator payload bundle consumed by future deterministic setup scoring."""

    symbol: str
    provider: str
    scored_at: datetime
    indicator_snapshot_id: int | None = None
    indicator_calculation_version: str
    technical_snapshot: TechnicalIndicatorSnapshot
    support_resistance_snapshot: SupportResistanceSnapshot
    relative_strength_snapshot: RelativeStrengthSnapshot

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> str:
        """Normalize supported ticker symbols."""
        return normalize_symbol(value)

    @field_validator("provider", "indicator_calculation_version", mode="before")
    @classmethod
    def validate_required_text(cls, value: object, info: ValidationInfo) -> str:
        """Require non-empty provider and version labels."""
        return normalize_required_text(value, info.field_name or "field")

    @field_validator("scored_at")
    @classmethod
    def validate_scored_at(cls, value: datetime) -> datetime:
        """Require a timezone-aware scoring timestamp."""
        return _validate_timezone_aware(value, "scored_at")

    @field_validator("indicator_snapshot_id")
    @classmethod
    def validate_indicator_snapshot_id(cls, value: int | None) -> int | None:
        """Require a positive persisted indicator snapshot id when one is supplied."""
        if value is not None and value <= 0:
            raise ValueError("indicator_snapshot_id must be positive")
        return value

    @model_validator(mode="after")
    def validate_snapshot_metadata(self) -> Self:
        """Require supplied indicator snapshots to match the scoring input basis."""
        _validate_snapshot_metadata(
            snapshot_name="technical_snapshot",
            symbol=self.technical_snapshot.symbol,
            provider=self.technical_snapshot.provider,
            expected_symbol=self.symbol,
            expected_provider=self.provider,
        )
        _validate_snapshot_metadata(
            snapshot_name="support_resistance_snapshot",
            symbol=self.support_resistance_snapshot.symbol,
            provider=self.support_resistance_snapshot.provider,
            expected_symbol=self.symbol,
            expected_provider=self.provider,
        )
        _validate_snapshot_metadata(
            snapshot_name="relative_strength_snapshot",
            symbol=self.relative_strength_snapshot.symbol,
            provider=self.relative_strength_snapshot.provider,
            expected_symbol=self.symbol,
            expected_provider=self.provider,
        )
        return self


class SetupLevel(MarketDataModel):
    """A price or price zone that future charts can render as an overlay."""

    kind: SetupLevelKind
    label: str
    price: PositiveDecimal | None = None
    zone_low: PositiveDecimal | None = None
    zone_high: PositiveDecimal | None = None
    source: str
    display_order: int

    @field_validator("label", "source", mode="before")
    @classmethod
    def validate_text(cls, value: object, info: ValidationInfo) -> str:
        """Require non-empty level labels and deterministic sources."""
        return normalize_required_text(value, info.field_name or "field")

    @field_validator("display_order")
    @classmethod
    def validate_display_order(cls, value: int) -> int:
        """Keep chart overlay ordering stable and non-negative."""
        if value < 0:
            raise ValueError("display_order must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_price_or_zone(self) -> Self:
        """Require a point price or coherent zone bounds for every setup level."""
        has_price = self.price is not None
        has_zone_low = self.zone_low is not None
        has_zone_high = self.zone_high is not None

        if not has_price and not has_zone_low and not has_zone_high:
            raise ValueError("setup level requires a price or zone")
        if has_zone_low != has_zone_high:
            raise ValueError("zone_low and zone_high must be provided together")
        if self.zone_low is not None and self.zone_high is not None:
            if self.zone_low > self.zone_high:
                raise ValueError("zone_low must be less than or equal to zone_high")
            if self.price is not None and not self.zone_low <= self.price <= self.zone_high:
                raise ValueError("price must be inside the zone")

        return self


class ExpectedHoldingWindow(MarketDataModel):
    """Expected educational swing-trade review window."""

    min_trading_days: int = 3
    max_trading_days: int = 20
    label: str = "3 to 20 trading days"

    @field_validator("min_trading_days", "max_trading_days")
    @classmethod
    def validate_positive_days(cls, value: int) -> int:
        """Require positive holding-window day counts."""
        if value <= 0:
            raise ValueError("holding-window days must be positive")
        return value

    @field_validator("label", mode="before")
    @classmethod
    def validate_label(cls, value: object) -> str:
        """Require a non-empty display label."""
        return normalize_required_text(value, "label")

    @model_validator(mode="after")
    def validate_window_order(self) -> Self:
        """Require the minimum window to be no greater than the maximum."""
        if self.min_trading_days > self.max_trading_days:
            raise ValueError("min_trading_days must be less than or equal to max_trading_days")
        return self


class RiskRewardEstimate(MarketDataModel):
    """Structured risk/reward estimate produced by deterministic scoring."""

    risk_per_share: PositiveDecimal
    reward_per_share: PositiveDecimal
    ratio: PositiveDecimal
    notes: str | None = None

    @field_validator("notes", mode="before")
    @classmethod
    def validate_notes(cls, value: object) -> str | None:
        """Normalize optional risk/reward notes."""
        return _normalize_optional_text(value, "notes")


class FailureCondition(MarketDataModel):
    """A condition that would weaken or invalidate a setup thesis."""

    label: str
    description: str
    level: SetupLevel | None = None
    signal_category: SignalCategory | None = None

    @field_validator("label", "description", mode="before")
    @classmethod
    def validate_text(cls, value: object, info: ValidationInfo) -> str:
        """Require clear failure-case text."""
        return normalize_required_text(value, info.field_name or "field")


class ConfidenceFactor(MarketDataModel):
    """One factor that contributes to the setup confidence label."""

    name: str
    category: SignalCategory
    polarity: SignalPolarity
    score_impact: int
    explanation: str

    @field_validator("name", "explanation", mode="before")
    @classmethod
    def validate_text(cls, value: object, info: ValidationInfo) -> str:
        """Require clear confidence-factor text."""
        return normalize_required_text(value, info.field_name or "field")


class SignalExplanation(MarketDataModel):
    """Structured signal explanation for UI cards and LLM rationale input."""

    category: SignalCategory
    polarity: SignalPolarity
    title: str
    summary: str
    value: str | None = None
    source: str | None = None

    @field_validator("title", "summary", mode="before")
    @classmethod
    def validate_required_text(cls, value: object, info: ValidationInfo) -> str:
        """Require clear signal explanation text."""
        return normalize_required_text(value, info.field_name or "field")

    @field_validator("value", "source", mode="before")
    @classmethod
    def validate_optional_text(cls, value: object, info: ValidationInfo) -> str | None:
        """Normalize optional signal explanation metadata."""
        return _normalize_optional_text(value, info.field_name or "field")


class SetupTradePlan(MarketDataModel):
    """Complete trade-plan structure for bullish setup labels."""

    entry: SetupLevel
    stop_invalidation: SetupLevel
    target: SetupLevel
    risk_reward: RiskRewardEstimate
    expected_holding_window: ExpectedHoldingWindow = Field(default_factory=ExpectedHoldingWindow)
    failure_conditions: tuple[FailureCondition, ...]

    @model_validator(mode="after")
    def validate_trade_plan(self) -> Self:
        """Require role-specific levels and at least one failure condition."""
        if self.entry.kind is not SetupLevelKind.ENTRY_ZONE:
            raise ValueError("entry level must use entry_zone kind")
        if self.stop_invalidation.kind is not SetupLevelKind.STOP_INVALIDATION:
            raise ValueError("stop_invalidation level must use stop_invalidation kind")
        if self.target.kind is not SetupLevelKind.TARGET_ZONE:
            raise ValueError("target level must use target_zone kind")
        if not self.failure_conditions:
            raise ValueError("failure_conditions must include at least one item")
        return self


class SetupIdea(MarketDataModel):
    """Shared deterministic setup idea contract for persistence, API, UI, and rationale."""

    symbol: str
    setup_label: SetupLabel
    score: int
    confidence: ConfidenceLabel
    scored_at: datetime
    scoring_version: str = SCORING_VERSION
    rationale_version: str = RATIONALE_VERSION
    indicator_snapshot_id: int | None = None
    trade_plan: SetupTradePlan | None = None
    confidence_factors: tuple[ConfidenceFactor, ...]
    signal_explanations: tuple[SignalExplanation, ...]
    no_setup_reasons: tuple[str, ...] = ()

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> str:
        """Normalize supported ticker symbols."""
        return normalize_symbol(value)

    @field_validator("scoring_version", "rationale_version", mode="before")
    @classmethod
    def validate_version_text(cls, value: object, info: ValidationInfo) -> str:
        """Require non-empty setup version labels."""
        return normalize_required_text(value, info.field_name or "field")

    @field_validator("scored_at")
    @classmethod
    def validate_scored_at(cls, value: datetime) -> datetime:
        """Require a timezone-aware scoring timestamp."""
        return _validate_timezone_aware(value, "scored_at")

    @field_validator("indicator_snapshot_id")
    @classmethod
    def validate_indicator_snapshot_id(cls, value: int | None) -> int | None:
        """Require a positive persisted indicator snapshot id when one is supplied."""
        if value is not None and value <= 0:
            raise ValueError("indicator_snapshot_id must be positive")
        return value

    @field_validator("no_setup_reasons", mode="before")
    @classmethod
    def validate_no_setup_reasons(cls, value: object) -> tuple[str, ...]:
        """Normalize reason text for no-clear, wait, and incomplete outputs."""
        if value is None:
            return ()
        if isinstance(value, str):
            raw_values: tuple[object, ...] = (value,)
        elif isinstance(value, (list, tuple)):
            raw_values = tuple(value)
        else:
            raise ValueError("no_setup_reasons must be a string or sequence of strings")

        reasons: list[str] = []
        for raw_value in raw_values:
            if not isinstance(raw_value, str):
                raise ValueError("no_setup_reasons must contain only strings")
            text = raw_value.strip()
            if text:
                reasons.append(text)
        return tuple(reasons)

    @model_validator(mode="after")
    def validate_setup_shape(self) -> Self:
        """Separate complete trade-plan ideas from no-clear and wait outputs."""
        is_trade_plan_setup = self.setup_label in TRADE_PLAN_LABELS

        if is_trade_plan_setup and self.trade_plan is None:
            raise ValueError("trade-plan setup labels require a trade_plan")
        if not is_trade_plan_setup and self.trade_plan is not None:
            raise ValueError("non-trade setup labels must not include a trade_plan")
        if not is_trade_plan_setup and not self.no_setup_reasons:
            raise ValueError("non-trade setup labels require no_setup_reasons")

        return self


def _validate_timezone_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _validate_snapshot_metadata(
    *,
    snapshot_name: str,
    symbol: str | None,
    provider: str | None,
    expected_symbol: str,
    expected_provider: str,
) -> None:
    if symbol is not None and symbol != expected_symbol:
        raise ValueError(f"{snapshot_name}.symbol must match symbol")
    if provider is not None and provider != expected_provider:
        raise ValueError(f"{snapshot_name}.provider must match provider")


def _normalize_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return normalize_required_text(value, field_name)


__all__ = [
    "RATIONALE_VERSION",
    "SCORING_VERSION",
    "TRADE_PLAN_LABELS",
    "ConfidenceFactor",
    "ConfidenceLabel",
    "ExpectedHoldingWindow",
    "FailureCondition",
    "RiskRewardEstimate",
    "SetupIdea",
    "SetupLabel",
    "SetupLevel",
    "SetupLevelKind",
    "SetupScoringInput",
    "SetupTradePlan",
    "SignalCategory",
    "SignalExplanation",
    "SignalPolarity",
]

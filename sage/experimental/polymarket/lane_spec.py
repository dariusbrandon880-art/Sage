"""Polymarket External Intelligence Evidence Lane Specification & Contracts.

Defines the 8-stage lifecycle (DISCOVER -> SNAPSHOT -> HASH -> FORECAST -> SEAL -> RESOLVE -> CALIBRATE -> AUDIT),
data contracts, anti-price-echo isolation rules, linear SHA-256 hash chaining, and zero-execution guards.
"""

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


class LifecycleStage(str, Enum):
    DISCOVER = "DISCOVER"
    SNAPSHOT = "SNAPSHOT"
    HASH = "HASH"
    FORECAST = "FORECAST"
    SEAL = "SEAL"
    RESOLVE = "RESOLVE"
    CALIBRATE = "CALIBRATE"
    AUDIT = "AUDIT"


class ExecutionGuardViolation(RuntimeError):
    """Raised when an illegal trading, wallet, capital, or automated execution operation is attempted."""
    pass


class PriceEchoViolation(ValueError):
    """Raised when a SAGE forecast relies on or echoes market prices directly rather than independent probability modeling."""
    pass


@dataclass(frozen=True)
class PolymarketMarketSnapshot:
    condition_id: str
    question_id: str
    question: str
    outcomes: tuple[str, ...]
    outcome_prices: Mapping[str, float]
    observed_at_utc: str
    volume_24h: float = 0.0
    liquidity: float = 0.0
    active: bool = True
    closed: bool = False
    source: str = "Polymarket Gamma/CLOB"
    source_url: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.condition_id or not self.question_id:
            raise ValueError("POLYMARKET_SNAPSHOT_INVALID: condition_id and question_id are required")
        if not self.outcomes or not self.outcome_prices:
            raise ValueError("POLYMARKET_SNAPSHOT_INVALID: outcomes and outcome_prices are required")
        if any(p < 0.0 or p > 1.0 for p in self.outcome_prices.values()):
            raise ValueError("POLYMARKET_SNAPSHOT_INVALID: prices must be valid probabilities in [0.0, 1.0]")
        if abs(sum(self.outcome_prices.values()) - 1.0) > 0.1:  # allow minor market spread / fee margin
            pass

    @property
    def canonical_hash(self) -> str:
        payload = {
            "condition_id": self.condition_id,
            "question_id": self.question_id,
            "question": self.question,
            "outcomes": list(self.outcomes),
            "prices": {k: round(v, 6) for k, v in sorted(self.outcome_prices.items())},
            "observed_at_utc": self.observed_at_utc,
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PolymarketObservation:
    observation_id: str
    snapshot: PolymarketMarketSnapshot
    retrieved_at_utc: str
    raw_payload_hash: str
    normalized_payload_hash: str
    provenance_class: str = "external_live"
    wagering_executed: bool = False

    def __post_init__(self) -> None:
        if self.wagering_executed:
            raise ExecutionGuardViolation("ZERO_EXECUTION_VIOLATION: wagering_executed must be False in read-only lane")
        if not self.observation_id:
            raise ValueError("POLYMARKET_OBSERVATION_INVALID: observation_id required")


@dataclass(frozen=True)
class PolymarketForecastRecord:
    forecast_id: str
    condition_id: str
    predicted_probabilities: Mapping[str, float]
    forecast_generated_at_utc: str
    model_version: str
    rationale: str
    market_price_at_forecast: Mapping[str, float]
    price_echo_isolated: bool = True

    def __post_init__(self) -> None:
        if not self.price_echo_isolated:
            raise PriceEchoViolation("PRICE_ECHO_VIOLATION: forecast failed price echo isolation check")
        if any(p < 0.0 or p > 1.0 for p in self.predicted_probabilities.values()):
            raise ValueError("POLYMARKET_FORECAST_INVALID: probabilities must be in [0.0, 1.0]")
        prob_sum = sum(self.predicted_probabilities.values())
        if abs(prob_sum - 1.0) > 0.01:
            raise ValueError(f"POLYMARKET_FORECAST_INVALID: probabilities must sum to 1.0, got {prob_sum}")

    def validate_price_echo_isolation(self, max_allowed_correlation: float = 0.99) -> bool:
        """Check if forecast probabilities simply copy market prices without independent analysis."""
        diffs = [
            abs(self.predicted_probabilities.get(k, 0.0) - self.market_price_at_forecast.get(k, 0.0))
            for k in self.predicted_probabilities
        ]
        # If difference across all outcomes is exact 0.0, it's a price echo
        if all(d < 1e-6 for d in diffs):
            return False
        return True


@dataclass(frozen=True)
class PolymarketEvidenceRecord:
    evidence_id: str
    stage: LifecycleStage
    observation: PolymarketObservation | None
    forecast: PolymarketForecastRecord | None
    parent_hash: str
    current_hash: str
    timestamp_utc: str
    provenance_metadata: Mapping[str, Any] = field(default_factory=dict)
    wagering_executed: bool = False

    def __post_init__(self) -> None:
        if self.wagering_executed:
            raise ExecutionGuardViolation("ZERO_EXECUTION_VIOLATION: wagering_executed must be False in read-only lane")

    @classmethod
    def compute_record_hash(
        cls,
        evidence_id: str,
        stage: LifecycleStage,
        parent_hash: str,
        timestamp_utc: str,
        obs_hash: str = "",
        forecast_hash: str = "",
    ) -> str:
        payload = {
            "evidence_id": evidence_id,
            "stage": str(stage),
            "parent_hash": parent_hash,
            "timestamp_utc": timestamp_utc,
            "obs_hash": obs_hash,
            "forecast_hash": forecast_hash,
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class PolymarketLaneContract:
    """Enforces zero-execution, linear hash-chain integrity, and anti-price-echo isolation."""

    @staticmethod
    def verify_zero_execution(action_params: Mapping[str, Any]) -> None:
        illegal_keys = {"trade", "buy", "sell", "place_order", "wallet", "private_key", "capital", "execute"}
        found = illegal_keys.intersection({str(k).lower() for k in action_params.keys()})
        if found:
            raise ExecutionGuardViolation(f"ZERO_EXECUTION_VIOLATION: Illegal execution parameter(s) detected: {found}")

    @staticmethod
    def validate_lifecycle_transition(current_stage: LifecycleStage, target_stage: LifecycleStage) -> None:
        stage_order = [
            LifecycleStage.DISCOVER,
            LifecycleStage.SNAPSHOT,
            LifecycleStage.HASH,
            LifecycleStage.FORECAST,
            LifecycleStage.SEAL,
            LifecycleStage.RESOLVE,
            LifecycleStage.CALIBRATE,
            LifecycleStage.AUDIT,
        ]
        curr_idx = stage_order.index(current_stage)
        targ_idx = stage_order.index(target_stage)
        if targ_idx != curr_idx + 1:
            raise ValueError(f"ILLEGAL_LIFECYCLE_TRANSITION: Cannot transition from {current_stage} to {target_stage}")

"""SAGE Polymarket Evidence Lane Specification & Governed Contracts.

Operationalizes the 8-stage lifecycle:
DISCOVER -> SNAPSHOT -> HASH -> FORECAST -> SEAL -> RESOLVE -> CALIBRATE -> AUDIT

Enforces strict zero-execution governance, price-echo anti-contamination,
and immutable cryptographic hash chaining across all market lifecycle states.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class PolymarketLaneState(str, Enum):
    """Lifecycle states for a Polymarket evidence record."""
    DISCOVER = "DISCOVER"
    SNAPSHOT = "SNAPSHOT"
    HASH = "HASH"
    FORECAST = "FORECAST"
    SEAL = "SEAL"
    RESOLVE = "RESOLVE"
    CALIBRATE = "CALIBRATE"
    AUDIT = "AUDIT"


class ExecutionGuardViolation(Exception):
    """Raised when an illegal execution or trading action is attempted."""
    pass


class PriceEchoContaminationError(Exception):
    """Raised when market price is directly copied or leaked into SAGE forecast."""
    pass


class MarketObservation(BaseModel):
    """Raw external market observation (Phase 1: DISCOVER & SNAPSHOT)."""

    model_config = ConfigDict(frozen=True)

    market_id: str = Field(..., description="Unique Polymarket market identifier (e.g. condition_id or slug)")
    event_id: str = Field(..., description="Unique Polymarket event identifier")
    question: str = Field(..., description="Market question text")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp of snapshot")
    market_implied_probability: float = Field(..., ge=0.0, le=1.0, description="Price or probability implied by CLOB V2 order book")
    order_book_depth: Dict[str, Any] = Field(default_factory=dict, description="CLOB V2 bids/asks or depth summary")
    spread: float = Field(..., ge=0.0, description="Bid-ask spread")
    raw_payload_hash: str = Field(..., description="SHA-256 hash of raw API payload")
    provenance_source: str = Field(default="polymarket_clob_v2", description="Data source identifier (Gamma, CLOB, Data API)")


class SageForecast(BaseModel):
    """SAGE independent probability forecast (Phase 2: FORECAST & SEAL)."""

    model_config = ConfigDict(frozen=True)

    forecast_id: str = Field(..., description="Deterministic prediction ID")
    market_id: str = Field(..., description="Target Polymarket market ID")
    forecast_probability: float = Field(..., ge=0.0, le=1.0, description="SAGE independently calculated probability P(SAGE)")
    model_version: str = Field(..., description="Version of SAGE forecasting model/engine")
    forecast_timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp when forecast was sealed")
    rationale_digest: str = Field(..., description="SHA-256 hash of forecast reasoning/evidence context")
    price_echo_check_passed: bool = Field(..., description="Flag asserting market price was not directly copied")

    @model_validator(mode="after")
    def validate_forecast_integrity(self) -> SageForecast:
        if not self.price_echo_check_passed:
            raise PriceEchoContaminationError("Forecast rejected: price echo anti-contamination check failed")
        return self


class MarketResolution(BaseModel):
    """Authoritative market outcome resolution (Phase 3: RESOLVE)."""

    model_config = ConfigDict(frozen=True)

    market_id: str = Field(..., description="Target Polymarket market ID")
    resolved_outcome: float = Field(..., description="1.0 for YES/TRUE, 0.0 for NO/FALSE")
    resolved_timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp of resolution")
    resolution_source: str = Field(..., description="Oracle or resolution reference source")
    resolution_hash: str = Field(..., description="SHA-256 hash of authoritative resolution evidence")


class CalibrationMetrics(BaseModel):
    """Evaluation & Calibration metrics comparing SAGE vs Market vs Ground Truth."""

    model_config = ConfigDict(frozen=True)

    brier_score_sage: float = Field(..., ge=0.0, le=1.0, description="(P_SAGE - Outcome)^2")
    brier_score_market: float = Field(..., ge=0.0, le=1.0, description="(P_Market - Outcome)^2")
    log_loss_sage: float = Field(..., ge=0.0, description="-Outcome * log(P) - (1-Outcome) * log(1-P)")
    log_loss_market: float = Field(..., ge=0.0, description="-Outcome * log(P) - (1-Outcome) * log(1-P)")
    raw_dislocation: float = Field(..., description="P_SAGE - P_market")
    friction_adjusted_dislocation: float = Field(..., description="Dislocation after adjusting for spread & liquidity cost")
    calibration_delta: float = Field(..., description="Improvement in Brier score (Brier_market - Brier_sage)")


class PolymarketEvidenceRecord(BaseModel):
    """Immutable, hash-bound evidence record for the 8-stage lifecycle."""

    record_id: str = Field(..., description="Unique evidence record ID")
    state: PolymarketLaneState = Field(default=PolymarketLaneState.DISCOVER)
    observation: Optional[MarketObservation] = None
    forecast: Optional[SageForecast] = None
    resolution: Optional[MarketResolution] = None
    calibration: Optional[CalibrationMetrics] = None
    chain_hash: str = Field(default="", description="Cumulative SHA-256 linear hash chain")
    execution_attempted: bool = Field(default=False, description="Strict zero-execution sentinel flag")

    @model_validator(mode="after")
    def validate_zero_execution(self) -> PolymarketEvidenceRecord:
        if self.execution_attempted:
            raise ExecutionGuardViolation(
                "GOVERNANCE VIOLATION: Execution / Capital Deployment is STRICTLY PROHIBITED in the Polymarket Evidence Lane"
            )
        return self

    def transition_to_snapshot(self, obs: MarketObservation) -> PolymarketEvidenceRecord:
        """Advance state: DISCOVER -> SNAPSHOT -> HASH."""
        if self.execution_attempted:
            raise ExecutionGuardViolation("Illegal execution state detected")

        self.observation = obs
        self.state = PolymarketLaneState.HASH
        self._update_chain_hash(obs.raw_payload_hash)
        return self

    def seal_forecast(self, forecast: SageForecast, market_obs_prob: float) -> PolymarketEvidenceRecord:
        """Advance state: HASH -> FORECAST -> SEAL with anti-price-echo check."""
        if self.execution_attempted:
            raise ExecutionGuardViolation("Illegal execution state detected")
        if self.observation is None:
            raise ValueError("Cannot seal forecast without market observation")

        # Anti-price-echo isolation rule: exact equality or near-exact clone without tolerance fails closed
        if math.isclose(forecast.forecast_probability, market_obs_prob, abs_tol=1e-6):
            raise PriceEchoContaminationError(
                f"SAGE forecast ({forecast.forecast_probability}) exactly matches market-implied probability ({market_obs_prob})"
            )

        self.forecast = forecast
        self.state = PolymarketLaneState.SEAL
        self._update_chain_hash(forecast.rationale_digest)
        return self

    def resolve_and_calibrate(self, res: MarketResolution) -> PolymarketEvidenceRecord:
        """Advance state: SEAL -> RESOLVE -> CALIBRATE -> AUDIT."""
        if self.execution_attempted:
            raise ExecutionGuardViolation("Illegal execution state detected")
        if self.observation is None or self.forecast is None:
            raise ValueError("Cannot resolve/calibrate without complete observation and forecast")

        self.resolution = res
        self.state = PolymarketLaneState.RESOLVE

        # Compute calibration metrics
        y = res.resolved_outcome
        p_sage = max(1e-6, min(1 - 1e-6, self.forecast.forecast_probability))
        p_mkt = max(1e-6, min(1 - 1e-6, self.observation.market_implied_probability))

        brier_sage = (p_sage - y) ** 2
        brier_mkt = (p_mkt - y) ** 2

        log_loss_sage = -(y * math.log(p_sage) + (1 - y) * math.log(1 - p_sage))
        log_loss_mkt = -(y * math.log(p_mkt) + (1 - y) * math.log(1 - p_mkt))

        raw_dislocation = p_sage - p_mkt
        # Friction penalty = half spread + slippage buffer
        friction = (self.observation.spread / 2.0) + 0.005
        if abs(raw_dislocation) < 1e-9:
            adjusted_dislocation = 0.0
        elif raw_dislocation > 0:
            adjusted_dislocation = max(0.0, raw_dislocation - friction)
        else:
            adjusted_dislocation = min(0.0, raw_dislocation + friction)

        calibration_delta = brier_mkt - brier_sage  # Positive means SAGE was better

        self.calibration = CalibrationMetrics(
            brier_score_sage=round(brier_sage, 6),
            brier_score_market=round(brier_mkt, 6),
            log_loss_sage=round(log_loss_sage, 6),
            log_loss_market=round(log_loss_mkt, 6),
            raw_dislocation=round(raw_dislocation, 6),
            friction_adjusted_dislocation=round(adjusted_dislocation, 6),
            calibration_delta=round(calibration_delta, 6)
        )

        self.state = PolymarketLaneState.AUDIT
        self._update_chain_hash(res.resolution_hash)
        return self

    def attempt_execution(self) -> None:
        """Zero-Execution Guard sentinel function. Always fails closed."""
        self.execution_attempted = True
        raise ExecutionGuardViolation(
            "GOVERNANCE VIOLATION: Execution / Capital Deployment is STRICTLY PROHIBITED in the Polymarket Evidence Lane"
        )

    def _update_chain_hash(self, payload_hash: str) -> None:
        """Maintain SHA-256 linear hash chain: H_i = SHA-256(H_{i-1} || State || Payload_Hash)."""
        content = f"{self.chain_hash}:{self.state.value}:{payload_hash}"
        self.chain_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

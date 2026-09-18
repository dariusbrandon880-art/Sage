"""Unit tests for SAGE Polymarket Evidence Lane Specification & Contracts."""

import pytest
import math
from sage.experimental.polymarket.lane_spec import (
    PolymarketLaneState,
    PolymarketEvidenceRecord,
    MarketObservation,
    SageForecast,
    MarketResolution,
    ExecutionGuardViolation,
    PriceEchoContaminationError,
)


def test_polymarket_evidence_record_lifecycle_success():
    """Verify standard 8-stage lifecycle flow: DISCOVER -> SNAPSHOT -> HASH -> FORECAST -> SEAL -> RESOLVE -> CALIBRATE -> AUDIT."""
    record = PolymarketEvidenceRecord(record_id="poly_rec_001")
    assert record.state == PolymarketLaneState.DISCOVER
    assert record.chain_hash == ""

    # Phase 1: Snapshot
    obs = MarketObservation(
        market_id="mkt_123",
        event_id="evt_456",
        question="Will candidate X win the election?",
        timestamp_utc="2026-09-16T12:00:00Z",
        market_implied_probability=0.55,
        spread=0.02,
        raw_payload_hash="a1b2c3d4e5f60789a1b2c3d4e5f60789a1b2c3d4e5f60789a1b2c3d4e5f60789",
    )
    record.transition_to_snapshot(obs)
    assert record.state == PolymarketLaneState.HASH
    assert len(record.chain_hash) == 64
    initial_hash = record.chain_hash

    # Phase 2: Seal Forecast (Independent, non-echo probability)
    forecast = SageForecast(
        forecast_id="pred_mkt_123_v1",
        market_id="mkt_123",
        forecast_probability=0.68,
        model_version="sage_poly_v1.0",
        forecast_timestamp_utc="2026-09-16T12:05:00Z",
        rationale_digest="f1e2d3c4b5a60987f1e2d3c4b5a60987f1e2d3c4b5a60987f1e2d3c4b5a60987",
        price_echo_check_passed=True,
    )
    record.seal_forecast(forecast, market_obs_prob=obs.market_implied_probability)
    assert record.state == PolymarketLaneState.SEAL
    assert record.chain_hash != initial_hash
    forecast_hash = record.chain_hash

    # Phase 3: Resolve & Calibrate
    res = MarketResolution(
        market_id="mkt_123",
        resolved_outcome=1.0,  # YES resolved
        resolved_timestamp_utc="2026-11-04T00:00:00Z",
        resolution_source="polymarket_uma_oracle",
        resolution_hash="9f8e7d6c5b4a01239f8e7d6c5b4a01239f8e7d6c5b4a01239f8e7d6c5b4a0123",
    )
    record.resolve_and_calibrate(res)
    assert record.state == PolymarketLaneState.AUDIT
    assert record.chain_hash != forecast_hash
    assert record.calibration is not None

    # Calibration verification: P_SAGE=0.68 vs Outcome=1.0 -> Brier = (0.68 - 1)^2 = 0.1024
    # P_Market=0.55 vs Outcome=1.0 -> Brier = (0.55 - 1)^2 = 0.2025
    assert record.calibration.brier_score_sage == pytest.approx(0.1024, abs=1e-4)
    assert record.calibration.brier_score_market == pytest.approx(0.2025, abs=1e-4)
    assert record.calibration.calibration_delta > 0  # SAGE was better calibrated


def test_price_echo_contamination_fails_closed():
    """Verify that copying market probability directly into forecast raises PriceEchoContaminationError."""
    record = PolymarketEvidenceRecord(record_id="poly_rec_echo")
    obs = MarketObservation(
        market_id="mkt_echo",
        event_id="evt_echo",
        question="Will item Y occur?",
        timestamp_utc="2026-09-16T12:00:00Z",
        market_implied_probability=0.42,
        spread=0.01,
        raw_payload_hash="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    )
    record.transition_to_snapshot(obs)

    # Exact echo attempt
    echo_forecast = SageForecast(
        forecast_id="pred_mkt_echo",
        market_id="mkt_echo",
        forecast_probability=0.42,  # Exactly equal to market_implied_probability
        model_version="sage_poly_v1.0",
        forecast_timestamp_utc="2026-09-16T12:01:00Z",
        rationale_digest="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        price_echo_check_passed=True,
    )

    with pytest.raises(PriceEchoContaminationError):
        record.seal_forecast(echo_forecast, market_obs_prob=obs.market_implied_probability)


def test_forecast_failed_flag_raises_error():
    """Verify that price_echo_check_passed=False in SageForecast model raises PriceEchoContaminationError."""
    with pytest.raises(PriceEchoContaminationError):
        SageForecast(
            forecast_id="pred_failed_flag",
            market_id="mkt_fail",
            forecast_probability=0.75,
            model_version="sage_poly_v1.0",
            forecast_timestamp_utc="2026-09-16T12:00:00Z",
            rationale_digest="0000000000000000000000000000000000000000000000000000000000000000",
            price_echo_check_passed=False,
        )


def test_zero_execution_guard_fails_closed():
    """Verify that calling attempt_execution on PolymarketEvidenceRecord raises ExecutionGuardViolation."""
    record = PolymarketEvidenceRecord(record_id="poly_rec_exec")
    with pytest.raises(ExecutionGuardViolation):
        record.attempt_execution()

    assert record.execution_attempted is True

    # Subsequent transitions must fail closed
    obs = MarketObservation(
        market_id="mkt_exec",
        event_id="evt_exec",
        question="Will trade happen?",
        timestamp_utc="2026-09-16T12:00:00Z",
        market_implied_probability=0.50,
        spread=0.01,
        raw_payload_hash="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    )
    with pytest.raises(ExecutionGuardViolation):
        record.transition_to_snapshot(obs)

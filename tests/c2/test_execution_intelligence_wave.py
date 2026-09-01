"""Tests for Wave A Execution Intelligence Substrate."""
import pytest
from sage.c2.execution_intelligence import (
    AdaptiveConcurrencyGovernor,
    AdaptiveConcurrencyProfile,
    ConcurrencyValidationStatus,
    ExecutionAdmissionStatus,
    ExecutionAdmissionThrottler,
    ExecutionIntelligenceReceipt,
    WorkflowVelocityController,
)

EXACT_HEAD_SHA = "bf2560ede2899adfe73fe2e2cfb4accd0b8885e2"


def test_adaptive_concurrency_governor_scaling():
    governor = AdaptiveConcurrencyGovernor(min_workers=1, max_workers=8)

    # Low risk -> normal scaling
    profile_low = governor.calculate_safe_concurrency(
        wave_id="wave_low",
        requested_workers=8,
        lock_contention_rate=0.01,
        verification_latency_ms=50.0,
        rework_rate=0.0,
        cpu_load_factor=0.2,
    )
    assert profile_low.recommended_workers == 8
    assert profile_low.validation_status == ConcurrencyValidationStatus.VALIDATED

    # High risk -> throttled worker scaling
    profile_high = governor.calculate_safe_concurrency(
        wave_id="wave_high",
        requested_workers=8,
        lock_contention_rate=0.8,
        verification_latency_ms=1500.0,
        rework_rate=0.5,
        cpu_load_factor=0.9,
    )
    assert profile_high.recommended_workers < 8
    assert profile_high.validation_status == ConcurrencyValidationStatus.HOLD


def test_execution_admission_throttler_capacity_and_risk():
    throttler = ExecutionAdmissionThrottler(max_capacity=2, rate_limit_per_sec=100.0)

    # Request 1: Admitted
    r1 = throttler.request_admission("F1", risk_score=0.1)
    assert r1["admitted"] is True
    assert r1["status"] == ExecutionAdmissionStatus.ADMITTED

    # High risk request: Rejected
    r_high = throttler.request_admission("F_HIGH", risk_score=0.9)
    assert r_high["admitted"] is False
    assert r_high["status"] == ExecutionAdmissionStatus.REJECTED_HIGH_RISK


def test_workflow_velocity_controller_wave_execution():
    controller = WorkflowVelocityController()
    flights = [{"flight_id": f"F{i}", "target": f"Target {i}"} for i in range(1, 6)]

    receipt = controller.execute_execution_intelligence_wave(
        wave_id="wave_exec_test",
        exact_git_head=EXACT_HEAD_SHA,
        flights=flights,
        requested_workers=4,
    )

    assert receipt.exact_git_head == EXACT_HEAD_SHA
    assert receipt.total_flights == 5
    assert receipt.concurrent_workers_used > 0
    assert receipt.receipt_hash == receipt.compute_hash()
    assert receipt.rolls_royce_quality_passed is True


def test_workflow_velocity_controller_invalid_sha():
    controller = WorkflowVelocityController()
    with pytest.raises(ValueError, match="Invalid exact git HEAD commit SHA"):
        controller.execute_execution_intelligence_wave(
            wave_id="wave_invalid",
            exact_git_head="invalid_sha_123",
            flights=[{"flight_id": "F1"}],
        )

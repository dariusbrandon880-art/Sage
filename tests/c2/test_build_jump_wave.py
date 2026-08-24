"""Unit tests for Build Jump Wave Dispatch Engine."""

import pytest
from sage.c2.build_jump_wave import (
    BuildJumpWaveDispatchEngine,
    FlightVectorTarget,
    WaveStatus,
)


def test_build_jump_wave_normal_dispatch_and_reconvergence():
    """Verify normal 5-flight wave dispatch and reconvergence."""
    engine = BuildJumpWaveDispatchEngine()
    now_utc = "2026-08-24T00:15:00Z"
    commit_sha = "ed70dc8"

    targets = tuple(
        FlightVectorTarget(
            flight_id=f"F{i+1}_TARGET",
            path_number=i+1,
            course_part=1,
            mission_objective=f"Objective {i+1}",
            target_module=f"sage/c2/module_{i+1}.py",
            required_test_suite=f"tests/test_{i+1}.py",
            authorized=True,
        )
        for i in range(5)
    )

    status, receipts = engine.dispatch_wave("wave_001", commit_sha, targets, now_utc)
    assert status == WaveStatus.VERIFIED
    assert len(receipts) == 5

    wave_receipt = engine.reconverge_wave("wave_001", commit_sha, receipts, now_utc)
    assert wave_receipt.status == WaveStatus.RECONVERGED
    assert wave_receipt.reconvergence_verdict == "PASS"
    assert wave_receipt.receipt_digest is not None


def test_build_jump_wave_unauthorized_target_fails_closed():
    """Verify fail-closed HOLD state when a target is unauthorized."""
    engine = BuildJumpWaveDispatchEngine()
    now_utc = "2026-08-24T00:15:00Z"
    commit_sha = "ed70dc8"

    targets = tuple(
        FlightVectorTarget(
            flight_id=f"F{i+1}_TARGET",
            path_number=i+1,
            course_part=1,
            mission_objective=f"Objective {i+1}",
            target_module=f"sage/c2/module_{i+1}.py",
            required_test_suite=f"tests/test_{i+1}.py",
            authorized=(i != 2),  # Target F3 is unauthorized
        )
        for i in range(5)
    )

    status, receipts = engine.dispatch_wave("wave_unauth", commit_sha, targets, now_utc)
    assert status == WaveStatus.HOLD
    assert receipts[2].status == "HOLD_UNAUTHORIZED"

    wave_receipt = engine.reconverge_wave("wave_unauth", commit_sha, receipts, now_utc)
    assert wave_receipt.status == WaveStatus.HOLD
    assert wave_receipt.reconvergence_verdict == "HOLD"


def test_build_jump_wave_invalid_inputs():
    """Verify validation exceptions for empty wave ID, invalid commit SHA, or incorrect targets count."""
    engine = BuildJumpWaveDispatchEngine()
    now_utc = "2026-08-24T00:15:00Z"

    with pytest.raises(ValueError, match="Wave ID cannot be empty"):
        engine.dispatch_wave("", "ed70dc8", (), now_utc)

    with pytest.raises(ValueError, match="Valid commit SHA is required"):
        engine.dispatch_wave("wave_001", "123", (), now_utc)

    with pytest.raises(ValueError, match="requires exactly 5 flight targets"):
        engine.dispatch_wave("wave_001", "ed70dc8", (), now_utc)

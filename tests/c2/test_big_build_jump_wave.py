"""Unit tests for Big Build Jump Wave Full Frame Controller."""

import pytest
from sage.c2.big_build_jump_wave import (
    BigBuildJumpWaveEngine,
    FlightMission,
    FlightVector,
    WaveStatus,
)


def test_big_build_jump_wave_normal_execution():
    """Verify normal 5 independent flight vector dispatch and reconvergence."""
    engine = BigBuildJumpWaveEngine()
    now_utc = "2026-08-24T00:30:00Z"
    commit_sha = "ed70dc8"

    vectors = tuple(
        FlightVector(
            flight_number=i + 1,
            mission=FlightMission(
                mission_id=f"m_f{i+1}",
                frontier_id=f"frontier_{i+1}",
                target_subsystem=f"sage/experimental/subsystem_{i+1}.py",
                objective=f"Objective for flight {i+1}",
                required_test_suite=f"tests/experimental/test_{i+1}.py",
                authorized=True,
            ),
            risk_level="LOW",
            collision_keys=(f"key_{i+1}",),
        )
        for i in range(5)
    )

    receipt = engine.dispatch_and_reconverge("wave_bbjw_test_001", commit_sha, vectors, now_utc)

    assert receipt.status == WaveStatus.RECONVERGED
    assert receipt.collision_status == "CLEARED"
    assert receipt.boundary_status == "VERIFIED"
    assert receipt.validation_status == "PASS"
    assert receipt.promotion_status == "CLEARED_FOR_PROMOTION"
    assert len(receipt.flight_receipts) == 5


def test_big_build_jump_wave_collision_rejection():
    """Verify collision detection when two flights target the same collision key."""
    engine = BigBuildJumpWaveEngine()
    now_utc = "2026-08-24T00:30:00Z"
    commit_sha = "ed70dc8"

    vectors = tuple(
        FlightVector(
            flight_number=i + 1,
            mission=FlightMission(
                mission_id=f"m_f{i+1}",
                frontier_id=f"frontier_{i+1}",
                target_subsystem=f"sage/experimental/subsystem_{i+1}.py",
                objective=f"Objective for flight {i+1}",
                required_test_suite=f"tests/experimental/test_{i+1}.py",
                authorized=True,
            ),
            risk_level="LOW",
            # Flight 1 and Flight 2 share collision key 'shared_collision_key'
            collision_keys=("shared_collision_key",) if i < 2 else (f"key_{i+1}",),
        )
        for i in range(5)
    )

    receipt = engine.dispatch_and_reconverge("wave_collision", commit_sha, vectors, now_utc)

    assert receipt.status == WaveStatus.HOLD
    assert "BLOCKED" in receipt.collision_status
    assert receipt.validation_status == "HOLD"


def test_big_build_jump_wave_unauthorized_mission_fails_closed():
    """Verify fail-closed HOLD state when a flight mission is unauthorized."""
    engine = BigBuildJumpWaveEngine()
    now_utc = "2026-08-24T00:30:00Z"
    commit_sha = "ed70dc8"

    vectors = tuple(
        FlightVector(
            flight_number=i + 1,
            mission=FlightMission(
                mission_id=f"m_f{i+1}",
                frontier_id=f"frontier_{i+1}",
                target_subsystem=f"sage/experimental/subsystem_{i+1}.py",
                objective=f"Objective for flight {i+1}",
                required_test_suite=f"tests/experimental/test_{i+1}.py",
                authorized=(i != 3),  # Flight 4 is unauthorized
            ),
            risk_level="LOW",
            collision_keys=(f"key_{i+1}",),
        )
        for i in range(5)
    )

    receipt = engine.dispatch_and_reconverge("wave_unauth", commit_sha, vectors, now_utc)

    assert receipt.status == WaveStatus.HOLD
    assert receipt.boundary_status == "VIOLATION"
    assert receipt.flight_receipts[3].status == "HOLD_UNAUTHORIZED"


def test_big_build_jump_wave_duplicate_flight_numbers_rejection():
    """Verify ValueError when flight numbers are duplicated or invalid."""
    engine = BigBuildJumpWaveEngine()
    now_utc = "2026-08-24T00:30:00Z"
    commit_sha = "ed70dc8"

    vectors = tuple(
        FlightVector(
            flight_number=1,  # All flight numbers are 1
            mission=FlightMission(
                mission_id=f"m_f{i+1}",
                frontier_id=f"frontier_{i+1}",
                target_subsystem=f"sage/experimental/subsystem_{i+1}.py",
                objective=f"Objective for flight {i+1}",
                required_test_suite=f"tests/experimental/test_{i+1}.py",
                authorized=True,
            ),
            risk_level="LOW",
            collision_keys=(f"key_{i+1}",),
        )
        for i in range(5)
    )

    with pytest.raises(ValueError, match="numbered uniquely 1 through 5"):
        engine.dispatch_and_reconverge("wave_dup", commit_sha, vectors, now_utc)

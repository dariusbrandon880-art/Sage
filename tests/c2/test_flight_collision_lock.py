"""Unit tests for Multi-Session Flight Collision Prevention & Lock Manager."""

from sage.c2.flight_collision_lock import (
    FlightCollisionLockManager,
    FlightLockRequest,
)


def test_lock_acquisition_success():
    manager = FlightCollisionLockManager()

    request = FlightLockRequest(
        session_id="jules-session-1",
        flight_id="F1",
        target_files=["sage/c2/frontier_admission.py"],
        target_namespaces=["sage/c2/"],
    )

    result = manager.acquire_lock(request)

    assert result.acquired is True
    assert result.conflicting_resource is None
    assert len(result.lock_hash) == 64
    assert len(manager.get_active_locks()) == 2


def test_lock_conflict_prevention():
    manager = FlightCollisionLockManager()

    request1 = FlightLockRequest(
        session_id="jules-session-1",
        flight_id="F1",
        target_files=["sage/c2/shared.py"],
        target_namespaces=[],
    )

    request2 = FlightLockRequest(
        session_id="jules-session-2",
        flight_id="F2",
        target_files=["sage/c2/shared.py"],
        target_namespaces=[],
    )

    result1 = manager.acquire_lock(request1)
    assert result1.acquired is True

    result2 = manager.acquire_lock(request2)
    assert result2.acquired is False
    assert result2.conflicting_session_id == "jules-session-1"
    assert result2.conflicting_flight_id == "F1"
    assert result2.conflicting_resource == "sage/c2/shared.py"


def test_lock_release_and_reacquisition():
    manager = FlightCollisionLockManager()

    request1 = FlightLockRequest(
        session_id="jules-session-1",
        flight_id="F1",
        target_files=["sage/c2/shared.py"],
        target_namespaces=[],
    )

    request2 = FlightLockRequest(
        session_id="jules-session-2",
        flight_id="F2",
        target_files=["sage/c2/shared.py"],
        target_namespaces=[],
    )

    manager.acquire_lock(request1)
    released = manager.release_lock("jules-session-1", "F1")
    assert released is True

    result2 = manager.acquire_lock(request2)
    assert result2.acquired is True

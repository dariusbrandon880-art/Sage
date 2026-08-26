"""Unit tests for Multi-Session Flight Collision Prevention & Lock Manager."""

from sage.c2.flight_collision_lock import (
    FlightCollisionLockManager,
    FlightLockRequest,
    normalize_path,
    paths_overlap,
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


def test_paths_overlap_helper():
    assert paths_overlap("sage/c2/", "sage/c2/flight_gps/engine.py") is True
    assert paths_overlap("sage/c2/flight_gps/engine.py", "sage/c2") is True
    assert paths_overlap("sage/c2", "sage/core") is False
    assert paths_overlap("sage/c2_other", "sage/c2") is False


def test_hierarchical_subpath_containment_collision_rejection():
    manager = FlightCollisionLockManager()

    # Session 1 locks parent namespace 'sage/c2/'
    req1 = FlightLockRequest(
        session_id="session-1",
        flight_id="F1",
        target_files=[],
        target_namespaces=["sage/c2/"],
    )
    res1 = manager.acquire_lock(req1)
    assert res1.acquired is True

    # Session 2 attempts to lock child file 'sage/c2/flight_gps/engine.py'
    req2 = FlightLockRequest(
        session_id="session-2",
        flight_id="F2",
        target_files=["sage/c2/flight_gps/engine.py"],
        target_namespaces=[],
    )
    res2 = manager.acquire_lock(req2)
    assert res2.acquired is False, "Parent namespace lock must reject subpath file lock request."
    assert res2.conflicting_session_id == "session-1"
    assert res2.conflicting_flight_id == "F1"

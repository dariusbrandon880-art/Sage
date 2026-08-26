"""Unit and adversarial tests for FlightCollisionLockManager."""

from sage.c2.flight_collision_lock import FlightCollisionLockManager, FlightLockRequest


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
    request1 = FlightLockRequest("jules-session-1", "F1", ["sage/c2/shared.py"], [])
    request2 = FlightLockRequest("jules-session-2", "F2", ["sage/c2/shared.py"], [])
    assert manager.acquire_lock(request1).acquired is True
    result2 = manager.acquire_lock(request2)
    assert result2.acquired is False
    assert result2.conflicting_session_id == "jules-session-1"
    assert result2.conflicting_flight_id == "F1"
    assert result2.conflicting_resource == "sage/c2/shared.py"


def test_lock_release_and_reacquisition():
    manager = FlightCollisionLockManager()
    request1 = FlightLockRequest("jules-session-1", "F1", ["sage/c2/shared.py"], [])
    request2 = FlightLockRequest("jules-session-2", "F2", ["sage/c2/shared.py"], [])
    manager.acquire_lock(request1)
    assert manager.release_lock("jules-session-1", "F1") is True
    assert manager.acquire_lock(request2).acquired is True


def test_normalize_path_collapses_separators_and_dot_segments():
    manager = FlightCollisionLockManager()
    assert manager.normalize_path("./sage/c2//shared.py/") == "sage/c2/shared.py"
    assert manager.normalize_path(r"sage\\c2\\shared.py") == "sage/c2/shared.py"


def test_paths_overlap_parent_child_containment():
    manager = FlightCollisionLockManager()
    assert manager.paths_overlap("sage/c2/", "sage/c2/flight_collision_lock.py") is True
    assert manager.paths_overlap("sage/c2/frontier_admission.py", "sage/c2/frontier_admission.py") is True
    assert manager.paths_overlap("sage/c2/a.py", "sage/c20/a.py") is False


def test_parent_namespace_blocks_child_file():
    manager = FlightCollisionLockManager()
    parent = FlightLockRequest("jules-session-1", "F1", [], ["sage/c2/"])
    child = FlightLockRequest("jules-session-2", "F2", ["sage/c2/flight_collision_lock.py"], [])
    assert manager.acquire_lock(parent).acquired is True
    result = manager.acquire_lock(child)
    assert result.acquired is False
    assert result.conflicting_session_id == "jules-session-1"
    assert result.conflicting_flight_id == "F1"
    assert result.conflicting_resource == "sage/c2"


def test_child_namespace_blocks_parent_namespace():
    manager = FlightCollisionLockManager()
    child = FlightLockRequest("jules-session-1", "F1", [], ["sage/c2/flight/"])
    parent = FlightLockRequest("jules-session-2", "F2", [], ["sage/c2/"])
    assert manager.acquire_lock(child).acquired is True
    assert manager.acquire_lock(parent).acquired is False


def test_normalized_equivalent_paths_collide():
    manager = FlightCollisionLockManager()
    first = FlightLockRequest("jules-session-1", "F1", ["./sage/c2/shared.py/"], [])
    second = FlightLockRequest("jules-session-2", "F2", [r"sage\\c2\\shared.py"], [])
    assert manager.acquire_lock(first).acquired is True
    assert manager.acquire_lock(second).acquired is False

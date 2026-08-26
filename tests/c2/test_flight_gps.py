from sage.c2.flight_gps.classifier import classify_candidate
from sage.c2.flight_gps.engine import FlightGPS
from sage.c2.flight_gps.heartbeat import HeartbeatMonitor
from sage.c2.flight_gps.models import (
    AirspaceStatus,
    FlightLifecycle,
    FlightManifest,
    ObservabilityState,
    OwnershipFingerprint,
)
from sage.c2.flight_gps.wave_planner import WavePlanner


def manifest(flight_id="F", files=None, **kwargs):
    return FlightManifest(
        flight_id=flight_id,
        capability_target=flight_id,
        base_sha="HEAD",
        ownership=OwnershipFingerprint(files=set(files or [])),
        **kwargs,
    )


def test_dual_state_file_collision_is_occupied_for_active_owner():
    active = manifest("A", ["sage/x.py"], lifecycle=FlightLifecycle.ACTIVE)
    candidate = manifest("C", ["sage/x.py"])
    assert classify_candidate(candidate, {"A": active}, "HEAD") == AirspaceStatus.OCCUPIED


def test_expired_existing_owner_is_stale_not_occupied():
    active = manifest("A", ["sage/x.py"], lifecycle=FlightLifecycle.ACTIVE, last_ping_utc=0)
    candidate = manifest("C", ["sage/x.py"])
    assert classify_candidate(candidate, {"A": active}, "HEAD") == AirspaceStatus.STALE


def test_heartbeat_probe_refreshes_stale_owner():
    active = manifest("A", lifecycle=FlightLifecycle.ACTIVE, last_ping_utc=0)
    registry = {"A": active}
    HeartbeatMonitor(lambda session: True).evaluate_and_reclaim(registry, now=121)
    assert active.lifecycle == FlightLifecycle.ACTIVE
    assert active.airspace == AirspaceStatus.CLEAR
    assert active.last_ping_utc == 121


def test_heartbeat_reclaims_unresponsive_owner_without_erasing_manifest():
    active = manifest("A", lifecycle=FlightLifecycle.ACTIVE, last_ping_utc=0)
    registry = {"A": active}
    HeartbeatMonitor(lambda session: False).evaluate_and_reclaim(registry, now=121)
    assert registry["A"].lifecycle == FlightLifecycle.ABANDONED
    assert registry["A"].airspace == AirspaceStatus.STALE


def test_offline_observability_halts_new_dispatch():
    candidate = manifest("C")
    assert WavePlanner().plan(
        [candidate], {"C": AirspaceStatus.CLEAR}, ObservabilityState.OFFLINE
    ) == []


def test_wave_planner_routes_around_occupied_frontiers():
    candidates = [manifest(str(i)) for i in range(7)]
    airspace = {str(i): AirspaceStatus.CLEAR for i in range(7)}
    airspace["0"] = AirspaceStatus.OCCUPIED
    selected = WavePlanner().plan(candidates, airspace, ObservabilityState.NOMINAL)
    assert [m.flight_id for m in selected] == ["1", "2", "3", "4", "5"]


def test_engine_produces_observer_snapshot_without_git_writes():
    gps = FlightGPS("HEAD")
    snapshot = gps.observe([manifest("C")])
    assert snapshot.observability == ObservabilityState.NOMINAL
    assert snapshot.airspace["C"] == AirspaceStatus.CLEAR
    assert [m.flight_id for m in snapshot.recommended] == ["C"]
    assert "C" in snapshot.clearances
    assert snapshot.clearances["C"].cleared is True
    assert len(snapshot.clearances["C"].receipt_hash) == 64


def test_gps_clearance_receipt_tampering_detection():
    gps = FlightGPS("407f7b52b161c520688bd8eef509146d86717c74")
    snapshot = gps.observe([manifest("C")])
    receipt = snapshot.clearances["C"]
    assert receipt.cleared is True
    assert receipt.receipt_hash == receipt.compute_hash()

    # Tamper with target
    receipt.capability_target = "tampered/target.py"
    assert receipt.receipt_hash != receipt.compute_hash(), "Tampered receipt hash must mismatch."


def test_gps_clearance_fails_closed_on_occupied_or_offline():
    gps = FlightGPS("407f7b52b161c520688bd8eef509146d86717c74")
    active = manifest("A", ["sage/x.py"], lifecycle=FlightLifecycle.ACTIVE)
    gps.registry.register(active)

    candidate = manifest("C", ["sage/x.py"])
    snapshot = gps.observe([candidate], observability=ObservabilityState.NOMINAL)

    assert snapshot.airspace["C"] == AirspaceStatus.OCCUPIED
    assert snapshot.clearances["C"].cleared is False
    assert snapshot.recommended == []

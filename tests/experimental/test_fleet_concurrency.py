"""Unit and adversarial tests for SAGE Fleet Concurrency Engine."""
import pytest
from sage.experimental.airspace.fleet_concurrency import (
    FleetConcurrencyEngine,
    FlightWorkUnit,
    FleetConcurrencyResult,
)


def test_flight_work_unit_digest():
    """Verify FlightWorkUnit produces a valid deterministic digest."""
    unit = FlightWorkUnit(
        flight_id="Flight A",
        mission_id="msn-001",
        frontier_name="research_intelligence",
        namespace_boundary="sage.c2.flight_a",
        depends_on=("msn-base",),
    )
    digest = unit.digest()
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_detect_collisions_namespace_and_mission_id():
    """Verify engine detects namespace and mission ID collisions across units."""
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(
            flight_id="Flight A",
            mission_id="msn-001",
            frontier_name="frontier_a",
            namespace_boundary="sage.boundary.shared",
        ),
        FlightWorkUnit(
            flight_id="Flight B",
            mission_id="msn-001",  # Mission ID collision
            frontier_name="frontier_b",
            namespace_boundary="sage.boundary.shared",  # Namespace collision
        ),
    ]

    collisions = engine.detect_collisions(units)
    assert len(collisions) == 2
    assert "Namespace collision" in collisions[0]
    assert "Mission ID collision" in collisions[1]


def test_execute_concurrent_wave_success():
    """Verify successful collision-free concurrent dispatch across independent flight slots."""
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(
            flight_id="Flight A",
            mission_id="msn-001",
            frontier_name="frontier_a",
            namespace_boundary="sage.boundary.a",
        ),
        FlightWorkUnit(
            flight_id="Flight B",
            mission_id="msn-002",
            frontier_name="frontier_b",
            namespace_boundary="sage.boundary.b",
            depends_on=("msn-001",),
        ),
    ]

    result = engine.execute_concurrent_wave(dispatch_id="disp-001", units=units)
    assert result.verdict == "PASS"
    assert result.flight_units_executed == 2
    assert result.collisions_detected == ()
    assert result.successful_missions == ("msn-001", "msn-002")


def test_execute_concurrent_wave_fails_closed_on_collision():
    """Verify that collision detection rejects the wave in a fail-closed posture."""
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(
            flight_id="Flight A",
            mission_id="msn-dup",
            frontier_name="frontier_a",
            namespace_boundary="sage.boundary.a",
        ),
        FlightWorkUnit(
            flight_id="Flight B",
            mission_id="msn-dup",
            frontier_name="frontier_b",
            namespace_boundary="sage.boundary.b",
        ),
    ]

    result = engine.execute_concurrent_wave(dispatch_id="disp-collision", units=units)
    assert result.verdict == "REJECTED_COLLISION"
    assert result.flight_units_executed == 0
    assert len(result.collisions_detected) > 0


def test_invalid_engine_initialization_and_args():
    """Verify invalid engine arguments raise ValueError."""
    with pytest.raises(ValueError, match="max_concurrent_flights must be at least 1"):
        FleetConcurrencyEngine(max_concurrent_flights=0)

    engine = FleetConcurrencyEngine()
    with pytest.raises(ValueError, match="dispatch_id is required"):
        engine.execute_concurrent_wave(dispatch_id="  ", units=[])

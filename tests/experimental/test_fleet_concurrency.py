"""Test suite for SAGE Airspace Fleet Concurrency Substrate."""

import pytest
from sage.experimental.airspace.fleet_concurrency import (
    FleetConcurrencyEngine,
    FlightWorkUnit,
    FleetConcurrencyResult,
)


def test_fleet_concurrency_execution():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/c2/f1.py"),
        FlightWorkUnit(unit_id="U2", flight_id="F2", target_path="sage/c2/f2.py", dependencies=["U1"]),
    ]

    result = engine.execute_concurrent_wave("WAVE-001", units)
    assert result.is_reconverged is True
    assert result.total_units == 2
    assert result.successful_units == 2
    assert len(result.lock_conflicts) == 0
    assert "U1" in result.unit_receipts
    assert "U2" in result.unit_receipts


def test_fleet_concurrency_cycle_detection():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/c2/f1.py", dependencies=["U2"]),
        FlightWorkUnit(unit_id="U2", flight_id="F2", target_path="sage/c2/f2.py", dependencies=["U1"]),
    ]

    with pytest.raises(ValueError, match="cyclic dependency"):
        engine.execute_concurrent_wave("WAVE-CYCLE", units)


def test_fleet_concurrency_namespace_collision():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/c2/shared.py"),
        FlightWorkUnit(unit_id="U2", flight_id="F2", target_path="sage/c2/shared.py"),
    ]

    result = engine.execute_concurrent_wave("WAVE-COLLISION", units)
    assert result.is_reconverged is False
    assert len(result.lock_conflicts) == 1
    assert "Namespace collision" in result.lock_conflicts[0]

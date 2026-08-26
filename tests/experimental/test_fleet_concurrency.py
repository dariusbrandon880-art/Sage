"""Tests for the bounded SAGE Fleet Concurrency substrate."""

import time

import pytest

from sage.experimental.airspace.fleet_concurrency import (
    FleetConcurrencyEngine,
    FlightWorkUnit,
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
    assert result.executed_units == 2
    assert result.lock_conflicts == []
    assert set(result.unit_receipts) == {"U1", "U2"}


def test_fleet_concurrency_cycle_detection():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/c2/f1.py", dependencies=["U2"]),
        FlightWorkUnit(unit_id="U2", flight_id="F2", target_path="sage/c2/f2.py", dependencies=["U1"]),
    ]

    with pytest.raises(ValueError, match="cyclic dependency"):
        engine.execute_concurrent_wave("WAVE-CYCLE", units)


def test_fleet_concurrency_unknown_dependency_fails_closed():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/c2/f1.py", dependencies=["MISSING"]),
    ]

    with pytest.raises(ValueError, match="unknown dependencies"):
        engine.execute_concurrent_wave("WAVE-UNKNOWN", units)


def test_fleet_concurrency_duplicate_unit_id_fails_closed():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/c2/f1.py"),
        FlightWorkUnit(unit_id="U1", flight_id="F2", target_path="sage/c2/f2.py"),
    ]

    with pytest.raises(ValueError, match="duplicate unit IDs"):
        engine.execute_concurrent_wave("WAVE-DUP", units)


def test_fleet_concurrency_hierarchical_namespace_collision():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/experimental/c2"),
        FlightWorkUnit(unit_id="U2", flight_id="F2", target_path="sage/experimental/c2/submodule.py"),
    ]

    result = engine.execute_concurrent_wave("WAVE-HIERARCHICAL", units)
    assert result.is_reconverged is False
    assert result.failed_units == 2
    assert len(result.lock_conflicts) == 1
    assert "Hierarchical collision" in result.lock_conflicts[0]


def test_fleet_concurrency_namespace_collision():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/c2/shared.py"),
        FlightWorkUnit(unit_id="U2", flight_id="F2", target_path="sage/c2/shared.py"),
    ]

    result = engine.execute_concurrent_wave("WAVE-COLLISION", units)
    assert result.is_reconverged is False
    assert result.failed_units == 2
    assert len(result.lock_conflicts) == 1
    assert "Namespace collision" in result.lock_conflicts[0]


def test_fleet_concurrency_fingerprint_is_stable_across_runs():
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/c2/f1.py", payload={"x": 1}),
        FlightWorkUnit(unit_id="U2", flight_id="F2", target_path="sage/c2/f2.py", dependencies=["U1"], payload={"y": 2}),
    ]

    first = FleetConcurrencyEngine().execute_concurrent_wave("WAVE-STABLE", units)
    time.sleep(0.001)
    second = FleetConcurrencyEngine().execute_concurrent_wave("WAVE-STABLE", units)

    assert first.timestamp != second.timestamp
    assert first.wave_fingerprint == second.wave_fingerprint
    assert first.unit_receipts == second.unit_receipts


def test_fleet_concurrency_rejects_promotional_authority_action():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(
            unit_id="U1",
            flight_id="F1",
            target_path="sage/c2/f1.py",
            action_type="PROMOTIONAL",
        )
    ]

    with pytest.raises(ValueError, match="Unsupported action type"):
        engine.execute_concurrent_wave("WAVE-PROMOTION", units)


def test_fleet_concurrency_rejects_protected_namespace():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/runtime/model.py"),
    ]

    with pytest.raises(ValueError, match="protected namespace"):
        engine.execute_concurrent_wave("WAVE-PROTECTED", units)


def test_fleet_concurrency_rejects_path_traversal():
    engine = FleetConcurrencyEngine()
    units = [
        FlightWorkUnit(unit_id="U1", flight_id="F1", target_path="sage/c2/../runtime/model.py"),
    ]

    with pytest.raises(ValueError, match="protected namespace"):
        engine.execute_concurrent_wave("WAVE-TRAVERSAL", units)

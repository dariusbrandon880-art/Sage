"""Unit and adversarial tests for SAGE Fleet Readiness Intelligence Layer."""

from __future__ import annotations

from sage.c2.reconvergence_synthesizer import (
    C2ReconvergenceSynthesizer,
    FlightExecutionSummary,
    LifecycleMilestoneRecord,
    LifecycleStage,
)
from sage.experimental.airspace.fleet_readiness import (
    FleetReadinessEngine,
    ReadinessStatus,
)
from sage.experimental.airspace.models import AirspaceState, StationID

VALID_SHA = "db2592167dba5eda4c024bba9202ff085d9c1d9b"


def test_station_readiness_ready():
    state = AirspaceState()
    engine = FleetReadinessEngine(commit_sha="commit_test_123")

    score = engine.evaluate_station_readiness(
        state=state,
        station_id=StationID.ENGINEERING_FLIGHT,
        test_pass_rate=1.0,
        evidence_refs=["commit:123", "receipt:456"],
        protected_path_violations=0,
    )

    assert score.station_id == StationID.ENGINEERING_FLIGHT
    assert score.status == ReadinessStatus.READY
    assert score.overall_score > 0.7
    assert score.protected_path_violations == 0
    assert score.read_only is True


def test_station_readiness_unqualified_without_evidence():
    state = AirspaceState()
    engine = FleetReadinessEngine(commit_sha="commit_test_123")

    score = engine.evaluate_station_readiness(
        state=state,
        station_id=StationID.INTEL_STATION,
        test_pass_rate=1.0,
        evidence_refs=[],  # No evidence
        protected_path_violations=0,
    )

    assert score.station_id == StationID.INTEL_STATION
    assert score.status == ReadinessStatus.UNQUALIFIED
    assert score.overall_score == 0.0


def test_station_readiness_blocked_on_protected_path_violations():
    state = AirspaceState()
    engine = FleetReadinessEngine(commit_sha="commit_test_123")

    score = engine.evaluate_station_readiness(
        state=state,
        station_id=StationID.MISSION_CONTROL,
        test_pass_rate=1.0,
        evidence_refs=["receipt:777"],
        protected_path_violations=2,  # Violation present
    )

    assert score.station_id == StationID.MISSION_CONTROL
    assert score.status == ReadinessStatus.BLOCKED
    assert score.overall_score == 0.0
    assert score.protected_path_violations == 2


def test_station_readiness_degraded_on_failing_tests():
    state = AirspaceState()
    engine = FleetReadinessEngine(commit_sha="commit_test_123")

    score = engine.evaluate_station_readiness(
        state=state,
        station_id=StationID.ENGINEERING_FLIGHT,
        test_pass_rate=0.85,  # Failing tests
        evidence_refs=["receipt:888"],
        protected_path_violations=0,
    )

    assert score.station_id == StationID.ENGINEERING_FLIGHT
    assert score.status == ReadinessStatus.DEGRADED
    assert "DEGRADED" in score.rationale


def test_evaluate_fleet_readiness_overall_receipt():
    state = AirspaceState()
    engine = FleetReadinessEngine(commit_sha="sha_fleet_999")

    evaluations = {
        StationID.MISSION_DIRECTOR: {"test_pass_rate": 1.0, "evidence_refs": ["ref_1"]},
        StationID.MISSION_CONTROL: {"test_pass_rate": 1.0, "evidence_refs": ["ref_2"]},
        StationID.INTEL_STATION: {"test_pass_rate": 1.0, "evidence_refs": ["ref_3"]},
        StationID.ENGINEERING_FLIGHT: {"test_pass_rate": 1.0, "evidence_refs": ["ref_4"]},
    }

    receipt = engine.evaluate_fleet_readiness(state, evaluations)

    assert receipt.commit_sha == "sha_fleet_999"
    assert receipt.fleet_verdict == ReadinessStatus.READY
    assert len(receipt.station_scores) == 4
    assert receipt.overall_fleet_readiness > 0.7
    assert len(receipt.provenance_hash) == 64


def test_evaluate_wave_readiness_integration():
    state = AirspaceState()
    engine = FleetReadinessEngine(commit_sha=VALID_SHA)

    synthesizer = C2ReconvergenceSynthesizer(wave_id="wave-readiness-001")
    flights = []
    for i in range(1, 6):
        milestones = [
            LifecycleMilestoneRecord(stage=s, passed=True, evidence_ref=f"ref_{i}")
            for s in LifecycleStage
        ]
        flights.append(
            FlightExecutionSummary(
                flight_id=f"F{i}",
                target=f"target_{i}",
                classification="ACTIVE",
                execution_result="PASS",
                exact_head=VALID_SHA,
                tests_passed=10,
                evidence_ref=f"evidence_{i}.json",
                pr_or_change=f"PR #{i}",
                lifecycle_milestones=milestones,
            )
        )

    pkg = synthesizer.synthesize_reconvergence(flights)
    receipt = engine.evaluate_wave_readiness(state, pkg)

    assert receipt.fleet_verdict == ReadinessStatus.READY
    assert receipt.overall_fleet_readiness > 0.7


def test_fleet_readiness_does_not_mutate_state_or_xp():
    state = AirspaceState()
    xp_before = state.game_progression.get_total_airspace_xp()
    cql_before = state.stations[StationID.ENGINEERING_FLIGHT].current_cql

    engine = FleetReadinessEngine()
    engine.evaluate_fleet_readiness(
        state,
        {
            StationID.ENGINEERING_FLIGHT: {"test_pass_rate": 1.0, "evidence_refs": ["ref_5"]},
        },
    )

    xp_after = state.game_progression.get_total_airspace_xp()
    cql_after = state.stations[StationID.ENGINEERING_FLIGHT].current_cql

    assert xp_before == xp_after
    assert cql_before == cql_after

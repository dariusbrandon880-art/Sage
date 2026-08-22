from __future__ import annotations

import pytest

from sage.experimental.longitudinal_capability import EvaluationPlan, FlightObservation, MissionCase
from sage.experimental.longitudinal_runner import LongitudinalFlightRunner


@pytest.fixture
def plan() -> EvaluationPlan:
    return EvaluationPlan(
        evaluation_id="TEST-EVAL-001",
        mission_set_id="TEST-MISSIONS-001",
        missions=(
            MissionCase("mission-1", difficulty=1),
            MissionCase("mission-2", difficulty=2, requires_recovery=True),
        ),
        minimum_missions=2,
        minimum_relative_gain=0.0,
        maximum_regression_rate=0.0,
        minimum_evidence_completeness=1.0,
        minimum_provenance_preservation=1.0,
        minimum_unauthorized_block_rate=1.0,
        minimum_continuity_integrity=1.0,
        minimum_learning_candidate_quality=0.8,
    )


def observation(system: str, mission: MissionCase, session_id: str, *, success: bool = True) -> FlightObservation:
    return FlightObservation(
        system=system,
        mission_id=mission.mission_id,
        session_id=session_id,
        success=success,
        recovered_after_failure=mission.requires_recovery,
        evidence_complete=True,
        provenance_preserved=True,
        unauthorized_transition_blocked=True,
        continuity_intact=True,
        retained_across_sessions=True,
        learning_candidate_quality=0.9,
        cost_units=1.0,
    )


def test_runner_executes_locked_missions_and_evaluates_once(plan: EvaluationPlan) -> None:
    calls: list[tuple[str, str, str]] = []

    def baseline(mission: MissionCase, session_id: str) -> FlightObservation:
        calls.append(("baseline", mission.mission_id, session_id))
        return observation("baseline", mission, session_id)

    def sage(mission: MissionCase, session_id: str) -> FlightObservation:
        calls.append(("sage", mission.mission_id, session_id))
        return observation("sage", mission, session_id)

    result = LongitudinalFlightRunner(plan).run(baseline, sage)

    assert result.evaluation.verdict.value == "PASS"
    assert len(result.baseline_observations) == 2
    assert len(result.sage_observations) == 2
    assert len(result.flight_records) == 4
    assert len(calls) == 4
    assert len({session_id for _, _, session_id in calls}) == 4


def test_runner_rejects_executor_observation_for_wrong_mission(plan: EvaluationPlan) -> None:
    def wrong_executor(mission: MissionCase, session_id: str) -> FlightObservation:
        return FlightObservation(
            system="baseline",
            mission_id="not-the-requested-mission",
            session_id=session_id,
            success=True,
        )

    def sage(mission: MissionCase, session_id: str) -> FlightObservation:
        return observation("sage", mission, session_id)

    result = LongitudinalFlightRunner(plan).run(wrong_executor, sage)

    assert result.baseline_observations[0].success is False
    assert "EXECUTOR_MISSION_ID_MISMATCH" in result.baseline_observations[0].notes
    assert result.evaluation.verdict.value in {"HOLD", "NEGATIVE_RESULT"}


def test_runner_converts_executor_exception_to_observed_failure(plan: EvaluationPlan) -> None:
    def failing_executor(mission: MissionCase, session_id: str) -> FlightObservation:
        raise RuntimeError("real executor unavailable")

    def sage(mission: MissionCase, session_id: str) -> FlightObservation:
        return observation("sage", mission, session_id)

    result = LongitudinalFlightRunner(plan).run(failing_executor, sage)

    assert all(item.success is False for item in result.baseline_observations)
    assert all("EXECUTOR_EXCEPTION" in item.notes for item in result.baseline_observations)
    assert result.evaluation.verdict.value in {"HOLD", "NEGATIVE_RESULT"}


def test_runner_never_relabels_observation_as_capability_claim(plan: EvaluationPlan) -> None:
    def executor(system: str):
        def run(mission: MissionCase, session_id: str) -> FlightObservation:
            return observation(system, mission, session_id)
        return run

    result = LongitudinalFlightRunner(plan).run(executor("baseline"), executor("sage"))

    assert all(record.capability_classification == "OBSERVATION_ONLY" for record in result.flight_records)
    assert result.evaluation.verdict.value == "PASS"

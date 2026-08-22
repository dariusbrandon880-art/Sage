"""Governed execution harness for real longitudinal SAGE flights.

This module is intentionally an execution bridge, not a second evaluator or
authority. A caller supplies the real baseline and SAGE mission executors.
Those executors must return observations from actual execution; this harness
never fabricates successful telemetry or capability state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Callable, Mapping, Optional, Sequence
from uuid import uuid4

from .flight_record import SAGEFlightRecord, SAGEFlightRecordManager
from .longitudinal_capability import (
    CapabilityEvaluationReceipt,
    EvaluationPlan,
    FlightObservation,
    LongitudinalCapabilityEvaluator,
    MissionCase,
)


MissionExecutor = Callable[[MissionCase, str], FlightObservation]


@dataclass(frozen=True)
class LongitudinalFlightResult:
    """Complete result of one baseline-vs-SAGE longitudinal flight."""

    evaluation: CapabilityEvaluationReceipt
    baseline_observations: tuple[FlightObservation, ...]
    sage_observations: tuple[FlightObservation, ...]
    flight_records: tuple[SAGEFlightRecord, ...]


class LongitudinalFlightRunner:
    """Execute a locked mission plan against baseline and SAGE executors.

    The runner measures wall-clock execution time around each real executor,
    validates that returned observations belong to the requested mission and
    system, and optionally persists append-only flight records. It does not
    synthesize observations, mutate evaluation thresholds, or bypass the
    longitudinal evaluator.
    """

    def __init__(
        self,
        plan: EvaluationPlan,
        record_manager: Optional[SAGEFlightRecordManager] = None,
        mission_session_prefix: str = "longitudinal",
    ) -> None:
        self.plan = plan
        self.record_manager = record_manager
        self.mission_session_prefix = mission_session_prefix

    def run(
        self,
        baseline_executor: MissionExecutor,
        sage_executor: MissionExecutor,
    ) -> LongitudinalFlightResult:
        """Run every locked mission for baseline and SAGE, then evaluate once."""
        baseline = self._run_system("baseline", baseline_executor)
        sage = self._run_system("sage", sage_executor)

        evaluator = LongitudinalCapabilityEvaluator(self.plan)
        receipt = evaluator.evaluate(baseline, sage)

        records = tuple(
            self._persist_observation(system, observation)
            for system, observation in [
                *(('baseline', item) for item in baseline),
                *(('sage', item) for item in sage),
            ]
        )
        return LongitudinalFlightResult(
            evaluation=receipt,
            baseline_observations=tuple(baseline),
            sage_observations=tuple(sage),
            flight_records=records,
        )

    def _run_system(
        self,
        system: str,
        executor: MissionExecutor,
    ) -> list[FlightObservation]:
        observations: list[FlightObservation] = []
        for index, mission in enumerate(self.plan.missions, start=1):
            session_id = f"{self.mission_session_prefix}:{system}:{index}:{uuid4().hex}"
            started = perf_counter()
            started_at = datetime.now(timezone.utc).isoformat()
            try:
                observation = executor(mission, session_id)
                observation = self._validate_observation(
                    system, mission, session_id, observation, perf_counter() - started
                )
            except Exception as exc:
                # An execution exception is itself a real observed failure. The
                # conservative fields below intentionally prevent a PASS based
                # on telemetry that was never produced.
                observation = FlightObservation(
                    system=system,
                    mission_id=mission.mission_id,
                    session_id=session_id,
                    success=False,
                    recovered_after_failure=False,
                    evidence_complete=False,
                    provenance_preserved=False,
                    unauthorized_transition_blocked=False,
                    continuity_intact=False,
                    retained_across_sessions=False,
                    learning_candidate_quality=None,
                    elapsed_seconds=perf_counter() - started,
                    notes=f"EXECUTOR_EXCEPTION at {started_at}: {type(exc).__name__}: {exc}",
                )
            observations.append(observation)
        return observations

    @staticmethod
    def _validate_observation(
        system: str,
        mission: MissionCase,
        session_id: str,
        observation: FlightObservation,
        elapsed_seconds: float,
    ) -> FlightObservation:
        if not isinstance(observation, FlightObservation):
            raise TypeError("EXECUTOR_MUST_RETURN_FLIGHT_OBSERVATION")
        if observation.system != system:
            raise ValueError("EXECUTOR_SYSTEM_LABEL_MISMATCH")
        if observation.mission_id != mission.mission_id:
            raise ValueError("EXECUTOR_MISSION_ID_MISMATCH")
        if observation.session_id != session_id:
            raise ValueError("EXECUTOR_SESSION_ID_MISMATCH")
        if observation.elapsed_seconds is None:
            return FlightObservation(
                **{
                    **observation.__dict__,
                    "elapsed_seconds": elapsed_seconds,
                }
            )
        if observation.elapsed_seconds < 0:
            raise ValueError("NEGATIVE_ELAPSED_SECONDS")
        return observation

    def _persist_observation(
        self,
        system: str,
        observation: FlightObservation,
    ) -> SAGEFlightRecord:
        record = SAGEFlightRecord(
            record_id=uuid4().hex,
            timestamp=datetime.now(timezone.utc).isoformat(),
            mission_id=observation.mission_id,
            operator_or_agent=system,
            session_id=observation.session_id,
            task_description=observation.notes or observation.mission_id,
            action_type="LONGITUDINAL_FLIGHT_OBSERVATION",
            test_results={
                "success": observation.success,
                "evidence_complete": observation.evidence_complete,
                "provenance_preserved": observation.provenance_preserved,
                "unauthorized_transition_blocked": observation.unauthorized_transition_blocked,
                "continuity_intact": observation.continuity_intact,
                "retained_across_sessions": observation.retained_across_sessions,
                "recovered_after_failure": observation.recovered_after_failure,
                "elapsed_seconds": observation.elapsed_seconds,
                "cost_units": observation.cost_units,
                "regression_detected": observation.regression_detected,
                "learning_candidate_quality": observation.learning_candidate_quality,
            },
            result_status="SUCCESS" if observation.success else "FAILED",
            capability_classification="OBSERVATION_ONLY",
            learning_notes=observation.notes or None,
        )
        if self.record_manager is not None:
            return self.record_manager.record_flight_event(record)
        return record


def run_locked_longitudinal_flight(
    plan: EvaluationPlan,
    baseline_executor: MissionExecutor,
    sage_executor: MissionExecutor,
    record_manager: Optional[SAGEFlightRecordManager] = None,
) -> LongitudinalFlightResult:
    """Convenience entry point for a single locked baseline/SAGE flight."""
    return LongitudinalFlightRunner(
        plan=plan,
        record_manager=record_manager,
    ).run(baseline_executor, sage_executor)

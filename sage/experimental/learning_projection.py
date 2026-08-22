"""Bounded projection from flight outcomes into candidate learning records."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sage.experimental.longitudinal_capability import CapabilityVerdict, FlightObservation


@dataclass(frozen=True)
class LearningProjection:
    mission_id: str
    kind: str
    candidate: bool
    constraint: str | None
    reason: str


def project_learning(verdict: CapabilityVerdict, observations: Sequence[FlightObservation]) -> tuple[LearningProjection, ...]:
    if not observations:
        raise ValueError("NO_OBSERVATIONS")
    results: list[LearningProjection] = []
    if verdict is CapabilityVerdict.NEGATIVE_RESULT:
        for observation in observations:
            results.append(LearningProjection(observation.mission_id, "NEGATIVE_CONSTRAINT", False, "REGRESSION_OR_FAILURE_MUST_NOT_RECUR", "negative result is durable constraint, not capability success"))
        return tuple(results)
    if verdict is not CapabilityVerdict.PASS:
        return tuple(LearningProjection(o.mission_id, "NO_LEARNING", False, None, "HOLD_OR_INDETERMINATE_DOES_NOT_CREATE_CAPABILITY_MEMORY") for o in observations)
    for observation in observations:
        admissible = observation.success and observation.evidence_complete and observation.provenance_preserved and observation.continuity_intact
        results.append(LearningProjection(observation.mission_id, "CANDIDATE" if admissible else "NO_LEARNING", admissible, None if admissible else "EVIDENCE_BOUNDARY_NOT_SATISFIED", "bounded candidate projection only"))
    return tuple(results)

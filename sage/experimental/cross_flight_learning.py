"""Read-only cross-flight learning projection.

Validated observations can become candidate inputs for other missions without
becoming canonical knowledge, authorization, or automatic promotion.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class FlightLearning:
    source_mission: str
    learning_id: str
    summary: str
    evidence_digest: str
    verified: bool
    reusable: bool = True

    @property
    def admissible(self) -> bool:
        return bool(self.source_mission and self.learning_id and self.summary and self.evidence_digest and self.verified)


@dataclass(frozen=True)
class LearningCandidate:
    target_mission: str
    source_mission: str
    learning_id: str
    summary: str
    evidence_digest: str
    authority_granted: bool = False
    canonical: bool = False


def project_learning_candidates(
    learnings: Iterable[FlightLearning],
    target_mission: str,
) -> tuple[LearningCandidate, ...]:
    """Project only verified learning into candidate inputs for another mission."""
    if not target_mission:
        raise ValueError("target_mission is required")
    candidates = [
        LearningCandidate(
            target_mission=target_mission,
            source_mission=item.source_mission,
            learning_id=item.learning_id,
            summary=item.summary,
            evidence_digest=item.evidence_digest,
        )
        for item in learnings
        if item.admissible and item.source_mission != target_mission
    ]
    return tuple(sorted(candidates, key=lambda item: (item.learning_id, item.source_mission)))

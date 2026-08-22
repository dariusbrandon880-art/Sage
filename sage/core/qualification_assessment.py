"""Qualification assessment v0.1 — bounded multi-episode capability evidence.

This primitive aggregates already-verified episode evidence into a deterministic,
read-only qualification assessment. It recommends; it never promotes, mutates,
or grants authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import ClassVar, Sequence


class QualificationAssessmentValidationError(ValueError):
    """Raised when qualification evidence violates its structural contract."""


class EpisodeVerdict(str, Enum):
    """Semantic verdict carried by an already-evaluated episode."""

    VERIFIED_SUPPORT = "VERIFIED_SUPPORT"
    VERIFIED_CONTRADICTION = "VERIFIED_CONTRADICTION"
    UNRESOLVED = "UNRESOLVED"
    INDETERMINATE = "INDETERMINATE"


class FailureAttribution(str, Enum):
    """Bounded attribution classes; attribution never changes authority."""

    AGENT_FAULT = "AGENT_FAULT"
    ENVIRONMENT_NOISE = "ENVIRONMENT_NOISE"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


class QualificationRecommendation(str, Enum):
    """Non-authoritative recommendation produced by the assessment."""

    PROMOTION_RECOMMENDED = "PROMOTION_RECOMMENDED"
    REINFORCEMENT_NEEDED = "REINFORCEMENT_NEEDED"
    HOLD = "HOLD"


@dataclass(frozen=True)
class CapabilityEvidenceEpisode:
    """Immutable reference to one previously evaluated capability episode."""

    projection_digest: str
    capability_id: str
    verdict: EpisodeVerdict
    failure_attribution: FailureAttribution = FailureAttribution.NONE
    evidence_weight: float = 1.0
    independent: bool = True

    def __post_init__(self) -> None:
        for name in ("projection_digest", "capability_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise QualificationAssessmentValidationError(
                    f"{name} must be a non-empty string."
                )
        if not isinstance(self.verdict, EpisodeVerdict):
            raise QualificationAssessmentValidationError(
                "verdict must be an EpisodeVerdict."
            )
        if not isinstance(self.failure_attribution, FailureAttribution):
            raise QualificationAssessmentValidationError(
                "failure_attribution must be a FailureAttribution."
            )
        if not isinstance(self.evidence_weight, (int, float)) or not (
            0.0 < self.evidence_weight <= 1.0
        ):
            raise QualificationAssessmentValidationError(
                "evidence_weight must be greater than 0 and at most 1.0."
            )
        if not isinstance(self.independent, bool):
            raise QualificationAssessmentValidationError("independent must be bool.")
        if (
            self.verdict == EpisodeVerdict.VERIFIED_SUPPORT
            and self.failure_attribution != FailureAttribution.NONE
        ):
            raise QualificationAssessmentValidationError(
                "VERIFIED_SUPPORT cannot carry a failure attribution."
            )
        if (
            self.verdict == EpisodeVerdict.VERIFIED_CONTRADICTION
            and self.failure_attribution == FailureAttribution.NONE
        ):
            raise QualificationAssessmentValidationError(
                "VERIFIED_CONTRADICTION requires failure attribution."
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "projection_digest": self.projection_digest,
            "capability_id": self.capability_id,
            "verdict": self.verdict.value,
            "failure_attribution": self.failure_attribution.value,
            "evidence_weight": self.evidence_weight,
            "independent": self.independent,
        }


@dataclass(frozen=True)
class QualificationAssessment:
    """Deterministic, non-authoritative aggregation of capability evidence."""

    capability_id: str
    episodes: tuple[CapabilityEvidenceEpisode, ...]
    current_qualification_state: str = "UNQUALIFIED"
    reviewer_authorization_required: bool = field(default=True, init=False)
    authority_granted: bool = field(default=False, init=False)

    MIN_INDEPENDENT_EPISODES: ClassVar[int] = 3
    MIN_SUPPORTING_EPISODES: ClassVar[int] = 2
    PROMOTION_THRESHOLD: ClassVar[float] = 0.80
    MAX_AGENT_FAULT_RATE: ClassVar[float] = 0.25

    def __post_init__(self) -> None:
        if not isinstance(self.capability_id, str) or not self.capability_id.strip():
            raise QualificationAssessmentValidationError(
                "capability_id must be a non-empty string."
            )
        if not isinstance(self.episodes, tuple) or not self.episodes:
            raise QualificationAssessmentValidationError(
                "episodes must be a non-empty tuple."
            )
        if any(not isinstance(e, CapabilityEvidenceEpisode) for e in self.episodes):
            raise QualificationAssessmentValidationError(
                "episodes must contain CapabilityEvidenceEpisode values."
            )
        if any(e.capability_id != self.capability_id for e in self.episodes):
            raise QualificationAssessmentValidationError(
                "all episodes must target the assessed capability."
            )
        if self.current_qualification_state not in {"QUALIFIED", "UNQUALIFIED"}:
            raise QualificationAssessmentValidationError(
                "current_qualification_state must be QUALIFIED or UNQUALIFIED."
            )

    @property
    def independent_episodes(self) -> tuple[CapabilityEvidenceEpisode, ...]:
        return tuple(e for e in self.episodes if e.independent)

    @property
    def supporting_episodes(self) -> tuple[CapabilityEvidenceEpisode, ...]:
        return tuple(
            e
            for e in self.independent_episodes
            if e.verdict == EpisodeVerdict.VERIFIED_SUPPORT
        )

    @property
    def contradictory_episodes(self) -> tuple[CapabilityEvidenceEpisode, ...]:
        return tuple(
            e
            for e in self.independent_episodes
            if e.verdict == EpisodeVerdict.VERIFIED_CONTRADICTION
        )

    @property
    def agent_fault_episodes(self) -> tuple[CapabilityEvidenceEpisode, ...]:
        return tuple(
            e
            for e in self.independent_episodes
            if e.failure_attribution == FailureAttribution.AGENT_FAULT
        )

    @property
    def unresolved_episodes(self) -> tuple[CapabilityEvidenceEpisode, ...]:
        return tuple(
            e
            for e in self.independent_episodes
            if e.verdict in {EpisodeVerdict.UNRESOLVED, EpisodeVerdict.INDETERMINATE}
        )

    @property
    def confidence_score(self) -> float:
        """Return a transparent evidence-balance score, not a probability of truth."""
        support = sum(e.evidence_weight for e in self.supporting_episodes)
        contradiction = sum(e.evidence_weight for e in self.contradictory_episodes)
        total = support + contradiction
        if total == 0.0:
            return 0.0
        return round(support / total, 6)

    @property
    def agent_fault_rate(self) -> float:
        total = len(self.independent_episodes)
        if total == 0:
            return 0.0
        return round(len(self.agent_fault_episodes) / total, 6)

    @property
    def recommendation(self) -> QualificationRecommendation:
        if len(self.independent_episodes) < self.MIN_INDEPENDENT_EPISODES:
            return QualificationRecommendation.HOLD
        if self.contradictory_episodes:
            return QualificationRecommendation.HOLD
        if self.unresolved_episodes:
            return QualificationRecommendation.HOLD
        if len(self.supporting_episodes) < self.MIN_SUPPORTING_EPISODES:
            return QualificationRecommendation.REINFORCEMENT_NEEDED
        if self.agent_fault_rate > self.MAX_AGENT_FAULT_RATE:
            return QualificationRecommendation.REINFORCEMENT_NEEDED
        if self.confidence_score < self.PROMOTION_THRESHOLD:
            return QualificationRecommendation.REINFORCEMENT_NEEDED
        return QualificationRecommendation.PROMOTION_RECOMMENDED

    @property
    def assessment_digest(self) -> str:
        payload = {
            "agent_fault_rate": self.agent_fault_rate,
            "capability_id": self.capability_id,
            "confidence_score": self.confidence_score,
            "current_qualification_state": self.current_qualification_state,
            "episodes": [e.to_dict() for e in self.episodes],
            "recommendation": self.recommendation.value,
            "reviewer_authorization_required": self.reviewer_authorization_required,
        }
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "capability_id": self.capability_id,
            "confidence_score": self.confidence_score,
            "recommendation": self.recommendation.value,
            "current_qualification_state": self.current_qualification_state,
            "reviewer_authorization_required": self.reviewer_authorization_required,
            "authority_granted": self.authority_granted,
            "agent_fault_rate": self.agent_fault_rate,
            "assessment_digest": self.assessment_digest,
            "episodes": [e.to_dict() for e in self.episodes],
        }

    @classmethod
    def assess(
        cls,
        *,
        capability_id: str,
        episodes: Sequence[CapabilityEvidenceEpisode],
        current_qualification_state: str = "UNQUALIFIED",
    ) -> "QualificationAssessment":
        """Create an assessment without persistence, promotion, or side effects."""
        return cls(
            capability_id=capability_id,
            episodes=tuple(episodes),
            current_qualification_state=current_qualification_state,
        )

"""Transition sufficiency v0.1 — non-authoritative capability gate.

Evaluates an immutable QualificationAssessment against an explicit policy.
A sufficient verdict never grants authority, mutates qualification state, or
performs a capability transition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from sage.core.qualification_assessment import QualificationAssessment


class TransitionSufficiencyValidationError(ValueError):
    """Raised when a sufficiency policy or assessment violates its contract."""


class SufficiencyVerdict(str, Enum):
    """Non-authoritative result of evaluating transition evidence sufficiency."""

    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTED = "CONFLICTED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class TransitionSufficiencyPolicy:
    """Explicit deterministic requirements for a capability transition review."""

    minimum_independent_episodes: int = 3
    minimum_supporting_episodes: int = 2
    minimum_confidence_score: float = 0.85
    maximum_agent_fault_rate: float = 0.25
    require_unresolved_free: bool = True
    require_contradiction_free: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.minimum_independent_episodes, int) or isinstance(
            self.minimum_independent_episodes, bool
        ) or self.minimum_independent_episodes < 1:
            raise TransitionSufficiencyValidationError(
                "minimum_independent_episodes must be a positive integer."
            )
        if not isinstance(self.minimum_supporting_episodes, int) or isinstance(
            self.minimum_supporting_episodes, bool
        ) or self.minimum_supporting_episodes < 1:
            raise TransitionSufficiencyValidationError(
                "minimum_supporting_episodes must be a positive integer."
            )
        if self.minimum_supporting_episodes > self.minimum_independent_episodes:
            raise TransitionSufficiencyValidationError(
                "minimum_supporting_episodes cannot exceed minimum_independent_episodes."
            )
        if not isinstance(self.minimum_confidence_score, (int, float)) or not (
            0.0 <= self.minimum_confidence_score <= 1.0
        ):
            raise TransitionSufficiencyValidationError(
                "minimum_confidence_score must be between 0.0 and 1.0."
            )
        if not isinstance(self.maximum_agent_fault_rate, (int, float)) or not (
            0.0 <= self.maximum_agent_fault_rate <= 1.0
        ):
            raise TransitionSufficiencyValidationError(
                "maximum_agent_fault_rate must be between 0.0 and 1.0."
            )
        if not isinstance(self.require_unresolved_free, bool):
            raise TransitionSufficiencyValidationError(
                "require_unresolved_free must be bool."
            )
        if not isinstance(self.require_contradiction_free, bool):
            raise TransitionSufficiencyValidationError(
                "require_contradiction_free must be bool."
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "minimum_independent_episodes": self.minimum_independent_episodes,
            "minimum_supporting_episodes": self.minimum_supporting_episodes,
            "minimum_confidence_score": self.minimum_confidence_score,
            "maximum_agent_fault_rate": self.maximum_agent_fault_rate,
            "require_unresolved_free": self.require_unresolved_free,
            "require_contradiction_free": self.require_contradiction_free,
        }


@dataclass(frozen=True)
class TransitionSufficiency:
    """Immutable sufficiency result; it never authorizes a capability transition."""

    capability_id: str
    assessment_digest: str
    policy: TransitionSufficiencyPolicy
    verdict: SufficiencyVerdict
    failed_requirements: tuple[str, ...] = ()
    reviewer_authorization_required: bool = field(default=True, init=False)
    authority_granted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.capability_id, str) or not self.capability_id.strip():
            raise TransitionSufficiencyValidationError(
                "capability_id must be a non-empty string."
            )
        if not isinstance(self.assessment_digest, str) or not self.assessment_digest.strip():
            raise TransitionSufficiencyValidationError(
                "assessment_digest must be a non-empty string."
            )
        if not isinstance(self.policy, TransitionSufficiencyPolicy):
            raise TransitionSufficiencyValidationError(
                "policy must be a TransitionSufficiencyPolicy."
            )
        if not isinstance(self.verdict, SufficiencyVerdict):
            raise TransitionSufficiencyValidationError(
                "verdict must be a SufficiencyVerdict."
            )
        if not isinstance(self.failed_requirements, tuple) or any(
            not isinstance(item, str) or not item.strip()
            for item in self.failed_requirements
        ):
            raise TransitionSufficiencyValidationError(
                "failed_requirements must be a tuple of non-empty strings."
            )

    @property
    def sufficiency_digest(self) -> str:
        payload = {
            "assessment_digest": self.assessment_digest,
            "authority_granted": self.authority_granted,
            "capability_id": self.capability_id,
            "failed_requirements": list(self.failed_requirements),
            "policy": self.policy.to_dict(),
            "reviewer_authorization_required": self.reviewer_authorization_required,
            "verdict": self.verdict.value,
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "capability_id": self.capability_id,
            "assessment_digest": self.assessment_digest,
            "verdict": self.verdict.value,
            "failed_requirements": list(self.failed_requirements),
            "reviewer_authorization_required": self.reviewer_authorization_required,
            "authority_granted": self.authority_granted,
            "sufficiency_digest": self.sufficiency_digest,
        }

    @classmethod
    def evaluate(
        cls,
        assessment: QualificationAssessment,
        *,
        policy: TransitionSufficiencyPolicy | None = None,
    ) -> "TransitionSufficiency":
        """Evaluate sufficiency without persistence, mutation, or authorization."""
        if not isinstance(assessment, QualificationAssessment):
            raise TransitionSufficiencyValidationError(
                "assessment must be a QualificationAssessment."
            )
        policy = policy or TransitionSufficiencyPolicy()
        failed: list[str] = []
        independent_count = len(assessment.independent_episodes)
        supporting_count = len(assessment.supporting_episodes)

        if independent_count < policy.minimum_independent_episodes:
            failed.append("minimum_independent_episodes")
        if supporting_count < policy.minimum_supporting_episodes:
            failed.append("minimum_supporting_episodes")
        if policy.require_contradiction_free and assessment.contradictory_episodes:
            failed.append("contradiction_free")
        if policy.require_unresolved_free and assessment.unresolved_episodes:
            failed.append("unresolved_free")
        if assessment.confidence_score < policy.minimum_confidence_score:
            failed.append("minimum_confidence_score")
        if assessment.agent_fault_rate > policy.maximum_agent_fault_rate:
            failed.append("maximum_agent_fault_rate")

        if assessment.contradictory_episodes:
            verdict = SufficiencyVerdict.CONFLICTED
        elif assessment.unresolved_episodes:
            verdict = SufficiencyVerdict.INDETERMINATE
        elif failed:
            verdict = SufficiencyVerdict.INSUFFICIENT
        else:
            verdict = SufficiencyVerdict.SUFFICIENT

        return cls(
            capability_id=assessment.capability_id,
            assessment_digest=assessment.assessment_digest,
            policy=policy,
            verdict=verdict,
            failed_requirements=tuple(failed),
        )

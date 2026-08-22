"""RealityGapAssessment v0.1 — pure T0-to-T1 world-model fidelity projection.

This primitive intentionally separates three questions:
- whether a decision was authorized at T0;
- whether its evidence was sufficient at T0;
- whether a declared claim aligned with an observed T1 outcome.

It performs no storage, signing, authority, capability, qualification, XP,
mission, archive, runtime, or transport mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json


class RealityGapValidationError(ValueError):
    """Raised when a reality-gap assessment cannot be constructed safely."""


class RealityGapStatus(str, Enum):
    ALIGNED = "ALIGNED"
    PARTIALLY_ALIGNED = "PARTIALLY_ALIGNED"
    DIVERGED = "DIVERGED"
    UNRESOLVED = "UNRESOLVED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class RealityGapAssessment:
    """Immutable, deterministic comparison of a T0 claim to a T1 observation."""

    decision_id: str
    context_id: str
    t0_claim_ref: str
    t0_sufficiency_ref: str
    t1_observation_ref: str
    observed_at: str
    status: RealityGapStatus
    rationale: str
    authority_granted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        for name in (
            "decision_id",
            "context_id",
            "t0_claim_ref",
            "t0_sufficiency_ref",
            "t1_observation_ref",
            "observed_at",
            "rationale",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise RealityGapValidationError(f"{name} must be a non-empty string.")
        if not isinstance(self.status, RealityGapStatus):
            raise RealityGapValidationError("status must be a RealityGapStatus.")

    @property
    def assessment_digest(self) -> str:
        payload = {
            "context_id": self.context_id,
            "decision_id": self.decision_id,
            "observed_at": self.observed_at,
            "rationale": self.rationale,
            "status": self.status.value,
            "t0_claim_ref": self.t0_claim_ref,
            "t0_sufficiency_ref": self.t0_sufficiency_ref,
            "t1_observation_ref": self.t1_observation_ref,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "decision_id": self.decision_id,
            "context_id": self.context_id,
            "t0_claim_ref": self.t0_claim_ref,
            "t0_sufficiency_ref": self.t0_sufficiency_ref,
            "t1_observation_ref": self.t1_observation_ref,
            "observed_at": self.observed_at,
            "status": self.status.value,
            "rationale": self.rationale,
            "assessment_digest": self.assessment_digest,
            "authority_granted": self.authority_granted,
        }

    @classmethod
    def assess(
        cls,
        *,
        decision_id: str,
        context_id: str,
        t0_claim_ref: str,
        t0_sufficiency_ref: str,
        t1_observation_ref: str,
        observed_at: str,
        status: RealityGapStatus,
        rationale: str,
    ) -> "RealityGapAssessment":
        return cls(
            decision_id=decision_id,
            context_id=context_id,
            t0_claim_ref=t0_claim_ref,
            t0_sufficiency_ref=t0_sufficiency_ref,
            t1_observation_ref=t1_observation_ref,
            observed_at=observed_at,
            status=status,
            rationale=rationale,
        )

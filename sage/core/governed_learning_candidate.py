"""Governed learning candidate v0.1 — non-authoritative learning proposals."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import ClassVar


class GovernedLearningCandidateValidationError(ValueError):
    """Raised when a learning candidate violates its structural contract."""


class GovernedLearningCandidateStatus(str, Enum):
    """The only lifecycle state permitted by v0.1."""

    CANDIDATE_PROPOSED = "CANDIDATE_PROPOSED"


@dataclass(frozen=True)
class GovernedLearningCandidate:
    """Immutable evidence-bearing proposal with no model mutation authority."""

    candidate_id: str
    outcome_reconciliation_digest: str
    reality_gap_assessment_ref: str
    scope: str
    hypothesis: str
    proposed_change: str
    evidence_refs: tuple[str, ...]
    status: GovernedLearningCandidateStatus = field(
        default=GovernedLearningCandidateStatus.CANDIDATE_PROPOSED,
        init=False,
    )
    authority_granted: bool = field(default=False, init=False)

    VALID_STATUSES: ClassVar[frozenset[GovernedLearningCandidateStatus]] = frozenset(
        {GovernedLearningCandidateStatus.CANDIDATE_PROPOSED}
    )

    def __post_init__(self) -> None:
        for name in (
            "candidate_id",
            "outcome_reconciliation_digest",
            "reality_gap_assessment_ref",
            "scope",
            "hypothesis",
            "proposed_change",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise GovernedLearningCandidateValidationError(
                    f"{name} must be a non-empty string."
                )
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise GovernedLearningCandidateValidationError(
                "evidence_refs must be a non-empty tuple."
            )
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise GovernedLearningCandidateValidationError(
                "evidence_refs must contain only non-empty strings."
            )
        if self.status is not GovernedLearningCandidateStatus.CANDIDATE_PROPOSED:
            raise GovernedLearningCandidateValidationError(
                "v0.1 permits only CANDIDATE_PROPOSED."
            )

    @property
    def candidate_digest(self) -> str:
        """Return the deterministic SHA-256 identity of the candidate evidence."""
        payload = {
            "candidate_id": self.candidate_id,
            "evidence_refs": list(self.evidence_refs),
            "hypothesis": self.hypothesis,
            "outcome_reconciliation_digest": self.outcome_reconciliation_digest,
            "proposed_change": self.proposed_change,
            "reality_gap_assessment_ref": self.reality_gap_assessment_ref,
            "scope": self.scope,
            "status": self.status.value,
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        """Return the complete stable public projection."""
        return {
            "candidate_id": self.candidate_id,
            "outcome_reconciliation_digest": self.outcome_reconciliation_digest,
            "reality_gap_assessment_ref": self.reality_gap_assessment_ref,
            "scope": self.scope,
            "hypothesis": self.hypothesis,
            "proposed_change": self.proposed_change,
            "evidence_refs": list(self.evidence_refs),
            "status": self.status.value,
            "candidate_digest": self.candidate_digest,
            "authority_granted": self.authority_granted,
        }

    @classmethod
    def propose(
        cls,
        *,
        candidate_id: str,
        outcome_reconciliation_digest: str,
        reality_gap_assessment_ref: str,
        scope: str,
        hypothesis: str,
        proposed_change: str,
        evidence_refs: tuple[str, ...],
    ) -> "GovernedLearningCandidate":
        """Construct a candidate without side effects or active-model mutation."""
        return cls(
            candidate_id=candidate_id,
            outcome_reconciliation_digest=outcome_reconciliation_digest,
            reality_gap_assessment_ref=reality_gap_assessment_ref,
            scope=scope,
            hypothesis=hypothesis,
            proposed_change=proposed_change,
            evidence_refs=evidence_refs,
        )

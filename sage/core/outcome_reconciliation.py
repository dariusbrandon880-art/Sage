"""Outcome reconciliation v0.1 — bounded T0-to-T1 lineage composition.

This primitive relates a governed T0 claim to T1 observation and assessment
references without asserting that any observation is true or authoritative.
It is immutable, storage-free, signing-free, and execution-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import ClassVar


class OutcomeReconciliationValidationError(ValueError):
    """Raised when an outcome reconciliation violates its structural contract."""


class OutcomeReconciliationStatus(str, Enum):
    """Explicit semantic states for post-decision reconciliation evidence."""

    OBSERVED = "OBSERVED"
    REPORTED = "REPORTED"
    RECONCILED = "RECONCILED"
    UNRESOLVED = "UNRESOLVED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class OutcomeReconciliation:
    """Immutable, deterministic projection of T0/T1 reconciliation lineage.

    A reconciliation status describes the relationship represented by the
    supplied records. It is not a truth assertion, authorization, capability
    qualification, or proof of physical-world completion.
    """

    decision_id: str
    context_id: str
    t0_claim_ref: str
    t1_observation_ref: str
    reality_gap_assessment_ref: str
    outcome_ref: str
    status: OutcomeReconciliationStatus
    rationale: str
    authority_granted: bool = field(default=False, init=False)

    VALID_STATUSES: ClassVar[frozenset[OutcomeReconciliationStatus]] = frozenset(
        OutcomeReconciliationStatus
    )

    def __post_init__(self) -> None:
        for name in (
            "decision_id",
            "context_id",
            "t0_claim_ref",
            "t1_observation_ref",
            "reality_gap_assessment_ref",
            "outcome_ref",
            "rationale",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise OutcomeReconciliationValidationError(
                    f"{name} must be a non-empty string."
                )

        if not isinstance(self.status, OutcomeReconciliationStatus):
            raise OutcomeReconciliationValidationError(
                "status must be an OutcomeReconciliationStatus."
            )

    @property
    def reconciliation_digest(self) -> str:
        """Return the deterministic SHA-256 identity of the lineage envelope."""
        payload = {
            "context_id": self.context_id,
            "decision_id": self.decision_id,
            "outcome_ref": self.outcome_ref,
            "rationale": self.rationale,
            "reality_gap_assessment_ref": self.reality_gap_assessment_ref,
            "status": self.status.value,
            "t0_claim_ref": self.t0_claim_ref,
            "t1_observation_ref": self.t1_observation_ref,
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, str | bool]:
        """Return the complete stable public projection."""
        return {
            "decision_id": self.decision_id,
            "context_id": self.context_id,
            "t0_claim_ref": self.t0_claim_ref,
            "t1_observation_ref": self.t1_observation_ref,
            "reality_gap_assessment_ref": self.reality_gap_assessment_ref,
            "outcome_ref": self.outcome_ref,
            "status": self.status.value,
            "rationale": self.rationale,
            "reconciliation_digest": self.reconciliation_digest,
            "authority_granted": self.authority_granted,
        }

    @classmethod
    def reconcile(
        cls,
        *,
        decision_id: str,
        context_id: str,
        t0_claim_ref: str,
        t1_observation_ref: str,
        reality_gap_assessment_ref: str,
        outcome_ref: str,
        status: OutcomeReconciliationStatus,
        rationale: str,
    ) -> "OutcomeReconciliation":
        """Construct a validated reconciliation without performing side effects."""
        return cls(
            decision_id=decision_id,
            context_id=context_id,
            t0_claim_ref=t0_claim_ref,
            t1_observation_ref=t1_observation_ref,
            reality_gap_assessment_ref=reality_gap_assessment_ref,
            outcome_ref=outcome_ref,
            status=status,
            rationale=rationale,
        )

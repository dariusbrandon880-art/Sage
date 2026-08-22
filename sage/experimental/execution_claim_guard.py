"""Fail-closed guard for execution/verification status claims."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClaimState(str, Enum):
    PLANNED = "PLANNED"
    EXECUTED = "EXECUTED"
    VERIFIED = "VERIFIED"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True)
class ClaimEvidence:
    artifact_present: bool = False
    test_evidence_present: bool = False
    observation_present: bool = False
    independent_verification_present: bool = False
    receipt_present: bool = False

    @property
    def execution_ready(self) -> bool:
        return self.artifact_present and self.test_evidence_present

    @property
    def verification_ready(self) -> bool:
        return self.execution_ready and self.observation_present and self.independent_verification_present

    @property
    def completion_ready(self) -> bool:
        return self.verification_ready and self.receipt_present


def allowed_claim_state(evidence: ClaimEvidence) -> ClaimState:
    """Return the highest defensible state; never infer proof from narrative."""
    if evidence.completion_ready:
        return ClaimState.COMPLETE
    if evidence.verification_ready:
        return ClaimState.VERIFIED
    if evidence.execution_ready:
        return ClaimState.EXECUTED
    return ClaimState.PLANNED


def assert_claim_state(evidence: ClaimEvidence, requested: ClaimState) -> None:
    """Reject a status claim that outruns its observable evidence."""
    allowed = allowed_claim_state(evidence)
    order = list(ClaimState)
    if order.index(requested) > order.index(allowed):
        raise ValueError(f"claim {requested.value} exceeds evidence-supported state {allowed.value}")

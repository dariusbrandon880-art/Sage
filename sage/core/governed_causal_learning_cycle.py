"""Governed causal learning cycle v0.1.

Composes T0/T1 reconciliation, independently observed transition effects,
and a non-authoritative learning candidate into one deterministic review
projection. This boundary evaluates readiness for human review only; it never
promotes, mutates capability state, grants authority, persists state, or
executes a proposed change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import ClassVar

from sage.core.effect_observation import EffectObservation, TransitionOutcome
from sage.core.governed_learning_candidate import GovernedLearningCandidate
from sage.core.outcome_reconciliation import (
    OutcomeReconciliation,
    OutcomeReconciliationStatus,
)


class GovernedCausalLearningCycleValidationError(ValueError):
    """Raised when a causal learning cycle violates its composition contract."""


class GovernedCausalLearningCycleVerdict(str, Enum):
    """Non-authoritative posture for the composed evidence boundary."""

    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    HOLD = "HOLD"


@dataclass(frozen=True)
class GovernedCausalLearningCycle:
    """Immutable review projection across reconciliation, effect, and candidate."""

    reconciliation_digest: str
    observation_id: str
    candidate_digest: str
    verdict: GovernedCausalLearningCycleVerdict
    authority_granted: bool = field(default=False, init=False)
    reviewer_authorization_required: bool = field(default=True, init=False)

    VALID_VERDICTS: ClassVar[
        frozenset[GovernedCausalLearningCycleVerdict]
    ] = frozenset(GovernedCausalLearningCycleVerdict)

    @classmethod
    def compose(
        cls,
        *,
        reconciliation: OutcomeReconciliation,
        observation: EffectObservation,
        candidate: GovernedLearningCandidate,
    ) -> "GovernedCausalLearningCycle":
        """Compose existing evidence without creating authority or side effects."""
        if candidate.outcome_reconciliation_digest != reconciliation.reconciliation_digest:
            raise GovernedCausalLearningCycleValidationError(
                "candidate reconciliation lineage does not match supplied reconciliation."
            )
        if observation.execution_id != reconciliation.outcome_ref:
            raise GovernedCausalLearningCycleValidationError(
                "observation execution lineage does not match reconciliation outcome."
            )
        if observation.observation_id not in candidate.evidence_refs:
            raise GovernedCausalLearningCycleValidationError(
                "candidate evidence must include the supplied observation identity."
            )

        ready = (
            reconciliation.status is OutcomeReconciliationStatus.RECONCILED
            and observation.outcome is TransitionOutcome.CONFIRMED
        )
        verdict = (
            GovernedCausalLearningCycleVerdict.READY_FOR_REVIEW
            if ready
            else GovernedCausalLearningCycleVerdict.HOLD
        )
        return cls(
            reconciliation_digest=reconciliation.reconciliation_digest,
            observation_id=observation.observation_id,
            candidate_digest=candidate.candidate_digest,
            verdict=verdict,
        )

    @property
    def cycle_digest(self) -> str:
        """Return the deterministic SHA-256 identity of the review projection."""
        payload = {
            "candidate_digest": self.candidate_digest,
            "observation_id": self.observation_id,
            "reconciliation_digest": self.reconciliation_digest,
            "verdict": self.verdict.value,
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, str | bool]:
        """Return the complete stable public projection."""
        return {
            "reconciliation_digest": self.reconciliation_digest,
            "observation_id": self.observation_id,
            "candidate_digest": self.candidate_digest,
            "verdict": self.verdict.value,
            "cycle_digest": self.cycle_digest,
            "authority_granted": self.authority_granted,
            "reviewer_authorization_required": self.reviewer_authorization_required,
        }

"""Governed Outcome Quality Contract v0.1.

Derives a semantically valid, normalized outcome quality signal (0.0 <= actual_quality <= 1.0)
from authoritative OutcomeReconciliation lineage evidence and explicit quality metrics without
guessing or conflating lineage reconciliation status with decision quality.

Fails closed on UNRESOLVED, INDETERMINATE, or unverified evidence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional

from sage.core.outcome_reconciliation import (
    OutcomeReconciliation,
    OutcomeReconciliationStatus,
)


class OutcomeQualityValidationError(ValueError):
    """Raised when outcome quality evaluation fails closed due to invalid or unverified evidence."""


@dataclass(frozen=True)
class OutcomeQualityContract:
    """Immutable, deterministic projection of an evaluated outcome quality signal."""

    reconciliation_digest: str
    decision_id: str
    actual_quality: float
    quality_basis: str
    rationale: str
    reconciliation_status: str

    def __post_init__(self) -> None:
        if not isinstance(self.reconciliation_digest, str) or not self.reconciliation_digest.strip():
            raise OutcomeQualityValidationError("reconciliation_digest must be a non-empty string.")
        if not isinstance(self.decision_id, str) or not self.decision_id.strip():
            raise OutcomeQualityValidationError("decision_id must be a non-empty string.")
        if not isinstance(self.actual_quality, (int, float)) or isinstance(self.actual_quality, bool):
            raise OutcomeQualityValidationError("actual_quality must be a float between 0.0 and 1.0.")
        if not 0.0 <= float(self.actual_quality) <= 1.0:
            raise OutcomeQualityValidationError("actual_quality must be between 0.0 and 1.0.")
        if not isinstance(self.quality_basis, str) or not self.quality_basis.strip():
            raise OutcomeQualityValidationError("quality_basis must be a non-empty string.")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise OutcomeQualityValidationError("rationale must be a non-empty string.")

    @property
    def quality_digest(self) -> str:
        """Return the deterministic SHA-256 hash of the quality evaluation."""
        payload = {
            "actual_quality": round(self.actual_quality, 4),
            "decision_id": self.decision_id,
            "quality_basis": self.quality_basis,
            "rationale": self.rationale,
            "reconciliation_digest": self.reconciliation_digest,
            "reconciliation_status": self.reconciliation_status,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return dict representation of the contract."""
        return {
            "reconciliation_digest": self.reconciliation_digest,
            "decision_id": self.decision_id,
            "actual_quality": round(self.actual_quality, 4),
            "quality_basis": self.quality_basis,
            "rationale": self.rationale,
            "reconciliation_status": self.reconciliation_status,
            "quality_digest": self.quality_digest,
        }


def evaluate_outcome_quality(
    reconciliation: OutcomeReconciliation,
    *,
    actual_utility: Optional[float] = None,
    expected_utility: Optional[float] = None,
    confirmed_outcome: Optional[bool] = None,
) -> OutcomeQualityContract:
    """Evaluate an OutcomeReconciliation instance into a normalized OutcomeQualityContract.

    Fails closed if reconciliation status is UNRESOLVED or INDETERMINATE, or if explicit quality evidence is absent.
    Lineage status alone (RECONCILED, OBSERVED, REPORTED) does not imply outcome quality.
    """
    if not isinstance(reconciliation, OutcomeReconciliation):
        raise OutcomeQualityValidationError("reconciliation must be an instance of OutcomeReconciliation.")

    status = reconciliation.status
    if status in (OutcomeReconciliationStatus.UNRESOLVED, OutcomeReconciliationStatus.INDETERMINATE):
        raise OutcomeQualityValidationError(
            f"Cannot derive outcome quality from status '{status.value}': evidence is unresolved or indeterminate."
        )

    # 1. Confirmed explicit outcome indicator (e.g. True = success, False = failure)
    if confirmed_outcome is not None:
        if not isinstance(confirmed_outcome, bool):
            raise OutcomeQualityValidationError("confirmed_outcome must be a boolean.")
        actual_quality = 1.0 if confirmed_outcome else 0.0
        basis = "CONFIRMED_OUTCOME_INDICATOR"
        rationale = f"Outcome quality evaluated from explicit confirmed outcome boolean: {confirmed_outcome}"

    # 2. Utility realization ratio
    elif actual_utility is not None or expected_utility is not None:
        if actual_utility is None or expected_utility is None:
            raise OutcomeQualityValidationError(
                "Both actual_utility and expected_utility must be supplied together for utility evaluation."
            )
        if isinstance(actual_utility, bool) or isinstance(expected_utility, bool):
            raise OutcomeQualityValidationError("Utility values cannot be booleans.")
        if not isinstance(actual_utility, (int, float)) or not isinstance(expected_utility, (int, float)):
            raise OutcomeQualityValidationError("Utility values must be floats.")
        if expected_utility < 0.0 or actual_utility < 0.0:
            raise OutcomeQualityValidationError("Utility values cannot be negative.")

        if expected_utility == 0.0:
            actual_quality = 1.0 if actual_utility >= 0.0 else 0.0
        else:
            actual_quality = round(min(1.0, max(0.0, float(actual_utility) / float(expected_utility))), 4)

        basis = "REALIZED_UTILITY_RATIO"
        rationale = f"Evaluated realized utility ratio: {actual_utility} / {expected_utility} = {actual_quality}"

    else:
        # Strict Fail-Closed Rule: Lineage reconciliation status alone does not constitute outcome quality.
        raise OutcomeQualityValidationError(
            "Cannot evaluate outcome quality: lineage reconciliation status alone does not imply outcome quality. "
            "Explicit utility metrics (actual_utility, expected_utility) or confirmed_outcome boolean required."
        )

    return OutcomeQualityContract(
        reconciliation_digest=reconciliation.reconciliation_digest,
        decision_id=reconciliation.decision_id,
        actual_quality=actual_quality,
        quality_basis=basis,
        rationale=rationale,
        reconciliation_status=status.value,
    )


def apply_outcome_to_metacognitive_state(
    quality_contract: OutcomeQualityContract,
    prior_state: Any,
) -> Any:
    """Apply an OutcomeQualityContract to a MetacognitiveState instance.

    Uses duck-typing to adhere to the One-Way Import Law (core production module
    must not import from sage.experimental.*).
    """
    if not isinstance(quality_contract, OutcomeQualityContract):
        raise OutcomeQualityValidationError("quality_contract must be an OutcomeQualityContract instance.")

    if not hasattr(prior_state, "with_outcome") or not callable(prior_state.with_outcome):
        raise OutcomeQualityValidationError("prior_state must have a callable with_outcome() method.")

    return prior_state.with_outcome(quality_contract.actual_quality)


__all__ = [
    "OutcomeQualityContract",
    "OutcomeQualityValidationError",
    "apply_outcome_to_metacognitive_state",
    "evaluate_outcome_quality",
]
